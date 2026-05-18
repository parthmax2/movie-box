import pytest
from click.testing import CliRunner

from movie_box.console import _cli_entry
from movie_box.v3.constants import CustomResolutionType, SubjectType
from movie_box.v3.models.downloadables import (
    RootCaptionFileMetadata,
    RootDownloadableFilesDetailModel,
    VideoFileMetadata,
)
from movie_box.v3.models.details import DubModel
from movie_box.v3.models.search import ResultsSubjectModel


class AsyncContextSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None


class CapturingDownloader:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def download_movie(self, *args, **kwargs):
        self.calls.append(("movie", args, kwargs))
        return None, []

    async def download_tv_series(self, *args, **kwargs):
        self.calls.append(("series", args, kwargs))
        return {}


def run_cli(args):
    result = CliRunner().invoke(_cli_entry, args)
    assert result.exit_code == 0, result.output
    return result


@pytest.mark.parametrize(
    ("version", "module_path", "expected_quality"),
    [
        ("v1", "movie_box.v1.cli.interface", "1080P"),
        ("v2", "movie_box.v2.cli.interface", "1080P"),
        ("v3", "movie_box.v3.cli.interface", CustomResolutionType._1080P),
    ],
)
def test_readme_versioned_movie_options_reach_downloader(
    monkeypatch, version, module_path, expected_quality
):
    module = pytest.importorskip(module_path)
    CapturingDownloader.calls = []
    monkeypatch.setattr(module, "Downloader", CapturingDownloader)
    if version == "v3":
        monkeypatch.setattr(module, "MovieBoxHttpClient", AsyncContextSession)

    run_cli([
        version,
        "download-movie",
        "Avatar",
        "--quality",
        "1080p",
        "--language",
        "French",
        "--stream-via",
        "mpv",
        "--no-caption",
        "--yes",
        "--test",
        "--quiet",
    ])

    kind, args, kwargs = CapturingDownloader.calls[-1]
    assert kind == "movie"
    assert args[0] == "Avatar"
    assert kwargs["quality"] == expected_quality
    assert kwargs["language"] == ("French",)
    assert kwargs["stream_via"] == "mpv"
    assert kwargs["download_caption"] is False
    assert kwargs["yes"] is True
    assert kwargs["test"] is True


@pytest.mark.parametrize(
    ("version", "module_path", "expected_quality"),
    [
        ("v1", "movie_box.v1.cli.interface", "720P"),
        ("v2", "movie_box.v2.cli.interface", "720P"),
        ("v3", "movie_box.v3.cli.interface", CustomResolutionType._720P),
    ],
)
def test_readme_versioned_series_options_reach_downloader(
    monkeypatch, version, module_path, expected_quality
):
    module = pytest.importorskip(module_path)
    CapturingDownloader.calls = []
    monkeypatch.setattr(module, "Downloader", CapturingDownloader)
    if version == "v3":
        monkeypatch.setattr(module, "MovieBoxHttpClient", AsyncContextSession)

    run_cli([
        version,
        "download-series",
        "Merlin",
        "--season",
        "1",
        "--episode",
        "2",
        "--limit",
        "3",
        "--quality",
        "720p",
        "--language",
        "Spanish",
        "--stream-via",
        "vlc",
        "--yes",
        "--test",
        "--quiet",
    ])

    kind, args, kwargs = CapturingDownloader.calls[-1]
    assert kind == "series"
    assert args[0] == "Merlin"
    assert kwargs["season"] == 1
    assert kwargs["episode"] == 2
    assert kwargs["limit"] == 3
    assert kwargs["quality"] == expected_quality
    assert kwargs["language"] == ("Spanish",)
    assert kwargs["stream_via"] == "vlc"
    assert kwargs["yes"] is True
    assert kwargs["test"] is True


def test_readme_friendly_movie_options_reach_downloader(monkeypatch, tmp_path):
    import movie_box.friendly_cli as friendly_cli

    CapturingDownloader.calls = []
    monkeypatch.setenv("MOVIEBOX_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(friendly_cli, "Downloader", CapturingDownloader)
    monkeypatch.setattr(friendly_cli, "MovieBoxHttpClient", AsyncContextSession)
    monkeypatch.setattr(friendly_cli, "print_compact_header", lambda: None)

    run_cli([
        "movie",
        "Avatar",
        "--quality",
        "480P",
        "--language",
        "Hindi",
        "--stream-via",
        "mpv",
        "--no-caption",
        "--yes",
    ])

    kind, args, kwargs = CapturingDownloader.calls[-1]
    assert kind == "movie"
    assert args[0] == "Avatar"
    assert kwargs["quality"] == CustomResolutionType._480P
    assert kwargs["language"] == ("Hindi",)
    assert kwargs["stream_via"] == "mpv"
    assert kwargs["download_caption"] is False
    assert kwargs["yes"] is True


def test_v3_caption_language_lookup_is_case_insensitive_for_names():
    captions = RootCaptionFileMetadata.model_validate({
        "subjectId": "123456789012345678",
        "extCaptions": [
            {
                "id": "caption-1",
                "lan": "fil",
                "lanName": "Filipino",
                "url": "https://example.com/subtitle.vtt",
                "size": 10,
                "delay": 0,
            }
        ],
    })

    assert captions.get_subtitle_by_language("fil") is not None
    assert captions.get_subtitle_by_language("Filipino") is not None
    assert captions.get_subtitle_by_language("filipino") is not None


@pytest.mark.asyncio
async def test_v3_movie_stream_without_captions_uses_empty_subtitle_list(
    monkeypatch,
):
    import movie_box.v3.cli.downloader as downloader_module

    target_movie = ResultsSubjectModel.model_construct(
        subject_id="123456789012345678",
        subject_type=SubjectType.MOVIES,
        title="Avatar",
        release_date="2009-12-18",
    )
    target_media = VideoFileMetadata.model_construct(
        resource_link="https://example.com/avatar.mp4",
        url="https://example.com/avatar.mp4",
        resolution=1080,
    )
    downloadable_details = RootDownloadableFilesDetailModel.model_construct(
        list=[target_media],
        subject_id="123456789012345678",
        subject_type=SubjectType.MOVIES,
        subject_title="Avatar",
    )
    item_details = ResultsSubjectModel.model_construct(
        subject_id="123456789012345678",
        dubs=[
            DubModel.model_construct(
                subject_id="123456789012345678",
                lan_name="Original",
                lan_code="en",
            )
        ],
    )
    stream_calls = []

    class FakeItemDetails:
        def __init__(self, *args, **kwargs):
            pass

        async def get_content_model(self, subject_id):
            return item_details

    class FakeDownloadableFilesDetail:
        def __init__(self, *args, **kwargs):
            pass

        async def get_content_model(self, *args, **kwargs):
            return downloadable_details

    async def fake_search(*args, **kwargs):
        return target_movie

    def fake_player(url, subtitles, subtitles_dir):
        stream_calls.append((url, subtitles, subtitles_dir))
        return "streamed"

    monkeypatch.setattr(downloader_module, "ItemDetails", FakeItemDetails)
    monkeypatch.setattr(
        downloader_module, "DownloadableFilesDetail", FakeDownloadableFilesDetail
    )
    monkeypatch.setattr(
        downloader_module,
        "resolve_media_file_to_be_downloaded",
        lambda quality, details: target_media,
    )
    monkeypatch.setitem(
        downloader_module.media_player_name_func_map, "mpv", fake_player
    )

    downloader = object.__new__(downloader_module.Downloader)
    object.__setattr__(downloader, "client_session", object())

    result = await downloader.download_movie(
        "Avatar",
        search_function=fake_search,
        stream_via="mpv",
        download_caption=False,
        caption_only=False,
        test=False,
    )

    assert result == "streamed"
    assert stream_calls[0][0] == "https://example.com/avatar.mp4"
    assert stream_calls[0][1] == []
