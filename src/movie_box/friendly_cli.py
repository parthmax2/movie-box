import json
import os
import re
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from movie_box.v3.cli.downloader import Downloader
from movie_box.v3.constants import (
    CURRENT_WORKING_DIR,
    DEFAULT_CAPTION_LANGUAGE,
    DEFAULT_DUB_LANGUAGE_NAME_OR_CODE,
    CustomResolutionType,
    SubjectType,
)
from movie_box.v3.core import (
    DownloadableFilesDetail,
    ItemDetails,
    Search,
    SeasonDetails,
)
from movie_box.v3.http_client import MovieBoxHttpClient
from movie_box.v3.models.details import DubModel
from movie_box.v3.models.details import SeasonsModel
from movie_box.v3.models.downloadables import (
    RootCaptionFileMetadata,
    RootDownloadableFilesDetailModel,
)
from movie_box.v3.models.search import ResultsSubjectModel
from movie_box.tui.art import print_banner as print_tui_banner
from movie_box.tui.art import render_banner, render_compact_header
from movie_box.tui.command_engine import CommandEngine
from movie_box.tui.splash import run_boot_sequence
from movie_box.tui.textual_app import launch_textual_app
from movie_box.tui.theme import THEME

console = Console()

QUICK_DEFAULT_DUB = "English"
TITLE_LANGUAGE_PATTERN = re.compile(r"\[([^\]]+)\]")
SEARCH_STOP_WORDS = {"a", "an", "and", "the"}

CONFIG_KEYS = {
    "dir",
    "caption_dir",
    "quality",
    "language",
    "dub",
}

SUBJECT_TYPE_CHOICES = {
    "all": SubjectType.ALL,
    "movie": SubjectType.MOVIES,
    "movies": SubjectType.MOVIES,
    "series": SubjectType.TV_SERIES,
    "tv": SubjectType.TV_SERIES,
    "music": SubjectType.MUSIC,
    "anime": SubjectType.ANIME,
    "education": SubjectType.EDUCATION,
}


def print_banner() -> None:
    print_tui_banner(console)


def print_compact_header() -> None:
    console.print(render_compact_header())


def prompt_shell_input() -> str:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.styles import Style
    except ImportError:
        return click.prompt(click.style("movie-box", fg="magenta"), default="", show_default=False)

    commands = WordCompleter(
        [
            "/help",
            "/search",
            "/select",
            "/download",
            "/movie",
            "/series",
            "/config",
            "/doctor",
            "/clear",
            "/exit",
        ],
        ignore_case=True,
    )
    style = Style.from_dict(
        {
            "prompt": "bold #d946ef",
            "marker": "#38bdf8",
        }
    )
    session = PromptSession(completer=commands, style=style)
    return session.prompt([("class:prompt", "movie-box"), ("class:marker", " > ")])


def get_config_path() -> Path:
    config_path = os.getenv("MOVIEBOX_CONFIG_PATH")
    if config_path:
        return Path(config_path).expanduser()

    config_home = os.getenv("MOVIEBOX_CONFIG_HOME")
    if config_home:
        return Path(config_home).expanduser() / "config.json"

    base_dir = os.getenv("APPDATA")
    if base_dir:
        return Path(base_dir) / "movie-box" / "config.json"
    return Path.home() / ".config" / "movie-box" / "config.json"


def load_config() -> dict[str, Any]:
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_config(config: dict[str, Any]) -> None:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def subject_type_from_choice(value: str) -> SubjectType:
    return SUBJECT_TYPE_CHOICES[value.lower()]


def normalize_quality(value: str) -> CustomResolutionType:
    normalized = value.lower()
    for quality in CustomResolutionType:
        if quality.value.lower() == normalized:
            return quality
    choices = ", ".join(item.value for item in CustomResolutionType)
    raise click.ClickException(
        f"Invalid quality {value!r}. Choose one of: {choices}."
    )


def item_year(item: ResultsSubjectModel) -> str:
    return str(item.release_date.year) if item.release_date else "-"


def format_languages(item: ResultsSubjectModel) -> str:
    languages = item.language[:3] if item.language else []
    suffix = " +" if len(item.language) > 3 else ""
    return ", ".join(languages) + suffix if languages else "-"


def display_subject_type(subject_type: SubjectType) -> str:
    if subject_type is SubjectType.TV_SERIES:
        return "Series"
    if subject_type is SubjectType.MOVIES:
        return "Movie"
    return subject_type.name.replace("_", " ").title()


def normalize_search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def is_confident_title_match(query: str, item: ResultsSubjectModel) -> bool:
    normalized_query = normalize_search_text(query)
    normalized_title = normalize_search_text(item.title)
    if normalized_query == normalized_title:
        return True

    query_tokens = {
        token for token in normalized_query.split() if token not in SEARCH_STOP_WORDS
    }
    title_tokens = set(normalized_title.split())
    return bool(query_tokens) and query_tokens.issubset(title_tokens)


def language_hint_from_title(title: str) -> str | None:
    match = TITLE_LANGUAGE_PATTERN.search(title)
    if not match:
        return None
    hint = match.group(1).replace("dub", "").strip()
    return hint or None


def is_supported_quick_type(item: ResultsSubjectModel) -> bool:
    return item.subject_type in {SubjectType.MOVIES, SubjectType.TV_SERIES}


def quick_subject_label(subject_type: SubjectType) -> str:
    if subject_type is SubjectType.TV_SERIES:
        return "Series"
    if subject_type is SubjectType.MOVIES:
        return "Movie"
    return display_subject_type(subject_type)


def choose_quick_subject_type(
    query: str,
    items: list[ResultsSubjectModel],
) -> SubjectType:
    supported_items = [item for item in items if is_supported_quick_type(item)]
    if not supported_items:
        raise click.ClickException("No movie or series results found.")

    first_item = supported_items[0]
    if is_confident_title_match(query, first_item):
        return first_item.subject_type

    available_types = {item.subject_type for item in supported_items}
    if len(available_types) == 1:
        return first_item.subject_type

    type_choice = click.prompt(
        "Type",
        type=click.Choice(["auto", "movie", "series"], case_sensitive=False),
        default="auto",
        show_default=True,
    ).lower()
    if type_choice == "movie":
        return SubjectType.MOVIES
    if type_choice == "series":
        return SubjectType.TV_SERIES
    return first_item.subject_type


def choose_quick_result(
    items: list[ResultsSubjectModel],
) -> ResultsSubjectModel:
    supported_items = [item for item in items if is_supported_quick_type(item)]
    if not supported_items:
        raise click.ClickException("No movie or series results found.")

    if len(supported_items) == 1:
        return supported_items[0]

    render_results_table(supported_items)
    return choose_item(supported_items)


def default_audio_name(selected: ResultsSubjectModel, config: dict[str, Any]) -> str:
    return (
        language_hint_from_title(selected.title)
        or config.get("dub")
        or QUICK_DEFAULT_DUB
    )


def choose_quick_item(
    query: str,
    items: list[ResultsSubjectModel],
    subject_type: SubjectType,
) -> ResultsSubjectModel:
    matching_items = [
        item for item in items if item.subject_type is subject_type
    ]
    if not matching_items:
        label = quick_subject_label(subject_type)
        raise click.ClickException(f"No {label} results found.")

    if len(matching_items) == 1 or is_confident_title_match(
        query, matching_items[0]
    ):
        return matching_items[0]

    console.print(
        f"[yellow]Multiple {quick_subject_label(subject_type)} matches found.[/yellow]"
    )
    render_results_table(matching_items)
    return choose_item(matching_items)


def choose_default_dub(dubs: list[DubModel], current: str) -> str:
    preferred = current.casefold()
    for dub in dubs:
        if preferred in {dub.lan_name.casefold(), dub.lan_code.casefold()}:
            return dub.lan_name

    for fallback in ("English", "Original"):
        normalized_fallback = fallback.casefold()
        for dub in dubs:
            if normalized_fallback in {
                dub.lan_name.casefold(),
                dub.lan_code.casefold(),
            }:
                return dub.lan_name

    return dubs[0].lan_name


def choose_quick_dub(dubs: list[DubModel], current: str) -> DubModel | None:
    if not dubs:
        return None

    default_index = 1
    normalized_current = current.casefold()
    rows = []
    for index, dub in enumerate(dubs, start=1):
        if normalized_current in {
            dub.lan_name.casefold(),
            dub.lan_code.casefold(),
        }:
            default_index = index
        rows.append((dub.lan_name, f"code: {dub.lan_code}"))

    if len(dubs) == 1:
        console.print(f"[dim]Audio:[/dim] {dubs[0].lan_name}")
        return dubs[0]

    choice = choose_numbered_option(
        "Audio language",
        rows,
        default=default_index,
    )
    return dubs[choice - 1]


def choose_quick_quality(
    details: RootDownloadableFilesDetailModel,
    current: CustomResolutionType,
) -> CustomResolutionType:
    quality_items = sorted(
        {
            CustomResolutionType(f"{item.resolution.value}P")
            for item in details.collection_resolutions
            if item.resolution.value > 0
        },
        key=lambda item: CustomResolutionType.convert_to_default_resolution(
            item
        ).value,
        reverse=True,
    )

    if not quality_items and details.subject_type is not SubjectType.TV_SERIES:
        quality_items = sorted(
            details.get_quality_downloads_map(),
            key=lambda item: CustomResolutionType.convert_to_default_resolution(
                item
            ).value,
            reverse=True,
        )

    if not quality_items:
        return current

    default_index = 1
    rows = []
    for index, quality in enumerate(quality_items, start=1):
        if quality == current:
            default_index = index
        details = "best available" if index == 1 else "available"
        rows.append((quality.value, details))

    choice = choose_numbered_option(
        "Video quality",
        rows,
        default=default_index,
    )
    return quality_items[choice - 1]


def render_seasons_table(seasons: SeasonsModel) -> None:
    table = Table(
        title="Available seasons",
        border_style=THEME.neon_soft,
        header_style=f"bold {THEME.text}",
        show_lines=False,
    )
    table.add_column("Season", justify="right", style="bold cyan")
    table.add_column("Episodes", justify="right", style="green")
    table.add_column("Qualities", style="blue")

    for season in seasons.seasons:
        qualities = ", ".join(
            f"{item.resolution.value}P"
            for item in sorted(
                season.resolutions,
                key=lambda item: item.resolution.value,
                reverse=True,
            )
        )
        table.add_row(str(season.se), str(season.max_ep), qualities or "-")

    console.print(table)


def choose_quick_series_range(seasons: SeasonsModel) -> tuple[int, int, int]:
    render_seasons_table(seasons)
    season_numbers = [season.se for season in seasons.seasons]
    default_season = season_numbers[0] if season_numbers else 1
    season = click.prompt(
        "Season",
        type=click.Choice([str(item) for item in season_numbers]),
        default=str(default_season),
        show_default=True,
    )
    season_number = int(season)
    season_details = seasons.get_season_by_number(season_number)
    episode = click.prompt(
        f"Start episode (1-{season_details.max_ep})",
        type=click.IntRange(1, season_details.max_ep),
        default=1,
        show_default=True,
    )
    remaining = season_details.max_ep - episode + 1
    limit = click.prompt(
        f"Download count (1-{remaining})",
        type=click.IntRange(1, remaining),
        default=1,
        show_default=True,
    )
    return season_number, episode, limit


def format_episode_range(season: int, episode: int, limit: int) -> str:
    if limit <= 1:
        return f"S{season}E{episode}"
    end_episode = episode + limit - 1
    return f"S{season}E{episode}-E{end_episode}"


def choose_action() -> str:
    """Ask whether to download to disk or stream in the browser."""
    choice = choose_numbered_option(
        "What next?",
        [
            ("Download", "save to your folder"),
            ("Stream", "watch now in your browser, no player needed"),
        ],
        default=1,
    )
    return "download" if choice == 1 else "stream"


def render_download_summary(
    *,
    selected: ResultsSubjectModel,
    audio: str,
    quality: CustomResolutionType,
    target_dir: str | Path,
    season: int | None = None,
    episode: int | None = None,
    limit: int | None = None,
    stream: bool = False,
) -> None:
    rows = [
        ("Title", selected.title),
        ("Type", display_subject_type(selected.subject_type)),
        ("Year", item_year(selected)),
        ("Audio", audio),
        ("Quality", quality.value),
        ("Stream", "Browser (no download)") if stream else ("Folder", str(target_dir)),
    ]
    if selected.subject_type is SubjectType.TV_SERIES:
        rows.insert(
            3,
            (
                "Episodes",
                format_episode_range(season or 1, episode or 1, limit or 1),
            ),
        )

    summary = "\n".join(
        f"[bold]{label}:[/bold] {value}" for label, value in rows
    )
    console.print(
        Panel(
            summary,
            title="Stream summary" if stream else "Download summary",
            border_style=THEME.neon_soft,
        )
    )


def filter_items_by_year(
    items: list[ResultsSubjectModel], year: int | None
) -> list[ResultsSubjectModel]:
    if not year:
        return items
    return [
        item
        for item in items
        if item.release_date is not None and item.release_date.year == year
    ]


def render_results_table(items: list[ResultsSubjectModel]) -> None:
    table = Table(
        title="movie-box search results",
        border_style=THEME.neon_soft,
        header_style=f"bold {THEME.text}",
        show_lines=False,
    )
    table.add_column("#", justify="right", style="bold cyan", no_wrap=True)
    table.add_column("Title", style="bold", overflow="fold", ratio=3)
    table.add_column("Type", style="magenta")
    table.add_column("Year", justify="right", style="green")
    table.add_column("IMDb", justify="right", style="yellow")
    table.add_column("Listed Langs", style="blue", overflow="ellipsis")

    for index, item in enumerate(items, start=1):
        table.add_row(
            str(index),
            item.title,
            display_subject_type(item.subject_type),
            item_year(item),
            f"{item.imdb_rating_value:g}" if item.imdb_rating_value else "-",
            format_languages(item),
        )

    console.print(table)


def render_selected_item(item: ResultsSubjectModel) -> None:
    imdb = f"{item.imdb_rating_value:g}" if item.imdb_rating_value else "-"
    details = (
        f"[bold]{item.title}[/bold]\n"
        f"Type: {display_subject_type(item.subject_type)}\n"
        f"Year: {item_year(item)}\n"
        f"IMDb: {imdb}\n"
        f"Listed Langs: {format_languages(item)}\n"
        f"Subject ID: {item.subject_id}"
    )
    console.print(Panel(details, title="Selected", border_style="green"))


def choose_item(
    items: list[ResultsSubjectModel], *, yes: bool = False
) -> ResultsSubjectModel:
    if not items:
        raise click.ClickException(
            "No results found. Bold of you to assume that movie exists — "
            "try a different query."
        )
    if yes or len(items) == 1:
        return items[0]

    choice = click.prompt(
        "Select a result",
        type=click.IntRange(1, len(items)),
        default=1,
        show_default=True,
    )
    return items[choice - 1]


def choose_numbered_option(
    title: str,
    rows: list[tuple[str, str]],
    *,
    default: int = 1,
) -> int:
    if not rows:
        raise click.ClickException(f"No choices available for {title.lower()}.")

    table = Table(
        title=title,
        border_style=THEME.neon_soft,
        header_style=f"bold {THEME.text}",
        show_lines=False,
    )
    table.add_column("#", justify="right", style="bold cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Details", style="blue")

    for index, (name, details) in enumerate(rows, start=1):
        table.add_row(str(index), name, details)

    console.print(table)
    return click.prompt(
        title,
        type=click.IntRange(1, len(rows)),
        default=default,
        show_default=True,
    )


def choose_movie_dub(dubs: list[DubModel], current: str) -> str:
    default_index = 1
    rows = []
    for index, dub in enumerate(dubs, start=1):
        if current in {dub.lan_name, dub.lan_code}:
            default_index = index
        rows.append((dub.lan_name, f"code: {dub.lan_code}"))

    choice = choose_numbered_option(
        "Select audio dub",
        rows,
        default=default_index,
    )
    return dubs[choice - 1].lan_name


def choose_movie_quality(
    details: RootDownloadableFilesDetailModel,
    current: CustomResolutionType,
) -> CustomResolutionType:
    quality_items = sorted(
        details.get_quality_downloads_map().items(),
        key=lambda item: item[1].resolution,
        reverse=True,
    )
    if not quality_items:
        return current

    default_index = 1
    rows = []
    for index, (quality, media_file) in enumerate(quality_items, start=1):
        if quality == current:
            default_index = index
        rows.append((quality.value, f"{media_file.resolution}p"))

    choice = choose_numbered_option(
        "Select video quality",
        rows,
        default=default_index,
    )
    return quality_items[choice - 1][0]


def choose_caption_languages(
    captions: RootCaptionFileMetadata,
    current: tuple[str, ...],
) -> tuple[str, ...]:
    caption_items = captions.captions
    if not caption_items:
        return current

    default_index = 1
    normalized_current = {item.casefold() for item in current}
    rows = []
    for index, caption in enumerate(caption_items, start=1):
        if (
            caption.lan.casefold() in normalized_current
            or caption.lan_name.casefold() in normalized_current
        ):
            default_index = index
        rows.append((caption.lan_name, f"code: {caption.lan}"))

    choice = choose_numbered_option(
        "Select subtitle language",
        rows,
        default=default_index,
    )
    return (caption_items[choice - 1].lan,)


async def fetch_search_items(
    query: str,
    *,
    subject_type: SubjectType,
    year: int | None,
    limit: int,
    client_session: MovieBoxHttpClient | None = None,
) -> list[ResultsSubjectModel]:
    async def run(session: MovieBoxHttpClient) -> list[ResultsSubjectModel]:
        search = Search(
            session,
            query,
            subject_type=subject_type,
            per_page=max(1, min(limit, 20)),
        )
        result = await search.get_content_model()
        return filter_items_by_year(result.items, year)[:limit]

    if client_session is not None:
        return await run(client_session)

    async with MovieBoxHttpClient() as session:
        return await run(session)


def run(coro):
    from movie_box.v3.helpers import get_event_loop

    return get_event_loop().run_until_complete(coro)


async def rich_search_function(
    client_session: MovieBoxHttpClient,
    title: str,
    year: int,
    subject_type: SubjectType,
    yes: bool,
    **_: Any,
) -> ResultsSubjectModel:
    items = await fetch_search_items(
        title,
        subject_type=subject_type,
        year=year,
        limit=10,
        client_session=client_session,
    )
    render_results_table(items)
    selected = choose_item(items, yes=yes)
    render_selected_item(selected)
    return selected


@click.command("quick", hidden=True)
@click.argument("query_parts", nargs=-1)
def quick_command(query_parts: tuple[str, ...] = ()):
    """Guided one-screen download flow."""

    print_compact_header()
    config = load_config()
    query = " ".join(query_parts).strip()
    if not query:
        query = click.prompt("Search", type=str).strip()
    if not query:
        raise click.ClickException("Search cannot be empty.")

    target_dir = config.get("dir", CURRENT_WORKING_DIR)
    caption_dir = config.get("caption_dir", target_dir)

    async def run_quick():
        async with MovieBoxHttpClient() as session:
            items = await fetch_search_items(
                query,
                subject_type=SubjectType.ALL,
                year=0,
                limit=8,
                client_session=session,
            )
            selected = choose_quick_result(items)
            subject_type = selected.subject_type

            console.print(
                f"[dim]Detected:[/dim] "
                f"[bold]{quick_subject_label(subject_type)}[/bold]"
            )
            render_selected_item(selected)

            item_details = await ItemDetails(session).get_content_model(
                selected.subject_id
            )
            dub_default = (
                language_hint_from_title(selected.title)
                or config.get("dub", QUICK_DEFAULT_DUB)
            )
            selected_dub = choose_quick_dub(item_details.dubs, dub_default)
            target_subject_id = (
                selected_dub.subject_id if selected_dub else selected.subject_id
            )

            if subject_type is SubjectType.TV_SERIES:
                series_info = await SeasonDetails(session).get_content_model(
                    target_subject_id
                )
                season, episode, limit = choose_quick_series_range(
                    series_info
                )
            else:
                season = episode = limit = 1

            downloadable_details = await DownloadableFilesDetail(
                session
            ).get_content_model(
                target_subject_id,
                release_date=str(selected.release_date),
            )
            quality = choose_quick_quality(
                downloadable_details,
                normalize_quality(
                    config.get("quality", CustomResolutionType.BEST.value)
                ),
            )
            audio_name = selected_dub.lan_name if selected_dub else "Original"
            action = choose_action()
            streaming = action == "stream"
            stream_via = "browser" if streaming else None
            render_download_summary(
                selected=selected,
                audio=audio_name,
                quality=quality,
                target_dir=target_dir,
                season=season,
                episode=episode,
                limit=limit,
                stream=streaming,
            )
            prompt = "Stream?" if streaming else "Download?"
            if not click.confirm(prompt, default=True, show_default=True):
                console.print("[yellow]Cancelled.[/yellow]")
                return

            async def selected_item_search_function(
                *_: Any, **__: Any
            ) -> ResultsSubjectModel:
                return selected

            downloader = Downloader(session)
            if subject_type is SubjectType.TV_SERIES:
                await downloader.download_tv_series(
                    selected.title,
                    year=selected.release_date.year if selected.release_date else 0,
                    season=season,
                    episode=episode,
                    limit=limit,
                    yes=True,
                    dir=target_dir,
                    caption_dir=caption_dir,
                    quality=quality,
                    language=(DEFAULT_CAPTION_LANGUAGE,),
                    download_caption=False,
                    stream_via=stream_via,
                    search_function=selected_item_search_function,
                    dub=audio_name,
                )
                return

            await downloader.download_movie(
                selected.title,
                year=selected.release_date.year if selected.release_date else 0,
                yes=True,
                dir=target_dir,
                caption_dir=caption_dir,
                quality=quality,
                language=(DEFAULT_CAPTION_LANGUAGE,),
                download_caption=False,
                caption_only=False,
                stream_via=stream_via,
                search_function=selected_item_search_function,
                dub=audio_name,
            )

    run(run_quick())


@click.command("search")
@click.argument("query")
@click.option(
    "-t",
    "--type",
    "subject_type_name",
    type=click.Choice(sorted(SUBJECT_TYPE_CHOICES), case_sensitive=False),
    default="all",
    show_default=True,
    help="Result type to search for.",
)
@click.option("-y", "--year", type=int, default=0, help="Filter by release year.")
@click.option("-l", "--limit", type=click.IntRange(1, 20), default=10, show_default=True)
@click.option("--select/--no-select", default=False, help="Prompt to select one result.")
def search_command(query: str, subject_type_name: str, year: int, limit: int, select: bool):
    """Search and show colorful, selectable results."""

    print_compact_header()
    subject_type = subject_type_from_choice(subject_type_name)
    items = run(
        fetch_search_items(
            query,
            subject_type=subject_type,
            year=year,
            limit=limit,
        )
    )
    render_results_table(items)
    if select:
        render_selected_item(choose_item(items))


@click.command("movie")
@click.argument("title")
@click.option("-y", "--year", type=int, default=0, help="Filter by release year.")
@click.option("-q", "--quality", default=None, help="Quality: best, 1080P, 720P, 480P, 360P.")
@click.option("-d", "--dir", "download_dir", default=None, type=click.Path(file_okay=False))
@click.option("-x", "--language", multiple=True, help="Subtitle language.")
@click.option("-u", "--dub", default=None, help="Dub language name or code.")
@click.option("--caption/--no-caption", default=False, help="Download subtitle files.")
@click.option("--caption-only", is_flag=True, help="Download subtitle files only.")
@click.option(
    "--stream-via",
    type=click.Choice(["browser", "mpv", "vlc"]),
    default=None,
    help="Stream instead of download. 'browser' needs no extra player.",
)
@click.option("--dry-run", is_flag=True, help="Preview selected result without downloading.")
@click.option("-Y", "--yes", is_flag=True, help="Use first result without prompting.")
def movie_command(
    title: str,
    year: int,
    quality: str | None,
    download_dir: str | None,
    language: tuple[str, ...],
    dub: str | None,
    caption: bool,
    caption_only: bool,
    stream_via: str | None,
    dry_run: bool,
    yes: bool,
):
    """Search, select, and download a movie with a nicer prompt."""

    print_compact_header()
    config = load_config()
    quality_value = quality or config.get("quality", CustomResolutionType.BEST.value)
    target_dir = download_dir or config.get("dir", CURRENT_WORKING_DIR)
    caption_dir = config.get("caption_dir", target_dir)
    languages = language or tuple(config.get("language", [DEFAULT_CAPTION_LANGUAGE]))
    dub_value = dub or config.get("dub", DEFAULT_DUB_LANGUAGE_NAME_OR_CODE)

    async def run_movie():
        async with MovieBoxHttpClient() as session:
            if dry_run:
                items = await fetch_search_items(
                    title,
                    subject_type=SubjectType.MOVIES,
                    year=year,
                    limit=10,
                    client_session=session,
                )
                render_results_table(items)
                render_selected_item(choose_item(items, yes=yes))
                console.print("[yellow]Dry run only. No files downloaded.[/yellow]")
                return

            downloader = Downloader(session)
            await downloader.download_movie(
                title,
                year=year,
                yes=yes,
                dir=target_dir,
                caption_dir=caption_dir,
                quality=normalize_quality(quality_value),
                language=languages,
                download_caption=caption,
                caption_only=caption_only,
                stream_via=stream_via,
                search_function=rich_search_function,
                dub=dub_value,
                dub_selector=None if yes or dub else choose_movie_dub,
                quality_selector=(
                    None if yes or quality else choose_movie_quality
                ),
                caption_language_selector=(
                    None if yes or language else choose_caption_languages
                ),
            )

    run(run_movie())


@click.command("series")
@click.argument("title")
@click.option("-y", "--year", type=int, default=0, help="Filter by release year.")
@click.option("-s", "--season", type=click.IntRange(1, 1000), default=1, show_default=True)
@click.option("-e", "--episode", type=click.IntRange(1, 1000), default=1, show_default=True)
@click.option("-l", "--limit", type=click.IntRange(-1, 1000), default=1, show_default=True)
@click.option("-q", "--quality", default=None, help="Quality: best, 1080P, 720P, 480P, 360P.")
@click.option("-d", "--dir", "download_dir", default=None, type=click.Path(file_okay=False))
@click.option("-x", "--language", multiple=True, help="Subtitle language.")
@click.option("-u", "--dub", default=None, help="Dub language name or code.")
@click.option("--caption/--no-caption", default=False, help="Download subtitle files.")
@click.option(
    "--stream-via",
    type=click.Choice(["browser", "mpv", "vlc"]),
    default=None,
    help="Stream instead of download. 'browser' needs no extra player.",
)
@click.option("--dry-run", is_flag=True, help="Preview selected result without downloading.")
@click.option("-Y", "--yes", is_flag=True, help="Use first result without prompting.")
def series_command(
    title: str,
    year: int,
    season: int,
    episode: int,
    limit: int,
    quality: str | None,
    download_dir: str | None,
    language: tuple[str, ...],
    dub: str | None,
    caption: bool,
    stream_via: str | None,
    dry_run: bool,
    yes: bool,
):
    """Search, select, and download a TV series episode or batch."""

    print_compact_header()
    config = load_config()
    quality_value = quality or config.get("quality", CustomResolutionType.BEST.value)
    target_dir = download_dir or config.get("dir", CURRENT_WORKING_DIR)
    caption_dir = config.get("caption_dir", target_dir)
    languages = language or tuple(config.get("language", [DEFAULT_CAPTION_LANGUAGE]))
    dub_value = dub or config.get("dub", DEFAULT_DUB_LANGUAGE_NAME_OR_CODE)

    async def run_series():
        async with MovieBoxHttpClient() as session:
            if dry_run:
                items = await fetch_search_items(
                    title,
                    subject_type=SubjectType.TV_SERIES,
                    year=year,
                    limit=10,
                    client_session=session,
                )
                render_results_table(items)
                render_selected_item(choose_item(items, yes=yes))
                console.print("[yellow]Dry run only. No files downloaded.[/yellow]")
                return

            downloader = Downloader(session)
            await downloader.download_tv_series(
                title,
                year=year,
                season=season,
                episode=episode,
                limit=limit,
                yes=yes,
                dir=target_dir,
                caption_dir=caption_dir,
                quality=normalize_quality(quality_value),
                language=languages,
                download_caption=caption,
                stream_via=stream_via,
                search_function=rich_search_function,
                dub=dub_value,
            )

    run(run_series())


@click.command("ui")
@click.option(
    "--no-animation",
    is_flag=True,
    help="Open instantly without the startup animation.",
)
def ui_command(no_animation: bool):
    """Open the interactive cyberpunk movie-box shell."""

    engine = CommandEngine(console)
    last_items: list[ResultsSubjectModel] = []
    if no_animation:
        print_banner()
    else:
        run_boot_sequence(console)
    engine.render_help()

    while True:
        try:
            command_line = prompt_shell_input()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]closing movie-box shell[/dim]")
            return

        command, argument = engine.parse(command_line)
        if command.isdigit() and last_items:
            argument = command
            command = "select"
        elif command and command not in {
            "exit",
            "quit",
            "q",
            "clear",
            "help",
            "config",
            "doctor",
            "search",
            "movie",
            "series",
            "select",
            "download",
            "credits",
        }:
            argument = command_line.strip()
            command = "search"

        if not command:
            continue
        if command in {"exit", "quit", "q"}:
            console.print(f"[{THEME.neon_soft}]session closed[/]")
            return
        if command == "clear":
            console.clear()
            console.print(render_compact_header())
            continue
        if command == "help":
            engine.render_help()
            continue
        if command == "config":
            config = load_config()
            if config:
                console.print_json(json.dumps(config, indent=2, sort_keys=True))
            else:
                console.print("[yellow]No config saved yet.[/yellow]")
            console.print(f"[dim]Config path: {get_config_path()}[/dim]")
            continue
        if command == "doctor":
            console.print(
                "[dim]Run[/dim] [bold]movie-box doctor[/bold] "
                "[dim]for the full environment check.[/dim]"
            )
            continue
        if command == "credits":
            console.print(
                Panel(
                    "\n".join(
                        [
                            "built by parthmax",
                            "powered by httpx, pydantic, rich, click",
                            "fueled by spite for ad-walled redirects",
                            "",
                            "you've reached the end of the documentation.",
                            "there is no prize.",
                            "there is a --help flag.",
                            "",
                            "long live the moviebox spirit.",
                        ]
                    ),
                    title="MOVIE-BOX",
                    border_style=THEME.neon,
                    title_align="center",
                )
            )
            continue
        if command == "select":
            if not last_items:
                console.print(f"[{THEME.warning}]Run /search <title> first.[/]")
                continue
            if not argument.isdigit():
                console.print(f"[{THEME.warning}]Usage:[/] /select <number>")
                continue
            index = int(argument)
            if index < 1 or index > len(last_items):
                console.print(
                    f"[{THEME.warning}]Choose a number from 1 to {len(last_items)}.[/]"
                )
                continue
            selected = last_items[index - 1]
            render_selected_item(selected)
            console.print(
                f"[dim]Download with[/dim] [bold]/download {index}[/bold] "
                "[dim]or preview another result number.[/dim]"
            )
            continue
        if command == "download":
            if not last_items:
                console.print(f"[{THEME.warning}]Run /search <title> first.[/]")
                continue
            if not argument.isdigit():
                console.print(f"[{THEME.warning}]Usage:[/] /download <number>")
                continue
            index = int(argument)
            if index < 1 or index > len(last_items):
                console.print(
                    f"[{THEME.warning}]Choose a number from 1 to {len(last_items)}.[/]"
                )
                continue
            selected = last_items[index - 1]
            if selected.subject_type != SubjectType.MOVIES:
                console.print(
                    f"[{THEME.warning}]Only movie results can be downloaded from "
                    "the shell right now. Use movie-box series for episodes.[/]"
                )
                continue

            config = load_config()
            target_dir = config.get("dir", CURRENT_WORKING_DIR)
            caption_dir = config.get("caption_dir", target_dir)
            languages = tuple(config.get("language", [DEFAULT_CAPTION_LANGUAGE]))
            dub_value = config.get("dub", DEFAULT_DUB_LANGUAGE_NAME_OR_CODE)
            quality_value = config.get("quality", CustomResolutionType.BEST.value)

            async def selected_item_search_function(
                *_: Any, **__: Any
            ) -> ResultsSubjectModel:
                return selected

            async def download_selected_movie():
                async with MovieBoxHttpClient() as session:
                    downloader = Downloader(session)
                    await downloader.download_movie(
                        selected.title,
                        year=selected.release_date.year if selected.release_date else 0,
                        yes=True,
                        dir=target_dir,
                        caption_dir=caption_dir,
                        quality=normalize_quality(quality_value),
                        language=languages,
                        download_caption=False,
                        caption_only=False,
                        stream_via=None,
                        search_function=selected_item_search_function,
                        dub=dub_value,
                        dub_selector=choose_movie_dub,
                        quality_selector=choose_movie_quality,
                    )

            render_selected_item(selected)
            console.print(
                f"[{THEME.neon_soft}]Downloading selected movie to[/] {target_dir}"
            )
            run(download_selected_movie())
            continue
        if command in {"search", "movie", "series"}:
            if not argument:
                console.print(
                    f"[{THEME.warning}]Usage:[/] /{command} <title>"
                )
                continue
            subject_type = (
                SubjectType.TV_SERIES if command == "series" else SubjectType.MOVIES
            )
            if command == "search":
                subject_type = SubjectType.ALL
            items = run(
                fetch_search_items(
                    argument,
                    subject_type=subject_type,
                    year=0,
                    limit=8,
                )
            )
            last_items = items
            render_results_table(items)
            if command in {"movie", "series"}:
                render_selected_item(choose_item(items))
            elif items:
                console.print(
                    "[dim]Type a result number to preview, or[/dim] "
                    "[bold]/download 1[/bold] [dim]to download a movie result.[/dim]"
                )
            continue

        console.print(
            f"[{THEME.danger}]Unknown command:[/] {command!r}. "
            "Type [bold]/help[/bold]."
        )


@click.command("app")
def app_command():
    """Open the full-screen Textual cyberpunk app."""

    try:
        launch_textual_app()
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc


@click.group("config")
def config_command():
    """Show and edit movie-box defaults."""


@config_command.command("show")
def config_show():
    """Show saved defaults."""

    config = load_config()
    if not config:
        console.print("[yellow]No config saved yet.[/yellow]")
        console.print(f"Config path: {get_config_path()}")
        return
    console.print_json(json.dumps(config, indent=2, sort_keys=True))
    console.print(f"Config path: {get_config_path()}")


@config_command.command("set")
@click.argument("key", type=click.Choice(sorted(CONFIG_KEYS)))
@click.argument("value", nargs=-1, required=True)
def config_set(key: str, value: tuple[str, ...]):
    """Save a default value."""

    config = load_config()
    if key == "language":
        config[key] = list(value)
    else:
        config[key] = " ".join(value)
    save_config(config)
    console.print(f"[green]Saved[/green] {key} = {config[key]!r}")


@config_command.command("get")
@click.argument("key", type=click.Choice(sorted(CONFIG_KEYS)))
def config_get(key: str):
    """Read a saved default value."""

    config = load_config()
    if key not in config:
        raise click.ClickException(f"No saved value for {key!r}.")
    console.print(config[key])


@config_command.command("reset")
@click.option("-Y", "--yes", is_flag=True, help="Reset without confirmation.")
def config_reset(yes: bool):
    """Delete saved defaults."""

    path = get_config_path()
    if not path.exists():
        console.print("[yellow]No config file exists.[/yellow]")
        return
    if yes or click.confirm(f"Delete {path}?"):
        path.unlink()
        console.print("[green]Config reset.[/green]")


FRIENDLY_COMMANDS = (
    quick_command,
    search_command,
    movie_command,
    series_command,
    ui_command,
    app_command,
    config_command,
)
