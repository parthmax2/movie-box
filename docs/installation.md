## Installing from PyPI

The PyPI package name is **`movie-box-dl`**. The CLI commands after install are `movie-box` and `moviebox`.

We shall be using [uv tool](https://docs.astral.sh/uv/)

### With required dependencies

=== "Install"

    ```sh
    uv pip install movie-box-dl
    ```

=== "Add to project"

    ```sh
    uv add movie-box-dl
    ```
### With [commandline](./v1/cli.md) extra dependencies

=== "Install"

    ```sh
    uv pip install "movie-box-dl[cli]"
    ```

=== "Add to project"

    ```sh
    uv add "movie-box-dl[cli]"
    ```

!!! important "CLI utils"
    At some point, developers may want to make use of CLI utility functions for operations such as prompting users to choose the movie quality to be processed, etc. This will require the commandline extra dependencies to be installed.

## Installing from source

If you like new features before official releases:

=== "Install"

    ```sh
    uv pip install "git+https://github.com/parthmax2/movie-box.git[cli]"
    ```

=== "Add to project"

    ```sh
    uv add "git+https://github.com/parthmax2/movie-box.git[cli]"
    ```

???+ warning "Git required"
    For this method to work you need to have [git tool](https://git-scm.com) installed.


## Termux Installation (Android)

```sh
pip install movie-box-dl --no-deps
pip install 'pydantic==2.9.2'
pip install rich click bs4 httpx throttlebuster
```
