import logging
import os
import sys

import click


def clean_error_message(exception: Exception) -> str:
    if isinstance(exception, click.ClickException):
        return exception.format_message()

    if len(exception.args) > 1 and isinstance(exception.args[1], str):
        return exception.args[1]

    message = str(exception).strip()
    return message or exception.__class__.__name__


def handle_cli_error(
    exception: Exception,
    *,
    show_help,
    debug: bool | None = None,
) -> None:
    debug = os.getenv("DEBUG", "0") == "1" if debug is None else debug
    message = clean_error_message(exception)

    if debug:
        logging.exception(exception)
        sys.exit(1)

    if message:
        click.secho(f"Error: {message}", fg="red", err=True)

    sys.exit(show_help(exception, message))
