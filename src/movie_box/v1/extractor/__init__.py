"""Extracts data from specific movie/tv-series page"""

from movie_box.v1.extractor._core import (
    JsonDetailsExtractor,
    JsonDetailsExtractorModel,
    TagDetailsExtractor,
    TagDetailsExtractorModel,
)
from movie_box.v1.extractor.exceptions import DetailsExtractionError

__all__ = [
    "TagDetailsExtractor",
    "JsonDetailsExtractor",
    "TagDetailsExtractorModel",
    "JsonDetailsExtractorModel",
    "DetailsExtractionError",
]
