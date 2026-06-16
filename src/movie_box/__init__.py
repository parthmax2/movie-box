from importlib import metadata

from movie_box import _compat as _compat  # noqa: F401

try:
    __version__ = metadata.version("movie-box-dl")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Smartwa"
__repo__ = "https://github.com/parthmax2/movie-box"
