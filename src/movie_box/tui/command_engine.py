from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

from movie_box.tui.theme import THEME


@dataclass(frozen=True)
class CommandSpec:
    name: str
    usage: str
    description: str


COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("help", "/help", "show command menu"),
    CommandSpec("search", "/search <title>", "search movie-box results"),
    CommandSpec("select", "/select <number>", "select a result from the last search"),
    CommandSpec("download", "/download <number>", "download a movie from last results"),
    CommandSpec("movie", "/movie <title>", "preview movie matches"),
    CommandSpec("series", "/series <title>", "preview TV series matches"),
    CommandSpec("config", "/config", "show saved CLI defaults"),
    CommandSpec("doctor", "/doctor", "show local environment hints"),
    CommandSpec("clear", "/clear", "clear the terminal"),
    CommandSpec("exit", "/exit", "close the shell"),
)


class CommandEngine:
    def __init__(self, console: Console) -> None:
        self.console = console

    def render_help(self) -> None:
        table = Table(
            title="movie-box command deck",
            border_style=THEME.neon,
            header_style=f"bold {THEME.neon_soft}",
            title_style=f"bold {THEME.text}",
            show_lines=False,
        )
        table.add_column("Command", style=f"bold {THEME.text}", no_wrap=True)
        table.add_column("Action", style=THEME.muted)
        for command in COMMANDS:
            table.add_row(command.usage, command.description)
        self.console.print(table)

    def parse(self, value: str) -> tuple[str, str]:
        cleaned = value.strip()
        if not cleaned:
            return "", ""
        if cleaned.startswith("/"):
            cleaned = cleaned[1:]
        command, _, argument = cleaned.partition(" ")
        return command.lower(), argument.strip()
