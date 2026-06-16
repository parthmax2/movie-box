import shutil
import sys
from importlib import metadata
from importlib.util import find_spec

import click

from movie_box import __version__
from movie_box.cli_errors import handle_cli_error
from movie_box.friendly_cli import (
    FRIENDLY_COMMANDS,
    quick_command,
    render_banner,
    ui_command,
)
from movie_box.utils import build_command_group
from movie_box.v1.cli.helpers import show_any_help
from movie_box.v1.cli.interface import get_commands_map
from movie_box.v2.cli.interface import get_commands_map as get_commmands_map_2
from movie_box.v3.cli.interface import get_commands_map as get_commmands_map_3


class BrandedGroup(click.Group):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        formatter.write(render_banner())
        formatter.write("\n")
        super().format_help(ctx, formatter)

    def resolve_command(self, ctx, args):
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            if args and not args[0].startswith("-"):
                return "quick", quick_command, args
            raise


@click.group(cls=BrandedGroup, invoke_without_command=True)
@click.version_option(package_name="movie-box")
@click.pass_context
def _cli_entry(ctx: click.Context):
    """Search and download movies/tv-series and their subtitles
    (environment variable prefix : MOVIEBOX_{V1/V2/V3})

    Developed by parthmax."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(quick_command)


@_cli_entry.group()
def v1():
    """Search and download movies/tv-series using movie-box v1
    (environment variable prefix: MOVIEBOX_V1)"""


@_cli_entry.group()
def v2():
    """Search and download movies/tv-series etc using movie-box v2
    (environment variable prefix: MOVIEBOX_V2)"""


@_cli_entry.group()
def v3():
    """Search and download movies/tv-series etc using movie-box v3
    (environment variable prefix: MOVIEBOX_V3)"""


@click.command()
def doctor():
    """Check the local movie-box CLI environment."""

    click.echo(render_banner(), nl=False)
    click.echo(f"movie-box: {__version__}")
    click.echo("developer: parthmax")
    click.echo(f"python: {sys.version.split()[0]} ({sys.executable})")

    required_packages = ("click", "httpx", "pydantic", "throttlebuster", "bs4")
    for package in required_packages:
        try:
            version = metadata.version(package)
        except metadata.PackageNotFoundError:
            click.echo(f"{package}: missing")
        else:
            click.echo(f"{package}: {version}")

    for module_name in ("movie_box.v1", "movie_box.v2", "movie_box.v3"):
        status = "ok" if find_spec(module_name) else "missing"
        click.echo(f"{module_name}: {status}")

    for player in ("mpv", "vlc"):
        path = shutil.which(player)
        click.echo(f"{player}: {path or 'not found'}")


_cli_entry.add_command(doctor, "doctor")
_cli_entry.add_command(ui_command, "shell")
for command in FRIENDLY_COMMANDS:
    _cli_entry.add_command(command)
build_command_group(v1, get_commands_map())
build_command_group(v2, get_commmands_map_2())
build_command_group(v3, get_commmands_map_3())


def cli_entry():
    try:
        return _cli_entry()

    except Exception as e:
        handle_cli_error(e, show_help=show_any_help)

    sys.exit(1)
