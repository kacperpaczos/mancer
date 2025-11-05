"""
Text renderers for converting polars DataFrames to text format for command pipelines.
"""

from abc import ABC, abstractmethod
from typing import Optional

import polars as pl


class TextRenderer(ABC):
    """Abstract base class for text renderers."""

    @abstractmethod
    def render(self, df: pl.DataFrame) -> str:
        """Render DataFrame to text format."""
        pass


class RawLineRenderer(TextRenderer):
    """Renderer that uses 'raw_line' column to reconstruct original output."""

    def render(self, df: pl.DataFrame) -> str:
        """Render using raw_line column."""
        if "raw_line" in df.columns and len(df) > 0:
            return "\n".join(df["raw_line"].to_list())
        return ""


class CsvRenderer(TextRenderer):
    """Renderer that outputs DataFrame as CSV."""

    def __init__(self, separator: str = "\t"):
        self.separator = separator

    def render(self, df: pl.DataFrame) -> str:
        """Render DataFrame as CSV."""
        if len(df) == 0:
            return ""
        return df.write_csv(separator=self.separator, include_header=True)


class LineRenderer(TextRenderer):
    """Renderer that outputs each row as a single line using specified column."""

    def __init__(self, column: str = "line"):
        self.column = column

    def render(self, df: pl.DataFrame) -> str:
        """Render using specified column."""
        if self.column in df.columns and len(df) > 0:
            return "\n".join(df[self.column].to_list())
        return ""


class TextRendererFactory:
    """Factory for creating text renderers."""

    _renderers = {
        "raw_line": RawLineRenderer(),
        "csv": CsvRenderer(),
        "tsv": CsvRenderer(separator="\t"),
        "line": LineRenderer(),
        "text": LineRenderer("text"),
    }

    @classmethod
    def get_renderer(cls, name: Optional[str] = None) -> TextRenderer:
        """Get renderer by name."""
        if name is None or name not in cls._renderers:
            # Default to raw_line if available, otherwise line
            return RawLineRenderer()
        return cls._renderers[name]

    @classmethod
    def register_renderer(cls, name: str, renderer: TextRenderer) -> None:
        """Register a custom renderer."""
        cls._renderers[name] = renderer
