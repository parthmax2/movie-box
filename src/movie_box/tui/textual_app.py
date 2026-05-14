from __future__ import annotations


def launch_textual_app() -> None:
    try:
        from textual.app import App, ComposeResult
        from textual.containers import Container, Vertical
        from textual.widgets import Footer, Header, Static
    except ImportError as exc:
        raise RuntimeError(
            "Textual is not installed. Install with: pip install \"movie-box[cli]\""
        ) from exc

    from movie_box.tui.art import package_version

    class MovieBoxApp(App):
        CSS = """
        Screen {
            background: #000000;
            color: #f5f3ff;
        }

        Header, Footer {
            background: #09090b;
            color: #d946ef;
        }

        #shell {
            height: 100%;
            padding: 2 4;
            border: tall #8b5cf6;
            background: #050507;
        }

        #badge {
            width: auto;
            padding: 0 2;
            margin-bottom: 2;
            border: round #575268;
            background: #18181b;
            color: #f5f3ff;
        }

        #title {
            color: #d946ef;
            text-style: bold;
            margin-bottom: 1;
        }

        #credit {
            color: #c084fc;
            margin-bottom: 2;
        }

        .command {
            color: #f5f3ff;
            margin: 0 0 1 0;
        }
        """

        BINDINGS = [("q", "quit", "Quit"), ("escape", "quit", "Quit")]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Container(id="shell"):
                with Vertical():
                    yield Static("*  Welcome to MOVIE-BOX CLI", id="badge")
                    yield Static(
                        "\n".join(
                            (
                                "##   ##  ####  ##   ##  ####  #######",
                                "### ### ##  ## ##   ##   ##   ##",
                                "####### ##  ## ##   ##   ##   #####",
                                "## # ## ##  ##  ## ##    ##   ##",
                                "##   ##  ####    ###    ####  #######",
                            )
                        ),
                        id="title",
                    )
                    yield Static(
                        f"v{package_version()}  developed by parthmax",
                        id="credit",
                    )
                    yield Static("/search   find movies and series", classes="command")
                    yield Static("/movie    preview movie matches", classes="command")
                    yield Static("/series   preview TV series matches", classes="command")
                    yield Static("/config   show saved defaults", classes="command")
                    yield Static("/doctor   check environment", classes="command")
            yield Footer()

    MovieBoxApp().run()

