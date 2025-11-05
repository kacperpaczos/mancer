"""
Advanced filtering language for Mancer DataFrames.
Provides safe mathematical operations and matrix manipulations.
"""

import re
from typing import Any, Callable, List, Optional, Union

import polars as pl


class FilteringError(Exception):
    """Raised when filtering operations fail due to invalid data or operations."""

    pass


class SafeMath:
    """Safe mathematical operations with error validation."""

    @staticmethod
    def safe_add(a: Any, b: Any) -> Union[float, None]:
        """Safely add two values with error handling."""
        try:
            # Convert to float, handle None and invalid strings
            if a is None or b is None:
                return None
            a_float = (
                float(a)
                if isinstance(a, (int, float)) or (isinstance(a, str) and a.replace(".", "").replace("-", "").isdigit())
                else None
            )
            b_float = (
                float(b)
                if isinstance(b, (int, float)) or (isinstance(b, str) and b.replace(".", "").replace("-", "").isdigit())
                else None
            )

            if a_float is None or b_float is None:
                raise FilteringError(f"Cannot add non-numeric values: {a} + {b}")

            return a_float + b_float
        except (ValueError, TypeError) as e:
            raise FilteringError(f"Safe addition failed: {e}")

    @staticmethod
    def safe_subtract(a: Any, b: Any) -> Union[float, None]:
        """Safely subtract two values with error handling."""
        try:
            if a is None or b is None:
                return None
            a_float = (
                float(a)
                if isinstance(a, (int, float)) or (isinstance(a, str) and a.replace(".", "").replace("-", "").isdigit())
                else None
            )
            b_float = (
                float(b)
                if isinstance(b, (int, float)) or (isinstance(b, str) and b.replace(".", "").replace("-", "").isdigit())
                else None
            )

            if a_float is None or b_float is None:
                raise FilteringError(f"Cannot subtract non-numeric values: {a} - {b}")

            return a_float - b_float
        except (ValueError, TypeError) as e:
            raise FilteringError(f"Safe subtraction failed: {e}")

    @staticmethod
    def safe_multiply(a: Any, b: Any) -> Union[float, None]:
        """Safely multiply two values with error handling."""
        try:
            if a is None or b is None:
                return None
            a_float = (
                float(a)
                if isinstance(a, (int, float)) or (isinstance(a, str) and a.replace(".", "").replace("-", "").isdigit())
                else None
            )
            b_float = (
                float(b)
                if isinstance(b, (int, float)) or (isinstance(b, str) and b.replace(".", "").replace("-", "").isdigit())
                else None
            )

            if a_float is None or b_float is None:
                raise FilteringError(f"Cannot multiply non-numeric values: {a} * {b}")

            return a_float * b_float
        except (ValueError, TypeError) as e:
            raise FilteringError(f"Safe multiplication failed: {e}")

    @staticmethod
    def safe_divide(a: Any, b: Any) -> Union[float, None]:
        """Safely divide two values with error handling. Returns None for division by zero."""
        try:
            if a is None or b is None:
                return None
            a_float = (
                float(a)
                if isinstance(a, (int, float)) or (isinstance(a, str) and a.replace(".", "").replace("-", "").isdigit())
                else None
            )
            b_float = (
                float(b)
                if isinstance(b, (int, float)) or (isinstance(b, str) and b.replace(".", "").replace("-", "").isdigit())
                else None
            )

            if a_float is None or b_float is None:
                raise FilteringError(f"Cannot divide non-numeric values: {a} / {b}")

            if b_float == 0:
                return None  # Division by zero returns None instead of error

            return a_float / b_float
        except (ValueError, TypeError) as e:
            raise FilteringError(f"Safe division failed: {e}")


class MatrixOps:
    """Matrix and array operations."""

    @staticmethod
    def slice_2d(
        matrix: Union[List[List[Any]], pl.DataFrame], row_slice: slice = slice(None), col_slice: slice = slice(None)
    ) -> List[List[Any]]:
        """Slice 2D matrix like matrix[row_slice, col_slice]."""
        try:
            # Convert to list of lists if needed
            if isinstance(matrix, pl.DataFrame):
                matrix = matrix.to_numpy().tolist()

            rows = matrix[row_slice]
            result = []
            for row in rows:
                if isinstance(row, list):
                    result.append(row[col_slice])
                # Handle 1D arrays - row is already a single element
                # col_slice on a single element would be handled by the list case above
            return result
        except Exception as e:
            raise FilteringError(f"Matrix slicing failed: {e}")

    @staticmethod
    def transpose_2d(matrix: Union[List[List[Any]], pl.DataFrame]) -> List[List[Any]]:
        """Transpose 2D matrix."""
        try:
            if isinstance(matrix, pl.DataFrame):
                return matrix.to_numpy().T.tolist()

            if not matrix or not matrix[0]:
                return []

            # Standard transpose
            return [[matrix[j][i] for j in range(len(matrix))] for i in range(len(matrix[0]))]
        except Exception as e:
            raise FilteringError(f"Matrix transpose failed: {e}")

    @staticmethod
    def reshape_1d_to_2d(array: List[Any], rows: int, cols: int) -> List[List[Any]]:
        """Reshape 1D array to 2D matrix."""
        try:
            if len(array) != rows * cols:
                raise FilteringError(f"Cannot reshape array of size {len(array)} to {rows}x{cols}")

            result = []
            for i in range(rows):
                result.append(array[i * cols : (i + 1) * cols])
            return result
        except Exception as e:
            raise FilteringError(f"Array reshaping failed: {e}")


class FilterLanguage:
    """Advanced filtering language with safe operations."""

    @staticmethod
    def numeric_range(column: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Callable:
        """Create numeric range filter function."""

        def filter_func(df: pl.DataFrame) -> pl.DataFrame:
            try:
                numeric_col = pl.col(column).cast(pl.Float64)
                condition = pl.lit(True)

                if min_val is not None:
                    condition = condition & (numeric_col >= min_val)
                if max_val is not None:
                    condition = condition & (numeric_col <= max_val)

                return df.filter(condition & numeric_col.is_not_null())
            except Exception as e:
                raise FilteringError(f"Numeric range filter failed: {e}")

        return filter_func

    @staticmethod
    def string_pattern(column: str, pattern: str, case_insensitive: bool = True) -> Callable:
        """Create string pattern filter function."""

        def filter_func(df: pl.DataFrame) -> pl.DataFrame:
            try:
                if case_insensitive:
                    col_expr = pl.col(column).str.to_lowercase().str.contains(pattern.lower(), literal=False)
                else:
                    col_expr = pl.col(column).str.contains(pattern, literal=False)
                return df.filter(col_expr)
            except Exception as e:
                raise FilteringError(f"String pattern filter failed: {e}")

        return filter_func

    @staticmethod
    def safe_math_operation(col1: str, col2: str, operation: str, new_col: str) -> Callable:
        """Create safe mathematical operation function."""

        def math_func(df: pl.DataFrame) -> pl.DataFrame:
            try:
                if operation == "add":
                    return (
                        df.with_columns(
                            [
                                pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                                pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                            ]
                        )
                        .with_columns((pl.col(f"__{col1}_num") + pl.col(f"__{col2}_num")).alias(new_col))
                        .drop([f"__{col1}_num", f"__{col2}_num"])
                    )

                elif operation == "subtract":
                    return (
                        df.with_columns(
                            [
                                pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                                pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                            ]
                        )
                        .with_columns((pl.col(f"__{col1}_num") - pl.col(f"__{col2}_num")).alias(new_col))
                        .drop([f"__{col1}_num", f"__{col2}_num"])
                    )

                elif operation == "multiply":
                    return (
                        df.with_columns(
                            [
                                pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                                pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                            ]
                        )
                        .with_columns((pl.col(f"__{col1}_num") * pl.col(f"__{col2}_num")).alias(new_col))
                        .drop([f"__{col1}_num", f"__{col2}_num"])
                    )

                elif operation == "divide":
                    return (
                        df.with_columns(
                            [
                                pl.col(col1).cast(pl.Float64).alias(f"__{col1}_num"),
                                pl.col(col2).cast(pl.Float64).alias(f"__{col2}_num"),
                            ]
                        )
                        .with_columns(
                            pl.when(pl.col(f"__{col2}_num") != 0)
                            .then(pl.col(f"__{col1}_num") / pl.col(f"__{col2}_num"))
                            .otherwise(None)
                            .alias(new_col)
                        )
                        .drop([f"__{col1}_num", f"__{col2}_num"])
                    )

                else:
                    raise FilteringError(f"Unknown operation: {operation}")

            except Exception as e:
                raise FilteringError(f"Safe math operation '{operation}' failed: {e}")

        return math_func

    @staticmethod
    def matrix_slice(
        row_start: int = 0,
        row_end: Optional[int] = None,
        row_step: int = 1,
        col_start: int = 0,
        col_end: Optional[int] = None,
        col_step: int = 1,
    ) -> Callable:
        """Create matrix slicing function."""

        def slice_func(df: pl.DataFrame) -> pl.DataFrame:
            try:
                # Row slicing
                if row_step == 1:
                    length = (row_end - row_start) if row_end is not None else (df.height - row_start)
                    df = df.slice(row_start, length)
                else:
                    # For step != 1, use Python slicing on indices
                    indices = list(range(row_start, row_end if row_end is not None else df.height, row_step))
                    df = df[indices]

                # Column slicing - select every nth column
                if col_step > 1 or col_start > 0 or col_end is not None:
                    all_cols = df.columns
                    selected_cols = []
                    for i in range(
                        col_start, len(all_cols) if col_end is None else min(col_end, len(all_cols)), col_step
                    ):
                        if i < len(all_cols):
                            selected_cols.append(all_cols[i])
                    df = df.select(selected_cols)

                return df
            except Exception as e:
                raise FilteringError(f"Matrix slicing failed: {e}")

        return slice_func

    @staticmethod
    def custom_filter(filter_expression: str) -> Callable:
        """Create custom filter from string expression (safe evaluation)."""

        def custom_func(df: pl.DataFrame) -> pl.DataFrame:
            try:
                # Safe evaluation of filter expressions
                # Only allow safe operations
                allowed_names = {
                    "pl": pl,
                    "col": pl.col,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                }

                # Simple validation - only allow pl.col, logical operators, and basic functions
                if not re.match(r"^[pl.\w\s&|!=<>+\-*/()\[\]]+$", filter_expression):
                    raise FilteringError("Unsafe filter expression")

                # Evaluate in restricted environment
                condition = eval(filter_expression, {"__builtins__": {}}, allowed_names)
                return df.filter(condition)

            except Exception as e:
                raise FilteringError(f"Custom filter expression failed: {e}")

        return custom_func


# Convenience functions for easy access
def range_filter(column: str, min_val: Optional[float] = None, max_val: Optional[float] = None) -> Callable:
    """Convenience function for numeric range filtering."""
    return FilterLanguage.numeric_range(column, min_val, max_val)


def pattern_filter(column: str, pattern: str, case_insensitive: bool = True) -> Callable:
    """Convenience function for string pattern filtering."""
    return FilterLanguage.string_pattern(column, pattern, case_insensitive)


def safe_add(col1: str, col2: str, new_col: str) -> Callable:
    """Convenience function for safe addition."""
    return FilterLanguage.safe_math_operation(col1, col2, "add", new_col)


def safe_subtract(col1: str, col2: str, new_col: str) -> Callable:
    """Convenience function for safe subtraction."""
    return FilterLanguage.safe_math_operation(col1, col2, "subtract", new_col)


def safe_multiply(col1: str, col2: str, new_col: str) -> Callable:
    """Convenience function for safe multiplication."""
    return FilterLanguage.safe_math_operation(col1, col2, "multiply", new_col)


def safe_divide(col1: str, col2: str, new_col: str) -> Callable:
    """Convenience function for safe division."""
    return FilterLanguage.safe_math_operation(col1, col2, "divide", new_col)


def matrix_slice(rows: slice = slice(None), cols: slice = slice(None)) -> Callable:
    """Convenience function for matrix slicing."""
    return FilterLanguage.matrix_slice(
        rows.start or 0, rows.stop, rows.step or 1, cols.start or 0, cols.stop, cols.step or 1
    )
