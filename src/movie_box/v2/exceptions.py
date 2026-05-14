"""v2 Exceptions"""

from movie_box.v1.exceptions import (
    ExhaustedSearchResultsError,
    MovieboxApiException,
)


class InvalidDetailPathError(MovieboxApiException): ...
