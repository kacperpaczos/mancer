from enum import Enum, auto
from typing import Optional


class DataFormat(Enum):
    """Data formats for CommandResult.structured_output.

    - POLARS: polars.DataFrame (canonical format)
    - JSON: JSON string
    - TABLE: Tabular format used by commands like df/ps
    """

    POLARS = auto()
    JSON = auto()
    TABLE = auto()

    @staticmethod
    def from_string(format_name: str) -> Optional["DataFormat"]:
        """Convert a string name to a DataFormat enum value."""
        format_map = {
            "polars": DataFormat.POLARS,
            "json": DataFormat.JSON,
            "table": DataFormat.TABLE,
        }

        if format_name.lower() not in format_map:
            return None

        return format_map[format_name.lower()]

    @staticmethod
    def to_string(format_type: "DataFormat") -> str:
        """Convert a DataFormat enum value to its string name."""
        format_map = {
            DataFormat.POLARS: "polars",
            DataFormat.JSON: "json",
            DataFormat.TABLE: "table",
        }

        return format_map.get(format_type, "polars")

    @staticmethod
    def is_convertible(source_format: "DataFormat", target_format: "DataFormat") -> bool:
        """Return True if conversion between formats is possible."""
        # Wszystkie formaty są konwertowalne między sobą
        return True
