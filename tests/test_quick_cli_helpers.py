from movie_box.friendly_cli import (
    choose_default_dub,
    display_subject_type,
    format_episode_range,
    language_hint_from_title,
)
from movie_box.v3.constants import SubjectType


def dub(name: str, code: str):
    from types import SimpleNamespace

    return SimpleNamespace(lan_name=name, lan_code=code)


def test_default_dub_prefers_english_then_original():
    dubs = [dub("Hindi", "hi"), dub("English", "en"), dub("Original", "og")]

    assert choose_default_dub(dubs, "English") == "English"
    assert choose_default_dub(dubs, "Japanese") == "English"


def test_title_language_hint_prefers_bracketed_audio():
    assert language_hint_from_title("Titans [Hindi]") == "Hindi"
    assert language_hint_from_title("Little") is None


def test_display_labels_are_user_facing():
    assert display_subject_type(SubjectType.MOVIES) == "Movie"
    assert display_subject_type(SubjectType.TV_SERIES) == "Series"


def test_episode_range_summary():
    assert format_episode_range(1, 4, 1) == "S1E4"
    assert format_episode_range(1, 4, 2) == "S1E4-E5"
