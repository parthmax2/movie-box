"""In-browser streaming for users without a desktop media player.

mpv/vlc are great but not everyone has them installed. The CDN that serves the
video requires specific HTTP headers (``User-Agent`` and ``Referer``), so a
plain ``webbrowser.open(url)`` would be rejected with a 403.

To work for *anyone with a browser*, this module runs a tiny localhost HTTP
proxy that:

- streams the upstream video through while injecting the required headers,
- forwards ``Range`` requests so seeking works,
- serves a minimal HTML5 ``<video>`` page (plus any subtitle tracks).

The browser only ever talks to ``http://127.0.0.1:<port>`` so no special
headers are needed on its side.
"""

from __future__ import annotations

import logging
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
from throttlebuster import DownloadedFile

from movie_box.v1.constants import DOWNLOAD_REQUEST_HEADERS

__all__ = ["stream_video_via_browser", "build_player_html", "to_webvtt"]

PLAYER_PAGE_PATH = "/"
VIDEO_PATH = "/video"
SUBTITLE_PATH_PREFIX = "/subtitle/"

_STREAM_CHUNK_SIZE = 256 * 1024  # 256 KiB
_PROXIED_RESPONSE_HEADERS = ("Content-Range", "Accept-Ranges")
_SRT_TIMESTAMP_RE = re.compile(r"(\d{2}:\d{2}:\d{2}),(\d{3})")

_PLAYER_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>movie-box stream</title>
  <style>
    html, body { margin: 0; height: 100%; background: #000; }
    video { width: 100vw; height: 100vh; background: #000; }
  </style>
</head>
<body>
  <video controls autoplay src="__VIDEO__">
__TRACKS__
  </video>
</body>
</html>
"""


def to_webvtt(path: Path) -> bytes:
    """Read a subtitle file and return it as WebVTT bytes.

    The HTML ``<track>`` element only accepts WebVTT, so SubRip (``.srt``)
    files are converted on the fly (header + comma->dot in timestamps).
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if Path(path).suffix.lower() == ".vtt" or text.lstrip().startswith("WEBVTT"):
        return text.encode("utf-8")
    converted = _SRT_TIMESTAMP_RE.sub(r"\1.\2", text)
    return ("WEBVTT\n\n" + converted).encode("utf-8")


def build_player_html(subtitle_tracks: list[tuple[str, str]]) -> bytes:
    """Render the HTML5 player page.

    Args:
        subtitle_tracks: ``(src, language_label)`` pairs for each subtitle.
    """
    tracks = "\n".join(
        f'    <track kind="subtitles" src="{src}" srclang="{label}" '
        f'label="{label}"{" default" if index == 0 else ""}>'
        for index, (src, label) in enumerate(subtitle_tracks)
    )
    return (
        _PLAYER_PAGE_TEMPLATE.replace("__VIDEO__", VIDEO_PATH).replace(
            "__TRACKS__", tracks
        )
    ).encode("utf-8")


class _StreamProxyHandler(BaseHTTPRequestHandler):
    """Serves the player page and proxies the video/subtitles.

    Concrete subclasses are created per-stream with the request-specific
    attributes bound as class members.
    """

    # Bound per stream by ``stream_video_via_browser``.
    video_url: str
    client: httpx.Client
    html_page: bytes
    subtitle_paths: dict[str, Path]

    def log_message(self, fmt: str, *args) -> None:
        logging.debug("stream-proxy: " + fmt, *args)

    def do_GET(self) -> None:  # http.server dispatch name
        if self.path == PLAYER_PAGE_PATH:
            self._serve_bytes(self.html_page, "text/html; charset=utf-8")
        elif self.path == VIDEO_PATH:
            self._proxy_video()
        elif self.path.startswith(SUBTITLE_PATH_PREFIX):
            self._serve_subtitle()
        else:
            self.send_error(404)

    def _serve_bytes(self, payload: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_subtitle(self) -> None:
        key = self.path[len(SUBTITLE_PATH_PREFIX) :]
        path = self.subtitle_paths.get(key)
        if path is None or not path.exists():
            self.send_error(404)
            return
        self._serve_bytes(to_webvtt(path), "text/vtt; charset=utf-8")

    def _proxy_video(self) -> None:
        upstream_headers = dict(DOWNLOAD_REQUEST_HEADERS)
        range_header = self.headers.get("Range")
        if range_header:
            upstream_headers["Range"] = range_header

        try:
            with self.client.stream(
                "GET", self.video_url, headers=upstream_headers
            ) as upstream:
                self.send_response(upstream.status_code)
                self.send_header(
                    "Content-Type",
                    upstream.headers.get("Content-Type", "video/mp4"),
                )
                content_length = upstream.headers.get("Content-Length")
                if content_length:
                    self.send_header("Content-Length", content_length)
                for name in _PROXIED_RESPONSE_HEADERS:
                    value = upstream.headers.get(name)
                    if value:
                        self.send_header(name, value)
                if not upstream.headers.get("Accept-Ranges"):
                    self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                for chunk in upstream.iter_bytes(_STREAM_CHUNK_SIZE):
                    self.wfile.write(chunk)
        except ConnectionError:
            # Browser seeked or closed the tab mid-stream; expected.
            return
        except httpx.HTTPError as exc:
            logging.debug(f"stream-proxy upstream error: {exc}")
            try:
                self.send_error(502, "Upstream stream failed")
            except (ConnectionError, OSError):
                pass


def _bound_handler(
    *,
    video_url: str,
    client: httpx.Client,
    html_page: bytes,
    subtitle_paths: dict[str, Path],
) -> type[_StreamProxyHandler]:
    return type(
        "_BoundStreamProxyHandler",
        (_StreamProxyHandler,),
        {
            "video_url": video_url,
            "client": client,
            "html_page": html_page,
            "subtitle_paths": subtitle_paths,
        },
    )


def stream_video_via_browser(
    url: str,
    subtitle_details_items: list[DownloadedFile],
    subtitles_dir: str,
) -> tuple[None, None]:
    """Play ``url`` in the default web browser via a localhost proxy.

    Matches the ``media_player_name_func_map`` signature used for mpv/vlc so it
    can be selected with ``stream_via="browser"``. Blocks until the user
    presses Enter (mirroring how the mpv/vlc helpers block on the player).
    """
    subtitle_paths: dict[str, Path] = {}
    subtitle_tracks: list[tuple[str, str]] = []
    for index, sub_file in enumerate(subtitle_details_items or []):
        saved_to = Path(sub_file.saved_to)
        key = str(index)
        subtitle_paths[key] = saved_to
        label = saved_to.stem.split(".")[-1] or "sub"
        subtitle_tracks.append((SUBTITLE_PATH_PREFIX + key, label))

    client = httpx.Client(
        follow_redirects=True,
        timeout=httpx.Timeout(30.0, read=None),
    )
    handler = _bound_handler(
        video_url=str(url),
        client=client,
        html_page=build_player_html(subtitle_tracks),
        subtitle_paths=subtitle_paths,
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    host, port = server.server_address
    page_url = f"http://{host}:{port}/"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    logging.info(f"Streaming in your browser at {page_url}")
    print(f"\n  ▶ Streaming in your browser: {page_url}")
    print("  If it does not open automatically, paste the link above.")
    try:
        webbrowser.open(page_url)
    except Exception:  # browser launch is best-effort
        pass

    try:
        input(
            "\n  Press Enter here to stop streaming and return to movie-box... "
        )
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        server.shutdown()
        server.server_close()
        client.close()

    return (None, None)
