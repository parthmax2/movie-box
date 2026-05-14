from __future__ import annotations

import asyncio

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.text import Text

from movie_box.tui.art import glow_title, print_banner
from movie_box.tui.theme import THEME


BOOT_STEPS = (
    "warming neon renderer",
    "loading command engine",
    "syncing movie-box modules",
    "checking parthmax build signature",
    "opening terminal interface",
)


async def boot_sequence(console: Console, *, delay: float = 0.16) -> None:
    console.clear()
    with Progress(
        SpinnerColumn(style=THEME.neon_soft),
        TextColumn("[bold #f5f3ff]{task.description}"),
        BarColumn(
            bar_width=36,
            complete_style=THEME.neon,
            finished_style=THEME.neon_soft,
            pulse_style=THEME.violet,
        ),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("initializing movie-box", total=len(BOOT_STEPS))
        for step in BOOT_STEPS:
            progress.update(task, description=step, advance=1)
            await asyncio.sleep(delay)

    frames = (
        Text("MOVIE-BOX", style=f"bold {THEME.dim}"),
        Text("MOVIE-BOX", style=f"bold {THEME.violet}"),
        Text("MOVIE-BOX", style=f"bold {THEME.neon}"),
        glow_title(shadow=True),
    )
    with Live(console=console, refresh_per_second=18, transient=True) as live:
        for frame in frames:
            live.update(
                Panel(frame, box=box.ASCII, border_style=THEME.neon, padding=(1, 2))
            )
            await asyncio.sleep(delay)

    print_banner(console)


def run_boot_sequence(console: Console) -> None:
    asyncio.run(boot_sequence(console))
