<div align="center">

# movie-box

**movie-box by parthmax: CLI movie downloader and Python API**  
Search, inspect, download, stream, and manage subtitles from one Python tool.

[![PyPI version](https://badge.fury.io/py/movie-box-dl.svg)](https://pypi.org/project/movie-box-dl)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/movie-box-dl)](https://pypi.org/project/movie-box-dl)
![Coverage](https://raw.githubusercontent.com/parthmax2/movie-box/refs/heads/main/assets/coverage.svg)
[![PyPI - License](https://img.shields.io/pypi/l/movie-box-dl)](https://pypi.org/project/movie-box-dl)
[![Downloads](https://pepy.tech/badge/movie-box-dl)](https://pepy.tech/project/movie-box-dl)
[![CI](https://github.com/parthmax2/movie-box/actions/workflows/ci.yml/badge.svg)](https://github.com/parthmax2/movie-box/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[Install](#installation) | [Quick Start](#quick-start) | [CLI](#usage) | [Python API](#python-api) | [Disclaimer](#disclaimer) | [Docs](https://moviebox.parthmax.in)

![movie-box CLI](assets/cli.png)


</div>


## Why movie-box?

`movie-box` is built for people who want a scriptable downloader with a clean
CLI, async Python API, subtitle handling, resumable downloads, and media-player
streaming support. It is easy to try from the terminal and easy to automate
from Python.

Created and maintained by **Saksham Pathak**, also known as **parthmax** , this project focuses on being a polished educational Python
movie downloader CLI and API client.

```sh
pip install "movie-box-dl[cli]"
movie-box doctor
movie-box                        # launches the interactive UI
movie-box search "Avatar" --select
moviebox v3 download-movie "Avatar" --yes
```

## Features

* **Multi-Version Support** : Access multiple API versions (`v1`, `v2`, `v3`) for different provider services
* **Download Movies & TV Series** : High-quality downloads with multiple resolution options
* **Subtitle Support** : Download subtitles in multiple languages
* **Direct Streaming** : Stream via MPV or VLC without downloading (CLI only)
* **Faster Downloads** : Up to 5x faster than standard downloads
* **Async & Sync Support** : Fully asynchronous with synchronous fallback
* **Search & Discovery** : Find movies, trending content, and popular searches
* **Cyberpunk CLI UI** : Rich neon startup splash, PromptToolkit command shell, and optional Textual app
* **Developer-Friendly** : Python API with Pydantic models
* **Environment Checks** : Run `movie-box doctor` to verify Python, dependencies, and media players

## Installation

### CLI (for end users)

```sh
pip install "movie-box-dl[cli]"
```

### Base package (for developers)

```sh
pip install movie-box-dl
```

### Termux (Android)

```sh
pip install movie-box-dl --no-deps
pip install 'pydantic==2.9.2'
pip install rich click bs4 httpx throttlebuster
```

### Media Players (optional, required for streaming)

To stream content directly without downloading, install [MPV](https://mpv.io/installation) or [VLC](https://www.videolan.org):

<details>
<summary>Linux</summary>

```sh
# Ubuntu/Debian
sudo apt install mpv

# Fedora/RHEL
sudo dnf install mpv

# Arch Linux
sudo pacman -S mpv
```
</details>

<details>
<summary>macOS</summary>

```sh
brew install mpv
```
</details>

<details>
<summary>Windows</summary>

Download from [mpv.io/installation](https://mpv.io/installation/).
</details>

## Quick Start

### Command Line

```sh
# Check setup
movie-box doctor

# Launch the interactive cyberpunk shell (both commands are identical)
movie-box
moviebox

# Launch without the startup animation
movie-box ui --no-animation

# Open the full-screen Textual dashboard
movie-box app

# Search with a colorful table and optional selection prompt
movie-box search "Avatar" --select

# Download a movie
movie-box movie "Avatar"

# Download a TV series episode
movie-box series "Game of Thrones" -s 1 -e 1

# Stream a movie (requires MPV)
movie-box movie "Avatar" --stream-via mpv

# Stream with specific audio dub
movie-box series "Money Heist" --dub "English" --stream-via vlc

# Download Hindi audio without subtitles
movie-box movie "Narnia" --dub Hindi --no-caption --dir ./Movies/Narnia-Hindi

# Download subtitles/captions in a specific language
movie-box movie "Avatar" --caption --language en
```

### Python API

```python
from movie_box.v1 import MovieAuto
import asyncio

async def main():
    auto = MovieAuto()
    movie_file, subtitle_file = await auto.run("Avatar")
    print(f"Movie: {movie_file.saved_to}")
    print(f"Subtitle: {subtitle_file.saved_to}")

asyncio.run(main())
```

## Disclaimer

`movie-box` is provided for educational purposes only. Use it only with content
you are legally allowed to access, stream, inspect, or download. The project does
not host media files, does not bypass access controls, and is not affiliated with
or endorsed by MovieBox or any related provider. See [DISCLAIMER.md](DISCLAIMER.md).

## [Usage](https://moviebox.parthmax.in)

This is just a brief usage information. For more details visit official docs - [https://moviebox.parthmax.in](https://moviebox.parthmax.in)

<details open>
<summary><h3>Command Line Interface</h3></summary>

```sh
moviebox v2 --help
```

| Command | Description |
|-|-|
| `movie-box` / `moviebox` | Launch the interactive cyberpunk shell (no subcommand needed) |
| `movie-box search` | Search with colored results and optional numbered selection |
| `movie-box movie` | Search, select, download, or stream a movie |
| `movie-box series` | Search, select, download, or stream TV series episodes |
| `movie-box config` | Save defaults such as quality, language, and download directory |
| `movie-box ui` | Open the animated cyberpunk interactive shell (alias for the above) |
| `movie-box app` | Open the full-screen Textual dashboard |
| `movie-box doctor` | Check Python, dependencies, package imports, and media players |
| `download-movie` | Search, download, or stream movies, anime, music, and educational content |
| `download-series` | Search and download or stream TV series |
| `homepage-content` | Show contents displayed on the landing page |
| `item-details` | Show details of a particular movie or TV series |
| `mirror-hosts` | Discover available Moviebox mirror hosts |

#### Friendly CLI

The top-level commands use v3 internally and add a cleaner search table,
numbered selection, previews, a cyberpunk startup surface, and saved defaults:

```sh
# Open the interactive shell — typing movie-box or moviebox alone is enough
movie-box
moviebox

# You can also use the explicit subcommand; it is identical
movie-box ui

# Open instantly without the startup animation
movie-box ui --no-animation

# Open the full-screen Textual app
movie-box app

# Search only
movie-box search "Avatar"

# Search and choose from a colored numbered list
movie-box search "Avatar" --select

# Preview the selected movie without downloading
movie-box movie "Avatar" --dry-run

# Download after selecting from search results
movie-box movie "Avatar" -q 1080P -x English

# If you do not pass --quality or --dub, movie-box asks after selection.
# Press Enter on quality to keep the highest available option.
movie-box movie "Avatar"

# Download a Hindi dub/audio track; choose a Hindi result if the search shows one
movie-box movie "Narnia" --dub Hindi --no-caption --dir ./Movies/Narnia-Hindi

# Download captions/subtitles. The language must match a caption code or name
# returned by MovieBox, such as en, English, IN, Filipino, etc.
movie-box movie "Narnia" --caption --language IN

# Download one TV episode
movie-box series "Merlin" -s 1 -e 1

# Save defaults
movie-box config set quality 720P
movie-box config set language English Hindi
movie-box config set dir D:\Movies
movie-box config show
```

Config is stored in your user config directory. Set `MOVIEBOX_CONFIG_PATH` or
`MOVIEBOX_CONFIG_HOME` if you want to choose a custom location.

#### Audio dubs vs subtitle languages

`--dub` and `--language` control different things:

| Flag | What it selects | Example |
|-|-|-|
| `-u, --dub` | Audio dub track, such as Hindi audio | `movie-box movie "Narnia" --dub Hindi --no-caption` |
| `-x, --language` | Subtitle/caption file language | `movie-box movie "Narnia" --caption --language IN` |

The `Languages` column in search results is provider metadata and is not a
complete list of available audio dubs or caption files. For Hindi audio, prefer
passing `--dub Hindi` and selecting a result whose title includes `[Hindi]` when
one is listed. For subtitles, use the language name or code that MovieBox
returns for captions; if a caption is missing, the error message prints the
available choices, for example `en` or `IN`.

In the friendly `movie-box movie` command, leaving out `--dub` and `--quality`
opens numbered prompts after you select the search result. The quality prompt
defaults to the highest available file. Passing `--yes`, `--dub`, `--quality`,
or `--language` skips the matching prompt.

The interactive shell uses the same selection flow for movie downloads:
`/search <title>`, then `/download <number>` prompts for audio dub and quality
before downloading.

#### CLI Architecture

The premium terminal interface is split into reusable modules:

| Module | Purpose |
|-|-|
| `movie_box.tui.theme` | Central neon cyberpunk color system |
| `movie_box.tui.art` | Startup banner, ASCII typography, pyfiglet fallback, command deck |
| `movie_box.tui.splash` | Async Rich startup animation and glow simulation |
| `movie_box.tui.command_engine` | Slash-command registry and parser |
| `movie_box.tui.textual_app` | Optional full-screen Textual dashboard |

The CLI extra installs `Rich`, `PromptToolkit`, `pyfiglet`, and `Textual` so the
terminal experience can scale from normal command output to an interactive app.



#### Downloading Movies

**Basic usage:**
```sh
moviebox v2 download-movie "Avatar"
moviebox-v3 download-movie "avengers endgame" 
```

**Common options:**
```sh
moviebox v2 download-movie "Avatar" --quality 1080p
moviebox v2 download-movie "Avatar" --year 2009
moviebox v2 download-movie "Avatar" --dir ~/Movies
moviebox v2 download-movie "Avatar" --no-caption
moviebox v2 download-movie "Avatar" --yes
```

| Option | Description |
|-|-|
| `-y, --year` | Filter by release year |
| `-q, --quality` | Video quality: `best`, `1080p`, `720p`, `480p`, `360p`, `worst` |
| `-d, --dir` | Download directory |
| `-u, --dub` | Audio dub language/name or code (v3/friendly CLI) |
| `-x, --language` | Subtitle/caption language, not audio dub (default: English) |
| `--no-caption` | Skip subtitle download |
| `-Y, --yes` | Auto-confirm without prompts |

#### Downloading TV Series

**Basic usage:**
```sh
moviebox v2 download-series "Game of Thrones" -s 1 -e 1
moviebox-v3 download-series "A Knight of the Seven Kingdoms"
```

**Multiple episodes:**
```sh
# Download 5 episodes starting from S01E01
moviebox v2 download-series "Game of Thrones" -s 1 -e 1 -l 5

# Download entire season
moviebox v2 download-series "Game of Thrones" -s 1 -e 1 -l 100

# Download all remaining seasons
moviebox v2 download-series "Merlin" -s 1 -e 1 --auto-mode
```

| Option | Description |
|-|-|
| `-s, --season` | Season number (required) |
| `-e, --episode` | Starting episode number (required) |
| `-l, --limit` | Number of episodes to download (default: 1) |
| `-q, --quality` | Video quality |
| `-u, --dub` | Audio dub language/name or code (v3/friendly CLI) |
| `-x, --language` | Subtitle/caption language, not audio dub |
| `--no-caption` | Skip subtitles |
| `-Y, --yes` | Auto-confirm |
| `-A, --auto-mode` | Download all remaining seasons when `--limit` is 1 |

#### Streaming via Media Players

Stream content directly without downloading (requires MPV or VLC):

```sh
# Stream a movie
moviebox v2 download-movie "Avatar" --stream-via vlc

# Stream with subtitles in a specific language
moviebox v2 download-movie "Avatar" --stream-via mpv --language French

# Stream a series episode
moviebox v2 download-series "Game of Thrones" -s 1 -e 1 --stream-via vlc

# Stream with specific quality
moviebox v2 download-series "Breaking Bad" -s 1 -e 1 --stream-via vlc --quality 1080p
```

Streaming requires the `movie-box[cli]` installation and MPV or VLC installed on the system. Temporary files are cleaned up automatically.

### Command Shortcuts

```sh
# Full form
python -m movie_box v2 download-movie "Avatar"

# Short forms
movie-box v2 download-movie "Avatar"
moviebox-v2 download-movie "Avatar"
moviebox-v1 download-movie "Avatar"
```

### Episode Organization

**Group format** - episodes organized into season subfolders:

```sh
moviebox v2 download-series Merlin -s 1 -e 1 --auto-mode --format group
```

```
Merlin (2009)/
  S1/
    Merlin S1E1.mp4
    Merlin S1E2.mp4
  S2/
    Merlin S2E1.mp4
```

**Struct format** - hierarchical directory structure using episode numbers as filenames:

```sh
moviebox v2 download-series Merlin -s 1 -e 1 --auto-mode --format struct
```

```
Merlin (2009)/
  S1/
    E1.mp4
    E2.mp4
  S2/
    E1.mp4
```

</details>

<details>
<summary><h3>Python API</h3></summary>

#### Simple Auto-Download

```python
from movie_box.v1 import MovieAuto
import asyncio

async def main():
    auto = MovieAuto()
    movie_file, subtitle_file = await auto.run("Avatar")
    print(f"Movie saved to: {movie_file.saved_to}")
    print(f"Subtitle saved to: {subtitle_file.saved_to}")

asyncio.run(main())
```

#### Download with Progress Tracking

```python
from movie_box.v1 import DownloadTracker, MovieAuto
import asyncio

async def progress_callback(progress: DownloadTracker):
    percent = (progress.downloaded_size / progress.expected_size) * 100
    print(f"[{percent:.2f}%] Downloading {progress.saved_to.name}", end="\r")

async def main():
    auto = MovieAuto(tasks=1)
    await auto.run("Avatar", progress_hook=progress_callback)

asyncio.run(main())
```

#### Download with Manual Confirmation

```python
from movie_box.v1.cli import Downloader
import asyncio

async def main():
    downloader = Downloader()
    movie_file, subtitle_files = await downloader.download_movie("Avatar")
    print(f"Downloaded: {movie_file}")
    print(f"Subtitles: {subtitle_files}")

asyncio.run(main())
```

#### Download TV Series Episodes

```python
from movie_box.v1.cli import Downloader
import asyncio

async def main():
    downloader = Downloader()
    episodes_map = await downloader.download_tv_series(
        "Merlin",
        season=1,
        episode=1,
        limit=2,
        # auto_mode=True  # Download entire remaining seasons when limit=1
    )
    print(f"Downloaded episodes: {episodes_map}")

asyncio.run(main())
```

#### Custom Configuration

```python
from movie_box.v1 import MovieAuto
import asyncio

async def main():
    auto = MovieAuto(
        caption_language="Spanish",
        quality="720p",
        download_dir="~/Downloads"
    )
    movie_file, subtitle_file = await auto.run("Avatar")

asyncio.run(main())
```

#### Further Examples

- [V1 Examples](./docs/v1/examples/)
- [v2 Examples](./docs/v2/examples/)

</details>

## Mirror Hosts

h5.aoneroom.com has ~~[multiple mirror hosts](https://github.com/parthmax2/movie-box/issues/27)~~. To use a specific mirror:

```sh
# v1
export MOVIEBOX_API_HOST="h5.aoneroom.com"

# v2
export MOVIEBOX_API_HOST_V2="h5-api.aoneroom.com"
```

Discover available mirrors:

```sh
moviebox v1 mirror-hosts
```

## Alternatives

1. Movies - [fzmovies-api](https://github.com/parthmax2/fzmovies-api)
2. TV-Series - [fzseries-api](https://github.com/parthmax2/fzseries-api)

## Maintainer

This project is maintained by **Saksham Pathak**, also known as
**parthmax** / **parthmax2** on GitHub.

## Contributors

<div align="center">

<a href="https://github.com/parthmax2/movie-box/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=parthmax2/movie-box" />
</a>

</div>


<h2 align="center"> Disclaimer </h2>

`movie-box` is for educational purposes only. Use it only where you have the
legal right to access or download content. The project does not host media files
and is not affiliated with MovieBox or any related provider.

<div align=center>

**Long live Moviebox spirit.**
</div>

<div align="center">Made with ❤️ </div>
