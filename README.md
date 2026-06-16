<div align="center">

# movie-box

![movie-box CLI](assets/cli.png)

### Be kind. Rewind.
### Or just `pip install` and skip all that.

Search, pick a quality, hit play — it streams straight to your browser,
no VLC, no MPV, no membership card required.

[![PyPI version](https://badge.fury.io/py/movie-box-dl.svg)](https://pypi.org/project/movie-box-dl)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/movie-box-dl)](https://pypi.org/project/movie-box-dl)
![Coverage](https://raw.githubusercontent.com/parthmax2/movie-box/refs/heads/main/assets/coverage.svg)
[![PyPI - License](https://img.shields.io/pypi/l/movie-box-dl)](https://pypi.org/project/movie-box-dl)
[![Downloads](https://pepy.tech/badge/movie-box-dl)](https://pepy.tech/project/movie-box-dl)
[![CI](https://github.com/parthmax2/movie-box/actions/workflows/ci.yml/badge.svg)](https://github.com/parthmax2/movie-box/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[Install](#install) · [Quickstart](#quickstart) · [Python API](#python-api) · [Full Docs](https://moviebox.parthmax.in) · [Disclaimer](#disclaimer)

</div>

---

Every video store on the planet closed. Somehow this one just relocated
into a terminal — no rewind fee, no "be a member to rent that," no guy at
the counter judging your choices. `movie-box` is a CLI and async Python
API that searches, downloads, and streams movies and TV with subtitles,
multiple dubs, and resumable transfers, built for people who'd rather type
a title than click through five ad-walled redirects to find one.

<div align="center">
  <img src="assets/moviebox.gif" width="80%" alt="Movie Box ">
</div>

## Install

```sh
pip install "movie-box-dl[cli]"   # the full terminal experience
pip install movie-box-dl          # just the Python API, no extras
```

## Quickstart

```sh
movie-box doctor        # make sure your setup is good to go
movie-box "Avatar"      # search, pick, and download — or stream right there
movie-box shell         # the slash-command shell, for when you live in the terminal
```

That's the whole onboarding. Pick a result, pick a quality, pick **stream**
instead of **download** if you just want it playing — it opens in your
browser, no extra software to install. Everything else — TV series, dubs,
config defaults, the full-screen dashboard, Python API reference — lives
in the [docs](https://moviebox.parthmax.in) so this page doesn't have to.

<details>
<summary><b>A few more commands worth knowing</b></summary>

```sh
movie-box search "Avatar" --select        # search without committing to a download
movie-box movie "Avatar" --dub Hindi      # pick a specific audio dub
movie-box series "Merlin" -s 1 -e 1       # grab a TV episode
movie-box config set quality 1080P        # stop typing the same flags every time
movie-box app                             # the full-screen Textual dashboard
```

</details>

## Python API

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

More API examples (progress tracking, manual confirmation, TV series,
custom config) are in the [docs](https://moviebox.parthmax.in).

## Why not just use a browser?

Because the browser is where the ads, the fake "Download" buttons, and the
six redirect pages live. `movie-box` does the part you actually wanted —
search, pick, watch — in the time it takes those pages to load their first
pop-up.


## Disclaimer

`movie-box` is for educational purposes only. Use it only where you have
the legal right to access or download content. The project does not host
media files, does not bypass access controls, and is not affiliated with
or endorsed by MovieBox or any related provider. See [DISCLAIMER.md](DISCLAIMER.md).

## Maintainer

Built and maintained by **Saksham Pathak** ([parthmax](https://github.com/parthmax2)).

<div align="center">

<a href="https://github.com/parthmax2/movie-box/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=parthmax2/movie-box" />
</a>

**Long live the Moviebox spirit.**

</div>
