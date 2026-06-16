# Interactive CLI UI

movie-box ships a guided download flow and a cyberpunk interactive shell that
let you search, browse, and download content without memorizing long
command-line flags.

---

## Guided default flow

Typing `movie-box` or `moviebox` with no subcommand opens the guided download
flow. It asks for the title, detects movie vs series when it can, then asks only
for the details needed to start downloading.

```sh
movie-box
moviebox
```

You can also pass the search query directly:

```sh
movie-box "Avatar"
moviebox titans
```

Typical movie prompts:

```text
Search: Avatar
Detected: Movie
Audio language [1]:
Quality [best]:
Download summary
Download? [Y/n]:
```

For a series it also asks for season, episode, and episode count before quality.

```text
Search: Merlin
Detected: Series
Audio language [1]:
Available seasons
Season [1]:
Episode [1]:
Episodes [1]:
Quality [best]:
Download summary
Download? [Y/n]:
```

---

## Launching the shell

The older slash-command shell is still available explicitly.

```sh
movie-box shell
moviebox shell
```

You can also use the original subcommand:

```sh
movie-box ui
```

### Skip the startup animation

```sh
movie-box ui --no-animation
```

### Full-screen Textual dashboard

For a full-screen terminal UI (requires the `[cli]` extra):

```sh
movie-box app
```

Press `q` or `Escape` to exit the Textual app.

---

## Shell commands

Once inside the shell you control everything with slash commands.
Type `/help` at any time to print the command deck.

| Command | Usage | Description |
|---------|-------|-------------|
| `/help` | `/help` | Show the command deck |
| `/search` | `/search <title>` | Search across all content types and display a numbered results table |
| `/movie` | `/movie <title>` | Search movies and preview the top match |
| `/series` | `/series <title>` | Search TV series and preview the top match |
| `/select` | `/select <number>` | Preview a result from the last `/search` by its table number |
| `/download` | `/download <number>` | Download the chosen movie result from the last `/search`; prompts for audio dub and quality |
| `/config` | `/config` | Show your saved CLI defaults |
| `/doctor` | `/doctor` | Reminder to run `movie-box doctor` |
| `/clear` | `/clear` | Clear the terminal and redisplay the compact header |
| `/exit` | `/exit` | Close the shell |

### Shorthand

You can omit the leading `/`; the shell treats bare words as search queries:

```text
Avatar                 -> same as /search Avatar
/search Inception      -> explicit form
```

You can also type a result number directly after a `/search` to preview it:

```text
/search Avatar
2                      -> same as /select 2
```

---

## Typical shell workflow

```text
movie-box shell             # enter the shell

/search Inception           # search for a title
3                           # preview result #3
/download 3                 # choose dub, choose quality, then download

/series Breaking Bad        # preview a TV series match
                            # use movie-box series for episode downloads

/config                     # check saved defaults
/exit                       # leave the shell
```

---

## Saved defaults

Settings such as download directory, quality, and subtitle language are
persisted between sessions. Manage them with `movie-box config`:

```sh
movie-box config set quality 720P
movie-box config set language English Hindi
movie-box config set dir ~/Movies
movie-box config show
movie-box config reset
```

The guided flow and shell read these defaults automatically. During download the
saved `dub` and `quality` values become preferred selections when available.

Config is stored under your system's user config directory. Override the
location with environment variables:

| Variable | Effect |
|----------|--------|
| `MOVIEBOX_CONFIG_PATH` | Full path to the config file |
| `MOVIEBOX_CONFIG_HOME` | Directory that contains `config.json` |

---

## Requirements

The interactive shell requires the `[cli]` extra:

```sh
pip install "movie-box-dl[cli]"
```

This installs `Rich`, `PromptToolkit`, `pyfiglet`, and `Textual` alongside the
base package.
