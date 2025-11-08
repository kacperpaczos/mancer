from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl

from ..interface.command_interface import CommandInterface
from ..model.command_context import CommandContext
from ..model.command_result import CommandResult
from ..model.data_format import DataFormat
from ..model.execution_history import ExecutionHistory

try:
    from ...infrastructure.logging.mancer_logger import MancerLogger

    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


class CommandChain:
    """Klasa reprezentująca łańcuch komend"""

    def __init__(self, first_command: CommandInterface):
        self.commands: List[Optional[CommandInterface]] = [first_command]
        self.is_pipeline = [False]  # Pierwszy element jest zawsze False
        self.preferred_formats = [getattr(first_command, "preferred_data_format", DataFormat.POLARS)]
        self.history = ExecutionHistory()

    def then(self, next_command: CommandInterface) -> "CommandChain":
        """Dodaje kolejną komendę do łańcucha (sekwencyjnie)"""
        self.commands.append(next_command)
        self.is_pipeline.append(False)
        self.preferred_formats.append(getattr(next_command, "preferred_data_format", DataFormat.POLARS))
        return self

    def pipe(self, next_command: CommandInterface) -> "CommandChain":
        """Dodaje komendę jako potok (stdout -> stdin)"""
        self.commands.append(next_command)
        self.is_pipeline.append(True)
        self.preferred_formats.append(getattr(next_command, "preferred_data_format", DataFormat.POLARS))
        return self

    def with_data_format(self, format_type: DataFormat) -> "CommandChain":
        """Ustawia preferowany format danych dla wynikowego CommandResult"""
        # Ustawia preferowany format dla ostatniej komendy w łańcuchu
        if self.commands and self.commands[-1] is not None and hasattr(self.commands[-1], "preferred_data_format"):
            self.commands[-1].preferred_data_format = format_type
            self.preferred_formats[-1] = format_type
        return self

    def map_df(self, transform_fn: Callable[[Any], Any], renderer: Optional[str] = None) -> "CommandChain":
        """Dodaje transformację DataFrame między krokami łańcucha.

        Args:
            transform_fn: Funkcja transformacji przyjmująca DataFrame i zwracająca DataFrame
            renderer: Opcjonalny renderer do przeliczenia raw_output ('raw_line', 'csv', None)

        Returns:
            CommandChain: Zaktualizowany łańcuch
        """
        # Dodajemy specjalny "krok" transformacji - używamy None jako placeholder dla komendy
        self.commands.append(None)  # None oznacza transformację, nie komendę
        self.is_pipeline.append(False)  # Transformacje nie są pipeline'ami
        self.preferred_formats.append(DataFormat.POLARS)

        # Przechowujemy funkcję transformacji i renderer w dodatkowych listach
        if not hasattr(self, "transforms"):
            self.transforms = []
            self.renderers = []

        self.transforms.append(transform_fn)
        self.renderers.append(renderer)

        return self

    # Fluent DataFrame transformation methods for chains
    def filter(self, predicate: Any, renderer: Optional[str] = None) -> "CommandChain":
        """Add filter transformation to the chain."""
        return self.map_df(lambda df: df.filter(predicate), renderer)

    def select(self, columns: Any, renderer: Optional[str] = None) -> "CommandChain":
        """Add select transformation to the chain."""
        return self.map_df(lambda df: df.select(columns), renderer)

    def sort(self, by: Any, descending: bool = False, renderer: Optional[str] = None) -> "CommandChain":
        """Add sort transformation to the chain."""
        return self.map_df(lambda df: df.sort(by, descending=descending), renderer)

    def head(self, n: int = 5, renderer: Optional[str] = None) -> "CommandChain":
        """Add head transformation to the chain."""
        return self.map_df(lambda df: df.head(n), renderer)

    def tail(self, n: int = 5, renderer: Optional[str] = None) -> "CommandChain":
        """Add tail transformation to the chain."""
        return self.map_df(lambda df: df.tail(n), renderer)

    def group_by(self, by: Any, agg: Any = None, renderer: Optional[str] = None) -> "CommandChain":
        """Add group_by transformation to the chain."""

        def group_func(df):
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            if agg is not None:
                return df.group_by(by).agg(agg)
            # When no aggregation, return first row of each group
            return df.group_by(by).first()

        return self.map_df(group_func, renderer)

    def limit(self, n: int, renderer: Optional[str] = None) -> "CommandChain":
        """Add limit transformation to the chain (alias for head)."""
        return self.head(n, renderer)

    # Advanced column selection methods for chains
    def select_columns(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandChain":
        """Add column selection to the chain."""

        def select_func(df):
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            return df.select(columns)

        return self.map_df(select_func, renderer)

    def drop_columns(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandChain":
        """Add column dropping to the chain."""

        def drop_func(df):
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            return df.drop(columns)

        return self.map_df(drop_func, renderer)

    def rename_columns(self, mapping: Dict[str, str], renderer: Optional[str] = None) -> "CommandChain":
        """Add column renaming to the chain."""

        def rename_func(df):
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            return df.rename(mapping)

        return self.map_df(rename_func, renderer)

    # Advanced row selection methods for chains
    def filter_by_value(self, column: str, value: Any, renderer: Optional[str] = None) -> "CommandChain":
        """Add value-based filtering to the chain."""
        return self.map_df(lambda df: df.filter(pl.col(column) == value), renderer)

    def filter_not_value(self, column: str, value: Any, renderer: Optional[str] = None) -> "CommandChain":
        """Add not-value filtering to the chain."""
        return self.map_df(lambda df: df.filter(pl.col(column) != value), renderer)

    def filter_even_rows(self, renderer: Optional[str] = None) -> "CommandChain":
        """Add even rows filtering to the chain."""
        return self.map_df(
            lambda df: df.with_row_index("__idx").filter(pl.col("__idx") % 2 == 0).drop("__idx"), renderer
        )

    def filter_odd_rows(self, renderer: Optional[str] = None) -> "CommandChain":
        """Add odd rows filtering to the chain."""
        return self.map_df(
            lambda df: df.with_row_index("__idx").filter(pl.col("__idx") % 2 == 1).drop("__idx"), renderer
        )

    def filter_every_nth(self, n: int, offset: int = 0, renderer: Optional[str] = None) -> "CommandChain":
        """Add every Nth row filtering to the chain."""
        return self.map_df(
            lambda df: df.with_row_index("__idx").filter((pl.col("__idx") - offset) % n == 0).drop("__idx"), renderer
        )

    def where(self, condition: Any, renderer: Optional[str] = None) -> "CommandChain":
        """Add conditional filtering to the chain."""
        return self.map_df(lambda df: df.filter(condition), renderer)

    def sample(self, n: int, with_replacement: bool = False, renderer: Optional[str] = None) -> "CommandChain":
        """Add random sampling to the chain."""
        return self.map_df(lambda df: df.sample(n, with_replacement=with_replacement), renderer)

    # Mathematical operations for chains
    def add_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandChain":
        """Add column addition to the chain."""

        def add_func(df):
            try:
                # Ensure df is a DataFrame, not LazyFrame
                if isinstance(df, pl.LazyFrame):
                    df = df.collect()
                # Work with DataFrame directly, not LazyFrame chain
                # Use unique aliases to avoid duplicates when col1 == col2
                alias1 = f"__{col1}_num_1"
                alias2 = f"__{col2}_num_2"
                df = df.with_columns(
                    [
                        pl.col(col1).cast(pl.Float64, strict=False).alias(alias1),
                        pl.col(col2).cast(pl.Float64, strict=False).alias(alias2),
                    ]
                )
                df = df.with_columns((pl.col(alias1) + pl.col(alias2)).alias(new_col))
                return df.drop([alias1, alias2])
            except Exception as e:
                raise ValueError(f"Addition failed: {e}")

        return self.map_df(add_func, renderer)

    def divide_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandChain":
        """Add column division to the chain."""

        def divide_func(df):
            try:
                # Ensure df is a DataFrame, not LazyFrame
                if isinstance(df, pl.LazyFrame):
                    df = df.collect()
                # Use unique aliases to avoid duplicates when col1 == col2
                alias1 = f"__{col1}_num_1"
                alias2 = f"__{col2}_num_2"
                df = df.with_columns(
                    [
                        pl.col(col1).cast(pl.Float64, strict=False).alias(alias1),
                        pl.col(col2).cast(pl.Float64, strict=False).alias(alias2),
                    ]
                )
                df = df.with_columns(
                    pl.when(pl.col(alias2) != 0).then(pl.col(alias1) / pl.col(alias2)).otherwise(None).alias(new_col)
                )
                return df.drop([alias1, alias2])
            except Exception as e:
                raise ValueError(f"Division failed: {e}")

        return self.map_df(divide_func, renderer)

    def multiply_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandChain":
        """Add column multiplication to the chain."""

        def multiply_func(df):
            try:
                # Ensure df is a DataFrame, not LazyFrame
                if isinstance(df, pl.LazyFrame):
                    df = df.collect()
                # Use unique aliases to avoid duplicates when col1 == col2
                alias1 = f"__{col1}_num_1"
                alias2 = f"__{col2}_num_2"
                df = df.with_columns(
                    [
                        pl.col(col1).cast(pl.Float64, strict=False).alias(alias1),
                        pl.col(col2).cast(pl.Float64, strict=False).alias(alias2),
                    ]
                )
                df = df.with_columns((pl.col(alias1) * pl.col(alias2)).alias(new_col))
                return df.drop([alias1, alias2])
            except Exception as e:
                raise ValueError(f"Multiplication failed: {e}")

        return self.map_df(multiply_func, renderer)

    def subtract_columns(self, col1: str, col2: str, new_col: str, renderer: Optional[str] = None) -> "CommandChain":
        """Add column subtraction to the chain."""

        def subtract_func(df):
            try:
                # Ensure df is a DataFrame, not LazyFrame
                if isinstance(df, pl.LazyFrame):
                    df = df.collect()
                # Use unique aliases to avoid duplicates when col1 == col2
                alias1 = f"__{col1}_num_1"
                alias2 = f"__{col2}_num_2"
                df = df.with_columns(
                    [
                        pl.col(col1).cast(pl.Float64, strict=False).alias(alias1),
                        pl.col(col2).cast(pl.Float64, strict=False).alias(alias2),
                    ]
                )
                df = df.with_columns((pl.col(alias1) - pl.col(alias2)).alias(new_col))
                return df.drop([alias1, alias2])
            except Exception as e:
                raise ValueError(f"Subtraction failed: {e}")

        return self.map_df(subtract_func, renderer)

    # Matrix operations for chains
    def slice_rows(
        self, start: int = 0, end: Optional[int] = None, step: int = 1, renderer: Optional[str] = None
    ) -> "CommandChain":
        """Add row slicing to the chain."""

        def slice_func(df):
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            if step == 1:
                length = (end - start) if end is not None else (df.height - start)
                return df.slice(start, length)
            # For step != 1, use Python slicing on indices
            indices = list(range(start, end if end is not None else df.height, step))
            return df[indices]

        return self.map_df(slice_func, renderer)

    def slice_columns(self, columns: List[str], renderer: Optional[str] = None) -> "CommandChain":
        """Add column slicing to the chain."""
        return self.map_df(lambda df: df.select(columns), renderer)

    def transpose_matrix(self, renderer: Optional[str] = None) -> "CommandChain":
        """Add matrix transpose to the chain."""

        def transpose(df):
            # Ensure df is a DataFrame
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            # Convert to numpy, handling different types
            # Convert bool and other types to numeric for transpose
            matrix = df.to_numpy()
            # Convert object arrays (e.g., bool) to string or numeric
            if matrix.dtype == object:
                matrix = matrix.astype(str)
            transposed = matrix.T
            # Handle 1D case
            if len(transposed.shape) == 1:
                transposed = transposed.reshape(-1, 1)
            new_columns = [f"col_{i}" for i in range(transposed.shape[1])]
            return pl.DataFrame(transposed, schema=new_columns)

        return self.map_df(transpose, renderer)

    def reshape_matrix(self, new_shape: tuple, renderer: Optional[str] = None) -> "CommandChain":
        """Add matrix reshape to the chain."""

        def reshape(df):
            # Ensure df is a DataFrame
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
            matrix = df.to_numpy()
            total_elements = matrix.size
            expected_elements = new_shape[0] * (new_shape[1] if len(new_shape) > 1 else 1)

            # If reshape is not possible, return original or error
            if total_elements != expected_elements:
                raise ValueError(f"cannot reshape array of size {total_elements} into shape {new_shape}")

            reshaped = matrix.reshape(new_shape)
            # Convert object arrays (e.g., bool) to string or numeric for DataFrame creation
            if reshaped.dtype == object:
                reshaped = reshaped.astype(str)
            if len(reshaped.shape) > 1:
                new_columns = [f"col_{i}" for i in range(reshaped.shape[1])]
            else:
                new_columns = ["values"]
            return pl.DataFrame(reshaped, schema=new_columns)

        return self.map_df(reshape, renderer)

    # Advanced filtering for chains
    def filter_numeric_range(
        self,
        column: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        renderer: Optional[str] = None,
    ) -> "CommandChain":
        """Add numeric range filtering to the chain."""

        def numeric_filter(df):
            try:
                numeric_col = pl.col(column).cast(pl.Float64)
                condition = pl.lit(True)
                if min_val is not None:
                    condition = condition & (numeric_col >= min_val)
                if max_val is not None:
                    condition = condition & (numeric_col <= max_val)
                return df.filter(condition & numeric_col.is_not_null())
            except Exception as e:
                raise ValueError(f"Numeric range filtering failed: {e}")

        return self.map_df(numeric_filter, renderer)

    def filter_string_pattern(
        self, column: str, pattern: str, case_insensitive: bool = True, renderer: Optional[str] = None
    ) -> "CommandChain":
        """Add string pattern filtering to the chain."""

        def string_filter(df):
            try:
                col_expr = pl.col(column).str.contains(pattern, literal=False)
                if case_insensitive:
                    col_expr = pl.col(column).str.to_lowercase().str.contains(pattern.lower(), literal=False)
                return df.filter(col_expr)
            except Exception as e:
                raise ValueError(f"String pattern filtering failed: {e}")

        return self.map_df(string_filter, renderer)

    # Data manipulation methods for chains
    def drop_duplicates(self, subset: Optional[List[str]] = None, renderer: Optional[str] = None) -> "CommandChain":
        """Add duplicate removal to the chain."""
        return self.map_df(lambda df: df.unique() if subset is None else df.unique(subset=subset), renderer)

    def fill_nulls(
        self, value: Any, columns: Optional[List[str]] = None, renderer: Optional[str] = None
    ) -> "CommandChain":
        """Add null filling to the chain."""

        def fill_nulls_func(df):
            if columns is None:
                return df.fill_null(value)
            for col in columns:
                if col in df.columns:
                    df = df.with_columns(pl.col(col).fill_null(value))
            return df

        return self.map_df(fill_nulls_func, renderer)

    def drop_nulls(self, subset: Optional[List[str]] = None, renderer: Optional[str] = None) -> "CommandChain":
        """Add null dropping to the chain."""
        return self.map_df(lambda df: df.drop_nulls() if subset is None else df.drop_nulls(subset=subset), renderer)

    def describe(self, percentiles: Optional[List[float]] = None, renderer: Optional[str] = None) -> "CommandChain":
        """Add descriptive statistics to the chain."""

        def describe_func(df):
            local_percentiles = percentiles if percentiles is not None else [0.25, 0.5, 0.75]
            numeric_cols = [col for col in df.columns if df[col].dtype in [pl.Float64, pl.Int64]]
            if not numeric_cols:
                return pl.DataFrame()
            return df.select(numeric_cols).describe(percentiles=local_percentiles)

        return self.map_df(describe_func, renderer)

    def value_counts(self, column: str, sort: bool = True, renderer: Optional[str] = None) -> "CommandChain":
        """Add value counts to the chain."""

        def value_counts_func(df):
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found")
            result = df.group_by(column).agg(pl.count().alias("count"))
            if sort:
                result = result.sort("count", descending=True)
            return result

        return self.map_df(value_counts_func, renderer)

    # String operations for chains
    def str_upper(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandChain":
        """Add string uppercase conversion to the chain."""

        def str_upper_func(df):
            local_columns = [columns] if isinstance(columns, str) else columns
            for col in local_columns:
                if col in df.columns and df[col].dtype == pl.Utf8:
                    df = df.with_columns(pl.col(col).str.to_uppercase().alias(col))
            return df

        return self.map_df(str_upper_func, renderer)

    def str_lower(self, columns: Union[str, List[str]], renderer: Optional[str] = None) -> "CommandChain":
        """Add string lowercase conversion to the chain."""

        def str_lower_func(df):
            local_columns = [columns] if isinstance(columns, str) else columns
            for col in local_columns:
                if col in df.columns and df[col].dtype == pl.Utf8:
                    df = df.with_columns(pl.col(col).str.to_lowercase().alias(col))
            return df

        return self.map_df(str_lower_func, renderer)

    def str_contains(
        self, column: str, pattern: str, new_column: str, renderer: Optional[str] = None
    ) -> "CommandChain":
        """Add string contains check to the chain."""

        def str_contains_func(df):
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found")
            return df.with_columns(pl.col(column).str.contains(pattern).alias(new_column))

        return self.map_df(str_contains_func, renderer)

    def get_history(self) -> ExecutionHistory:
        """Zwraca historię wykonania łańcucha komend"""
        return self.history

    def _get_logger(self):
        """Pobiera logger, jeśli jest dostępny."""
        if LOGGER_AVAILABLE:
            return MancerLogger.get_instance()
        return None

    def _log_chain_structure(self):
        """Loguje strukturę łańcucha komend."""
        logger = self._get_logger()
        if not logger:
            return

        # Przygotuj opis łańcucha do zalogowania
        chain_steps = []
        for i, command in enumerate(self.commands):
            if command is None:
                # Transformacja DataFrame - pomijamy w logowaniu struktury
                continue
            command_name = command.__class__.__name__
            if hasattr(command, "name"):
                command_name = getattr(command, "name")

            step = {
                "name": command_name,
                "type": command.__class__.__name__,
                "connection": "pipe" if i > 0 and self.is_pipeline[i] else "then",
                "command_string": command.build_command(),
            }
            chain_steps.append(step)

        # Zaloguj łańcuch
        logger.log_command_chain(chain_steps)

    def execute(self, context: CommandContext) -> Optional[CommandResult]:
        """Wykonuje cały łańcuch komend"""
        if not self.commands:
            return None

        # Zaloguj strukturę łańcucha przed wykonaniem
        self._log_chain_structure()

        result = None
        current_context = context
        transform_counter = 0  # Track transform index separately

        for i, command in enumerate(self.commands):
            # Pierwszy element nie ma poprzedniego wyniku
            if i == 0:
                if command is None:
                    raise ValueError("First command in chain cannot be None")
                result = command.execute(current_context)
            else:
                # Sprawdź czy to transformacja DataFrame (command == None)
                if command is None:
                    # Transformacja DataFrame
                    if result and hasattr(result, "as_polars"):
                        df = result.as_polars()
                        # as_polars() always returns DataFrame, so no need to check for LazyFrame
                        if hasattr(self, "transforms") and transform_counter < len(self.transforms):
                            transform_fn = self.transforms[transform_counter]
                            renderer = self.renderers[transform_counter] if hasattr(self, "renderers") else None

                            # Zastosuj transformację
                            transformed_df = transform_fn(df)

                            # Ensure transformed_df is a DataFrame, not LazyFrame
                            # Note: DataFrame and LazyFrame are mutually exclusive,
                            # so this check is valid but mypy may not understand it
                            if isinstance(transformed_df, pl.LazyFrame):
                                transformed_df = transformed_df.collect()
                            # Type narrowing: after collect(), it's definitely a DataFrame
                            assert isinstance(transformed_df, pl.DataFrame)

                            # Zaktualizuj wynik
                            result.update_from_df(transformed_df, renderer)

                            # Increment transform counter for next transform
                            transform_counter += 1

                            # Dodaj do historii
                            result.add_to_history(
                                command_string=f"DataFrame transformation: {transform_fn.__name__}",
                                command_type="DataFrameTransform",
                                structured_sample=(
                                    transformed_df.head(5).to_dicts() if len(transformed_df) > 0 else None
                                ),
                            )
                elif self.is_pipeline[i]:
                    # Jeśli potok, przekazujemy wynik jako wejście
                    # Jeśli formaty danych się różnią, dokonaj konwersji
                    prev_format = self.preferred_formats[i - 1]
                    curr_format = self.preferred_formats[i]

                    if result and prev_format != curr_format and hasattr(result, "to_format"):
                        # Konwertuj wynik do preferowanego formatu bieżącej komendy
                        converted_result = result.to_format(curr_format)
                        if converted_result:
                            result = converted_result

                    result = command.execute(current_context, result)
                else:
                    # Jeśli sekwencja, używamy bieżącego kontekstu
                    result = command.execute(current_context)

            # Aktualizujemy kontekst po każdej komendzie
            if result and result.is_success():
                if command is not None:
                    current_context.add_to_history(command.build_command())

                # Dodajemy krok do historii wykonania łańcucha
                if hasattr(result, "get_history") and result.get_history():
                    # Kopiujemy historię z wyniku do historii łańcucha
                    for step in result.get_history().iter_steps():
                        self.history.add_step(step)

                # Zakładamy, że cd aktualizuje current_directory w kontekście
                if command is not None and command.__class__.__name__ == "CdCommand" and result.is_success():
                    # Nie trzeba robić nic więcej, bo komenda cd sama aktualizuje kontekst
                    pass

        # Dodajemy historię wykonania do metadanych wynikowego CommandResult
        if result and hasattr(result, "metadata"):
            if result.metadata is None:
                result.metadata = {}
            result.metadata["execution_history"] = self.history.model_dump()

            # Dodajemy także informację o całym łańcuchu
            result.metadata["command_chain"] = {
                "commands": [cmd.build_command() if cmd is not None else "<transform>" for cmd in self.commands],
                "pipeline_steps": self.is_pipeline,
                "total_commands": len(self.commands),
            }

        return result
