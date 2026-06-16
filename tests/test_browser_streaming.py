from pathlib import Path

from movie_box import friendly_cli
from movie_box.streaming import (
    SUBTITLE_PATH_PREFIX,
    VIDEO_PATH,
    build_player_html,
    to_webvtt,
)
from movie_box.v1.cli.helpers import media_player_name_func_map


def test_browser_registered_in_player_map():
    assert "browser" in media_player_name_func_map
    assert callable(media_player_name_func_map["browser"])


def test_build_player_html_points_at_proxy_video():
    html = build_player_html([]).decode("utf-8")
    assert f'src="{VIDEO_PATH}"' in html
    assert "<track" not in html


def test_build_player_html_renders_subtitle_tracks():
    html = build_player_html(
        [(f"{SUBTITLE_PATH_PREFIX}0", "en"), (f"{SUBTITLE_PATH_PREFIX}1", "hi")]
    ).decode("utf-8")
    assert f'src="{SUBTITLE_PATH_PREFIX}0"' in html
    assert 'srclang="en"' in html
    assert "default" in html  # first track is the default one


def test_to_webvtt_converts_srt_timestamps(tmp_path: Path):
    srt = tmp_path / "sub.srt"
    srt.write_text(
        "1\n00:00:01,000 --> 00:00:04,000\nHello there\n",
        encoding="utf-8",
    )
    out = to_webvtt(srt).decode("utf-8")
    assert out.startswith("WEBVTT")
    assert "00:00:01.000 --> 00:00:04.000" in out


def test_to_webvtt_passes_through_existing_vtt(tmp_path: Path):
    vtt = tmp_path / "sub.vtt"
    vtt.write_text(
        "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHi\n", encoding="utf-8"
    )
    assert to_webvtt(vtt).decode("utf-8").startswith("WEBVTT")


def test_choose_action_maps_prompt_to_intent(monkeypatch):
    monkeypatch.setattr(friendly_cli.click, "prompt", lambda *a, **k: 2)
    assert friendly_cli.choose_action() == "stream"

    monkeypatch.setattr(friendly_cli.click, "prompt", lambda *a, **k: 1)
    assert friendly_cli.choose_action() == "download"
