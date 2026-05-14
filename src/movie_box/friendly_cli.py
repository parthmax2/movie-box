import json
import os
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
from movie_box.v3.core import Search
from movie_box.v3.http_client import MovieBoxHttpClient
from movie_box.v3.models.search import ResultsSubjectModel
from movie_box.tui.art import print_banner as print_tui_banner
from movie_box.tui.art import render_banner, render_compact_header
from movie_box.tui.command_engine import CommandEngine
from movie_box.tui.splash import run_boot_sequence
from movie_box.tui.textual_app import launch_textual_app
from movie_box.tui.theme import THEME

console = Console()

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
    table.add_column("Languages", style="blue", overflow="ellipsis")

    for index, item in enumerate(items, start=1):
        table.add_row(
            str(index),
            item.title,
            item.subject_type.name.replace("_", " ").title(),
            item_year(item),
            f"{item.imdb_rating_value:g}" if item.imdb_rating_value else "-",
            format_languages(item),
        )

    console.print(table)


def render_selected_item(item: ResultsSubjectModel) -> None:
    imdb = f"{item.imdb_rating_value:g}" if item.imdb_rating_value else "-"
    details = (
        f"[bold]{item.title}[/bold]\n"
        f"Type: {item.subject_type.name.replace('_', ' ').title()}\n"
        f"Year: {item_year(item)}\n"
        f"IMDb: {imdb}\n"
        f"Languages: {format_languages(item)}\n"
        f"Subject ID: {item.subject_id}"
    )
    console.print(Panel(details, title="Selected", border_style="green"))


def choose_item(
    items: list[ResultsSubjectModel], *, yes: bool = False
) -> ResultsSubjectModel:
    if not items:
        raise click.ClickException("No results found. Try a different query.")
    if yes or len(items) == 1:
        return items[0]

    choice = click.prompt(
        "Select a result",
        type=click.IntRange(1, len(items)),
        default=1,
        show_default=True,
    )
    return items[choice - 1]


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
@click.option("--stream-via", type=click.Choice(["mpv", "vlc"]), default=None)
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
@click.option("--stream-via", type=click.Choice(["mpv", "vlc"]), default=None)
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
    search_command,
    movie_command,
    series_command,
    ui_command,
    app_command,
    config_command,
)
