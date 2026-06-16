# Generates the hero GIF for README.md.
#
# Install VHS first: https://github.com/charmbracelet/vhs#installation
#   winget install charmbracelet.vhs   (Windows)
#   brew install vhs                   (macOS)
#
# Then, with movie-box-dl[cli] installed in this shell:
#   vhs assets/demo.tape
#
# This drives the real `movie-box` quick flow against the live API, so the
# Sleep durations below are starting points, not guarantees — record once,
# watch the output, and nudge timings to match how fast results actually
# come back on your connection. Re-run until a take looks clean.

Output assets/demo.gif

Set Shell bash
Set FontFamily "JetBrains Mono"
Set FontSize 20
Set Width 1200
Set Height 650
Set Padding 24
Set BorderRadius 10
Set TypingSpeed 70ms
Set Framerate 24

# Cyberpunk neon palette, matched to src/movie_box/tui/theme.py.
Set Theme {
  "name": "movie-box",
  "black": "#000000",
  "red": "#fb7185",
  "green": "#22c55e",
  "yellow": "#facc15",
  "blue": "#38bdf8",
  "purple": "#d946ef",
  "cyan": "#c084fc",
  "white": "#f5f3ff",
  "brightBlack": "#575268",
  "brightRed": "#fb7185",
  "brightGreen": "#22c55e",
  "brightYellow": "#facc15",
  "brightBlue": "#38bdf8",
  "brightPurple": "#ff7aff",
  "brightCyan": "#8b5cf6",
  "brightWhite": "#ffffff",
  "background": "#000000",
  "foreground": "#f5f3ff",
  "cursor": "#ff7aff",
  "selection": "#8b5cf6"
}

Hide
Type "clear"
Enter
Sleep 500ms
Show

# Beat 1: the install, so the GIF proves the one-liner is real.
Type `pip install "movie-box-dl[cli]"`
Sleep 1s
Enter
Sleep 2s
Type "clear"
Enter
Sleep 500ms

# Beat 2: search straight from the prompt.
Type `movie-box "Inception"`
Sleep 800ms
Enter
Sleep 5s

# Beat 3: accept the top search result.
Enter
Sleep 2s

# Beat 4: accept the default audio dub.
Enter
Sleep 2s

# Beat 5: accept the default (best) quality.
Enter
Sleep 2s

# Beat 6: choose "Stream" instead of "Download" — this is the moment
# the GIF exists to sell, so let it breathe a little longer.
Type "2"
Sleep 400ms
Enter
Sleep 1500ms

# Beat 7: confirm and let it open in the browser.
Enter
Sleep 4s
