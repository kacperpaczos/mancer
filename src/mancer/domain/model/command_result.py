from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_serializer, field_validator

from ..service.data_converter_service import DataFormatConverter
from ..service.text_renderer import TextRendererFactory
from .data_format import DataFormat
from .execution_history import ExecutionHistory


class CommandResult(BaseModel):
    """Represents the result of a command execution.

    Attributes:
        raw_output: Raw stdout/stderr captured as a single string.
        success: True if the command succeeded (exit_code==0 by convention).
        structured_output: Structured representation (typically a polars.DataFrame).
        exit_code: Process exit code.
        error_message: Optional error message if available.
        metadata: Optional metadata associated with execution.
        data_format: Declared data format of structured_output.
        history: Execution history with steps and metadata.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    raw_output: str
    success: bool
    structured_output: Union[pl.DataFrame, Any]
    exit_code: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data_format: DataFormat = DataFormat.POLARS
    history: ExecutionHistory = Field(default_factory=ExecutionHistory)
    command_name: Optional[str] = None  # Optional field for logging purposes

    @field_serializer("structured_output")
    def serialize_structured_output(self, value: Any, _info) -> Any:
        """Serialize structured_output for JSON/dict serialization."""
        if isinstance(value, pl.DataFrame):
            # Convert DataFrame to list of dicts for serialization
            if len(value) > 0:
                return value.to_dicts()
            else:
                return []
        return value

    @field_validator("structured_output", mode="before")
    @classmethod
    def validate_structured_output(cls, value: Any, info: ValidationInfo) -> Any:
        """Convert list of dicts back to DataFrame if data_format is POLARS."""
        # Only convert if we're in POLARS format context
        # Check if data_format is POLARS (from info.data if available)
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            # Check if we should convert to DataFrame
            # This happens during deserialization when data_format is POLARS
            data = info.data if hasattr(info, "data") and info.data else {}
            data_format = data.get("data_format", DataFormat.POLARS)
            if data_format == DataFormat.POLARS:
                return pl.DataFrame(value)
        return value

    def __str__(self) -> str:
        return self.raw_output

    def is_success(self) -> bool:
        return self.success

    def get_structured(self) -> Union[pl.DataFrame, Any]:
        """Return the structured_output as-is."""
        return self.structured_output

    def get_format(self) -> DataFormat:
        """Return the current data format of structured_output."""
        return self.data_format

    def get_history(self) -> ExecutionHistory:
        """Return the execution history for this result."""
        return self.history

    def as_polars(self) -> pl.DataFrame:
        """Return structured_output as a polars.DataFrame."""
        if isinstance(self.structured_output, pl.DataFrame):
            return self.structured_output
        else:
            # If not already a DataFrame, try to convert
            return pl.DataFrame(self.structured_output)

    def update_from_df(self, df: pl.DataFrame, renderer: Optional[str] = None) -> "CommandResult":
        """Update structured_output and raw_output from a polars.DataFrame."""
        self.structured_output = df
        self.data_format = DataFormat.POLARS

        # Update raw_output using renderer
        text_renderer = TextRendererFactory.get_renderer(renderer)
        self.raw_output = text_renderer.render(df)

        return self

    # Fluent DataFrame transformation methods
    def filter(self, predicate: Any, renderer: Optional[str] = None) -> "CommandResult":
        """Filter DataFrame rows. Returns new CommandResult."""
        df = self.as_polars().filter(predicate)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def select(self, columns: Any, renderer: Optional[str] = None) -> "CommandResult":
        """Select columns from DataFrame. Returns new CommandResult."""
        df = self.as_polars().select(columns)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def sort(self, by: Any, descending: bool = False, renderer: Optional[str] = None) -> "CommandResult":
        """Sort DataFrame. Returns new CommandResult."""
        df = self.as_polars().sort(by, descending=descending)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def head(self, n: int = 5, renderer: Optional[str] = None) -> "CommandResult":
        """Take first n rows. Returns new CommandResult."""
        df = self.as_polars().head(n)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def tail(self, n: int = 5, renderer: Optional[str] = None) -> "CommandResult":
        """Take last n rows. Returns new CommandResult."""
        df = self.as_polars().tail(n)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def group_by(self, by: Any, agg: Any = None, renderer: Optional[str] = None) -> "CommandResult":
        """Group DataFrame and optionally aggregate. Returns new CommandResult."""
        df = self.as_polars()
        if agg is not None:
            df = df.group_by(by).agg(agg)
        else:
            df = df.group_by(by)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def transform(
        self, func: Callable[[pl.DataFrame], pl.DataFrame], renderer: Optional[str] = None
    ) -> "CommandResult":
        """Apply custom transformation function. Returns new CommandResult."""
        df = func(self.as_polars())
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Advanced column selection methods
    def select_columns(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandResult":
        """Select columns by name(s). Returns new CommandResult."""
        df = self.as_polars()
        if isinstance(columns, str):
            df = df.select(columns)
        else:
            df = df.select(columns)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def drop_columns(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandResult":
        """Drop columns by name(s). Returns new CommandResult."""
        df = self.as_polars()
        df = df.drop(columns)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def rename_columns(self, mapping: Dict[str, str], renderer: Optional[str] = None) -> "CommandResult":
        """Rename columns using a mapping dict. Returns new CommandResult."""
        df = self.as_polars()
        df = df.rename(mapping)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Advanced row selection methods
    def filter_by_value(self, column: str, value: Any, renderer: Optional[str] = None) -> "CommandResult":
        """Filter rows where column equals specific value. Returns new CommandResult."""
        df = self.as_polars()
        df = df.filter(pl.col(column) == value)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def filter_not_value(self, column: str, value: Any, renderer: Optional[str] = None) -> "CommandResult":
        """Filter rows where column does NOT equal specific value. Returns new CommandResult."""
        df = self.as_polars()
        df = df.filter(pl.col(column) != value)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def filter_even_rows(self, renderer: Optional[str] = None) -> "CommandResult":
        """Filter to even-indexed rows (0, 2, 4, ...). Returns new CommandResult."""
        df = self.as_polars()
        # Even indices (0-based) - create row numbers and filter
        df_with_idx = df.with_row_index("__idx")
        df = df_with_idx.filter(pl.col("__idx") % 2 == 0).drop("__idx")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def filter_odd_rows(self, renderer: Optional[str] = None) -> "CommandResult":
        """Filter to odd-indexed rows (1, 3, 5, ...). Returns new CommandResult."""
        df = self.as_polars()
        # Odd indices (0-based) - create row numbers and filter
        df_with_idx = df.with_row_index("__idx")
        df = df_with_idx.filter(pl.col("__idx") % 2 == 1).drop("__idx")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def filter_every_nth(self, n: int, offset: int = 0, renderer: Optional[str] = None) -> "CommandResult":
        """Filter to every Nth row starting from offset. Returns new CommandResult."""
        df = self.as_polars()
        df_with_idx = df.with_row_index("__idx")
        df = df_with_idx.filter((pl.col("__idx") - offset) % n == 0).drop("__idx")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def where(self, condition: Any, renderer: Optional[str] = None) -> "CommandResult":
        """Filter rows using a boolean condition expression. Returns new CommandResult."""
        df = self.as_polars()
        df = df.filter(condition)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def sample(self, n: int, with_replacement: bool = False, renderer: Optional[str] = None) -> "CommandResult":
        """Take a random sample of n rows. Returns new CommandResult."""
        df = self.as_polars()
        df = df.sample(n, with_replacement=with_replacement)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Row extraction and manipulation methods
    def get_row(self, index: int, renderer: Optional[str] = None) -> dict:
        """Get a single row by index as dictionary."""
        df = self.as_polars()
        if index >= len(df) or index < 0:
            raise IndexError(f"Row index {index} out of bounds for DataFrame with {len(df)} rows")
        return df.row(index, named=True)

    def get_rows(self, indices: List[int], renderer: Optional[str] = None) -> "CommandResult":
        """Get multiple rows by indices. Returns new CommandResult."""
        df = self.as_polars()
        try:
            selected_rows = df[indices]
        except IndexError as e:
            raise IndexError(f"Invalid row indices: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=selected_rows,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(selected_rows, renderer)

    def get_headers(self) -> List[str]:
        """Get column headers/names."""
        return self.as_polars().columns

    def get_column_names(self) -> List[str]:
        """Alias for get_headers()."""
        return self.get_headers()

    def get_shape(self) -> tuple:
        """Get DataFrame shape (rows, columns)."""
        df = self.as_polars()
        return (len(df), len(df.columns))

    # Data cleaning and manipulation methods
    def drop_duplicates(self, subset: Optional[List[str]] = None, renderer: Optional[str] = None) -> "CommandResult":
        """Drop duplicate rows. Optionally specify columns to consider. Returns new CommandResult."""
        df = self.as_polars()
        if subset is None:
            df = df.unique()
        else:
            df = df.unique(subset=subset)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def fill_nulls(
        self, value: Any, columns: Optional[List[str]] = None, renderer: Optional[str] = None
    ) -> "CommandResult":
        """Fill null values with specified value. Optionally specify columns. Returns new CommandResult."""
        df = self.as_polars()
        if columns is None:
            df = df.fill_null(value)
        else:
            for col in columns:
                if col in df.columns:
                    df = df.with_columns(pl.col(col).fill_null(value))
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def drop_nulls(self, subset: Optional[List[str]] = None, renderer: Optional[str] = None) -> "CommandResult":
        """Drop rows with null values. Optionally specify columns to check. Returns new CommandResult."""
        df = self.as_polars()
        if subset is None:
            df = df.drop_nulls()
        else:
            df = df.drop_nulls(subset=subset)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Statistical and aggregation methods
    def describe(self, percentiles: Optional[List[float]] = None, renderer: Optional[str] = None) -> "CommandResult":
        """Generate descriptive statistics. Returns new CommandResult with stats."""
        df = self.as_polars()
        if percentiles is None:
            percentiles = [0.25, 0.5, 0.75]

        # Get numeric columns
        numeric_cols = [col for col in df.columns if df[col].dtype in [pl.Float64, pl.Int64]]

        if not numeric_cols:
            # Return empty DataFrame if no numeric columns
            stats_df = pl.DataFrame()
        else:
            stats_df = df.select(numeric_cols).describe(percentiles=percentiles)

        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=stats_df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(stats_df, renderer)

    def value_counts(self, column: str, sort: bool = True, renderer: Optional[str] = None) -> "CommandResult":
        """Get value counts for a column. Returns new CommandResult."""
        df = self.as_polars()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")

        value_counts = (
            df.group_by(column).agg(pl.count().alias("count")).sort("count", descending=True)
            if sort
            else pl.DataFrame()
        )

        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=value_counts,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(value_counts, renderer)

    # String operations
    def str_upper(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandResult":
        """Convert string columns to uppercase. Returns new CommandResult."""
        df = self.as_polars()
        if isinstance(columns, str):
            columns = [columns]

        for col in columns:
            if col in df.columns and df[col].dtype == pl.Utf8:
                df = df.with_columns(pl.col(col).str.to_uppercase().alias(col))

        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def str_lower(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandResult":
        """Convert string columns to lowercase. Returns new CommandResult."""
        df = self.as_polars()
        if isinstance(columns, str):
            columns = [columns]

        for col in columns:
            if col in df.columns and df[col].dtype == pl.Utf8:
                df = df.with_columns(pl.col(col).str.to_lowercase().alias(col))

        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def str_contains(
        self, column: str, pattern: str, new_column: str, renderer: Optional[str] = None
    ) -> "CommandResult":
        """Check if string column contains pattern. Returns new CommandResult."""
        df = self.as_polars()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")

        df = df.with_columns(pl.col(column).str.contains(pattern).alias(new_column))

        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Mathematical operations with error validation
    def add_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandResult":
        """Add two columns with error validation. Returns new CommandResult."""
        df = self.as_polars()
        try:
            # Convert to numeric, invalid values become null
            df = df.with_columns(
                [
                    pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                    pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                ]
            )
            # Add with null handling
            df = df.with_columns((pl.col(f"__{col1}_num") + pl.col(f"__{col2}_num")).alias(new_col)).drop(
                [f"__{col1}_num", f"__{col2}_num"]
            )
        except Exception as e:
            raise ValueError(f"Addition failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def divide_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandResult":
        """Divide two columns with error validation. Returns new CommandResult."""
        df = self.as_polars()
        try:
            df = df.with_columns(
                [
                    pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                    pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                ]
            )
            # Safe division: handle division by zero
            df = df.with_columns(
                pl.when(pl.col(f"__{col2}_num") != 0)
                .then(pl.col(f"__{col1}_num") / pl.col(f"__{col2}_num"))
                .otherwise(None)
                .alias(new_col)
            ).drop([f"__{col1}_num", f"__{col2}_num"])
        except Exception as e:
            raise ValueError(f"Division failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def multiply_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandResult":
        """Multiply two columns with error validation. Returns new CommandResult."""
        df = self.as_polars()
        try:
            df = df.with_columns(
                [
                    pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                    pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                ]
            )
            df = df.with_columns((pl.col(f"__{col1}_num") * pl.col(f"__{col2}_num")).alias(new_col)).drop(
                [f"__{col1}_num", f"__{col2}_num"]
            )
        except Exception as e:
            raise ValueError(f"Multiplication failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def subtract_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandResult":
        """Subtract two columns with error validation. Returns new CommandResult."""
        df = self.as_polars()
        try:
            df = df.with_columns(
                [
                    pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                    pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                ]
            )
            df = df.with_columns((pl.col(f"__{col1}_num") - pl.col(f"__{col2}_num")).alias(new_col)).drop(
                [f"__{col1}_num", f"__{col2}_num"]
            )
        except Exception as e:
            raise ValueError(f"Subtraction failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    # Matrix/array operations
    def slice_rows(
        self, start: int = 0, end: Optional[int] = None, step: int = 1, renderer: Optional[str] = None
    ) -> "CommandResult":
        """Slice rows like array[start:end:step]. Returns new CommandResult."""
        df = self.as_polars()
        df = df.slice(start, end if end is not None else df.height, step)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def slice_columns(self, columns: List[str], renderer: Optional[str] = None) -> "CommandResult":
        """Slice/select specific columns by name list. Returns new CommandResult."""
        df = self.as_polars()
        df = df.select(columns)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def transpose_matrix(self, renderer: Optional[str] = None) -> "CommandResult":
        """Transpose matrix/DataFrame. Returns new CommandResult."""
        df = self.as_polars()
        # Convert to numpy for transpose, then back to polars
        matrix = df.to_numpy()
        transposed = matrix.T
        # Create new column names
        new_columns = [f"col_{i}" for i in range(transposed.shape[1])]
        df_transposed = pl.DataFrame(transposed, schema=new_columns)
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df_transposed,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df_transposed, renderer)

    def reshape_matrix(self, new_shape: tuple, renderer: Optional[str] = None) -> "CommandResult":
        """Reshape matrix to new dimensions. Returns new CommandResult."""
        df = self.as_polars()
        matrix = df.to_numpy()
        try:
            reshaped = matrix.reshape(new_shape)
            # Create new column names
            if len(reshaped.shape) > 1:
                new_columns = [f"col_{i}" for i in range(reshaped.shape[1])]
            else:
                new_columns = ["values"]
            df_reshaped = pl.DataFrame(reshaped, schema=new_columns)
        except ValueError as e:
            raise ValueError(f"Cannot reshape matrix: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df_reshaped,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df_reshaped, renderer)

    # Advanced filtering with safe operations
    def filter_numeric_range(
        self,
        column: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        renderer: Optional[str] = None,
    ) -> "CommandResult":
        """Filter rows where numeric column value is in range [min_val, max_val]. Returns new CommandResult."""
        df = self.as_polars()
        try:
            # Safely convert to numeric
            numeric_col = pl.col(column).cast(pl.Float64)
            condition = pl.lit(True)  # Start with always true

            if min_val is not None:
                condition = condition & (numeric_col >= min_val)
            if max_val is not None:
                condition = condition & (numeric_col <= max_val)

            df = df.filter(condition & numeric_col.is_not_null())  # Also filter out nulls
        except Exception as e:
            raise ValueError(f"Numeric range filtering failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def filter_string_pattern(
        self, column: str, pattern: str, case_insensitive: bool = True, renderer: Optional[str] = None
    ) -> "CommandResult":
        """Filter rows where string column matches regex pattern. Returns new CommandResult."""
        df = self.as_polars()
        try:
            col_expr = pl.col(column).str.contains(pattern, literal=False)
            if case_insensitive:
                # Polars doesn't have case insensitive regex directly, convert to lowercase
                col_expr = pl.col(column).str.to_lowercase().str.contains(pattern.lower(), literal=False)
            df = df.filter(col_expr)
        except Exception as e:
            raise ValueError(f"String pattern filtering failed: {e}")
        return CommandResult(
            raw_output="",
            success=self.success,
            structured_output=df,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=DataFormat.POLARS,
            history=self.history,
            command_name=self.command_name,
        ).update_from_df(df, renderer)

    def add_to_history(
        self,
        command_string: str,
        command_type: str,
        structured_sample: Any = None,
        **kwargs,
    ) -> None:
        """Dodaje krok do historii wykonania"""
        from .execution_step import ExecutionStep

        step = ExecutionStep(
            command_string=command_string,
            command_type=command_type,
            success=self.success,
            exit_code=self.exit_code,
            data_format=self.data_format,
            structured_sample=structured_sample,
            metadata={**(self.metadata or {}), **kwargs},
        )

        self.history.add_step(step)

    # Metoda do łatwej ekstrakcji konkretnych pól z strukturalnych wyników
    def extract_field(self, field_name: str) -> List[Any]:
        """Extract a column by name from structured_output."""
        if isinstance(self.structured_output, pl.DataFrame):
            if field_name in self.structured_output.columns:
                return self.structured_output[field_name].to_list()
            return []
        elif (
            isinstance(self.structured_output, list)
            and self.structured_output
            and isinstance(self.structured_output[0], dict)
        ):
            # Legacy support for list of dicts
            return [item.get(field_name) for item in self.structured_output if field_name in item]
        return []

    def to_format(self, target_format: DataFormat) -> "CommandResult":
        """Konwertuje dane do innego formatu"""
        if self.data_format == target_format:
            return self

        converted_data = DataFormatConverter.convert(self.structured_output, self.data_format, target_format)

        if converted_data is None:
            return CommandResult(
                raw_output=self.raw_output,
                structured_output=[],
                data_format=target_format,
                exit_code=1,
                history=self.history,
                success=False,
            )

        return CommandResult(
            raw_output=self.raw_output,
            structured_output=converted_data,
            data_format=target_format,
            exit_code=self.exit_code,
            history=self.history,
            success=self.success,
        )
