# Interactive Shell UI

movie-box ships a cyberpunk interactive shell that lets you search, browse, and
download content without memorizing long command-line flags.

---

## Launching the shell

Typing `movie-box` or `moviebox` with no subcommand goes straight into the
shell. Both commands are identical.

```sh
movie-box
moviebox
```

You can also use the explicit subcommand — it behaves the same way:

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
| `/download` | `/download <number>` | Download the chosen movie result from the last `/search` |
| `/config` | `/config` | Show your saved CLI defaults (quality, directory, language, etc.) |
| `/doctor` | `/doctor` | Reminder to run `movie-box doctor` for a full environment check |
| `/clear` | `/clear` | Clear the terminal and redisplay the compact header |
| `/exit` | `/exit` | Close the shell |

### Shorthand

You can omit the leading `/` — the shell treats bare words as search queries:

```
Avatar                 → same as /search Avatar
/search Inception      → explicit form
```

You can also type a result number directly after a `/search` to preview it:

```
/search Avatar
2                      → same as /select 2
```

---

## Autocomplete

The shell uses [PromptToolkit](https://python-prompt-toolkit.readthedocs.io/)
when it is installed (included in `movie-box[cli]`). Start typing `/` and press
`Tab` to cycle through available commands.

---

## Typical workflow

```
movie-box                   # enter the shell

/search Inception           # search for a title
3                           # preview result #3
/download 3                 # download that movie

/series Breaking Bad        # preview a TV series match
                            # use movie-box series on the CLI for episode downloads

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

The shell reads these defaults automatically when you run `/download`.

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
