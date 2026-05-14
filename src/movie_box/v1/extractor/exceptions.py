from movie_box.v1._bases import BaseMovieboxException


class DetailsExtractionError(BaseMovieboxException):
    """Raised when trying to extract data from html page without success"""
