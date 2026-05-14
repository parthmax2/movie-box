from __future__ import annotations

from io import StringIO
from importlib import metadata

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from movie_box.tui.theme import THEME

TITLE_FALLBACK = (
    r"##   ##  ####  ##   ##  ####  #######       ####    ####  ##   ##",
    r"### ### ##  ## ##   ##   ##   ##           ##  ##  ##  ##  ## ## ",
    r"####### ##  ## ##   ##   ##   #####        #####   ##  ##   ###  ",
    r"## # ## ##  ##  ## ##    ##   ##           ##  ##  ##  ##  ## ## ",
    r"##   ##  ####    ###    ####  #######      #####    ####  ##   ##",
)


def package_version() -> str:
    try:
        return metadata.version("movie-box")
    except metadata.PackageNotFoundError:
        return "dev"


def title_lines() -> tuple[str, ...]:
    try:
        from pyfiglet import Figlet
    except ImportError:
        return TITLE_FALLBACK

    rendered = Figlet(font="ansi_shadow", width=100).renderText("MOVIE BOX")
    lines = tuple(line.rstrip() for line in rendered.splitlines() if line.strip())
    return lines or TITLE_FALLBACK


def gradient_text(lines: tuple[str, ...]) -> Text:
    output = Text()
    styles = THEME.gradient
    for index, line in enumerate(lines):
        output.append(line, style=styles[index % len(styles)])
        output.append("\n")
    return output


def glow_title(*, shadow: bool = False) -> Text:
    lines = title_lines()
    glow = Text()
    if shadow:
        for line in lines:
            glow.append(f" {line}\n", style=f"{THEME.dim}")
    glow.append_text(gradient_text(lines))
    return glow


def command_table() -> Table:
    table = Table.grid(padding=(0, 3))
    table.add_column(style=f"bold {THEME.text}", no_wrap=True)
    table.add_column(style=THEME.muted)
    table.add_row("movie-box search", "find movies and series")
    table.add_row("movie-box movie", "select and download a movie")
    table.add_row("movie-box series", "select and download episodes")
    table.add_row("movie-box config", "save quality, language, and folders")
    table.add_row("movie-box ui", "open the interactive cyberpunk shell")
    table.add_row("movie-box doctor", "check your local setup")
    return table


def welcome_panel() -> Panel:
    label = Text()
    label.append("* ", style=f"bold {THEME.neon_soft}")
    label.append("Welcome to ", style=THEME.text)
    label.append("MOVIE-BOX CLI", style=f"bold {THEME.text}")
    return Panel.fit(
        label,
        box=box.ASCII,
        border_style=THEME.dim,
        style=f"on {THEME.surface}",
        padding=(0, 1),
    )


def render_banner(*, width: int = 100) -> str:
    output = StringIO()
    banner_console = Console(
        file=output,
        force_terminal=True,
        color_system="truecolor",
        width=width,
    )
    banner_console.print(welcome_panel())
    banner_console.print()
    banner_console.print(glow_title())
    banner_console.print(
        f"v{package_version()}   developed by [bold {THEME.neon_soft}]parthmax[/]",
        style=THEME.muted,
        highlight=False,
    )
    banner_console.print()
    banner_console.print(command_table())
    return output.getvalue()


def print_banner(console: Console) -> None:
    console.print(welcome_panel())
    console.print()
    console.print(glow_title())
    console.print(
        f"v{package_version()}   developed by [bold {THEME.neon_soft}]parthmax[/]",
        style=THEME.muted,
        highlight=False,
    )
    console.print()
    console.print(command_table())


def render_compact_header() -> Panel:
    title = Text()
    title.append("MOVIE-BOX", style=f"bold {THEME.neon_soft}")
    title.append(f" v{package_version()}", style=THEME.muted)
    title.append("  developed by parthmax", style=f"bold {THEME.text}")
    return Panel(
        Align.left(title),
        box=box.ASCII,
        border_style=THEME.neon,
        style=f"on {THEME.background}",
        padding=(0, 1),
    )
