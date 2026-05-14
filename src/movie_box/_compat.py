import enum
from enum import Enum

try:
    from enum import StrEnum
except ImportError:

    class StrEnum(str, Enum):
        """Python 3.10-compatible fallback for enum.StrEnum."""

        def __str__(self) -> str:
            return str.__str__(self)

        def __format__(self, format_spec: str) -> str:
            return str.__format__(self, format_spec)

        @staticmethod
        def _generate_next_value_(
            name: str, start: int, count: int, last_values: list[str]
        ) -> str:
            return name.lower()

    enum.StrEnum = StrEnum
