import subprocess
import sys

import pytest


def run_system_command(command: str) -> int:
    python = f'"{sys.executable}"'
    try:
        result = subprocess.run(
            (
                f"{python} -m movie_box v1 " + command
                if not command.startswith("python")
                else command.replace("python", python, 1)
            ),
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(e.stderr, e.output, sep="\n")
        return e.returncode


def test_version():
    returncode = run_system_command("python -m movie_box --version")
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["download-movie --help"],
        ["download-series --help"],
        ["mirror-hosts --help"],
        ["homepage-content --help"],
        ["popular-search --help"],
        ["item-details --help"],
    ],
)
def test_help(command):
    returncode = run_system_command(command)
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["download-movie avatar -YT"],
        ["download-series merlin -s 1 -e 1 -YT"],
    ],
)
def test_download(command):
    returncode = run_system_command(command)
    assert returncode <= 0


def test_mirror_hosts():
    returncode = run_system_command("mirror-hosts --json")
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=[
        ["homepage-content"],
        ["homepage-content --json"],
        ["homepage-content --banner"],
        ["homepage-content --banner --json"],
        ["homepage-content --title 'Bollywood'"],
    ],
)
def test_homepage(command):
    returncode = run_system_command(command)
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=(["popular-search"], ["popular-search --json"]),
)
def test_popular_search(command):
    returncode = run_system_command(command)
    assert returncode <= 0


@pytest.mark.parametrize(
    argnames=[
        "command",
    ],
    argvalues=(
        ["item-details Merlin --yes --json"],
        ["item-details Avatar -s MOVIES -Y -F"],
    ),
)
def test_item_details(command):
    returncode = run_system_command(command)
    assert returncode <= 0
