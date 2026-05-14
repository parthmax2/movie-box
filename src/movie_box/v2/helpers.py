"""V2 Helpers"""

import re

import movie_box.v1.helpers
from movie_box.v2.constants import HOST_URL

VALID_DETAIL_PATH_PATTERN = re.compile(r"^[\w-]+-\w{9,13}$")


def get_absolute_url(relative_url: str, base_url: str = HOST_URL):

    return movie_box.v1.helpers.get_absolute_url(relative_url, base_url)


def validate_detail_path(path: str) -> bool:
    return VALID_DETAIL_PATH_PATTERN.match(path) is not None
