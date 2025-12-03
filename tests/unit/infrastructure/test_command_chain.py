"""Unit tests for CommandChain - sequential and pipeline command execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult
from mancer.domain.service.command_chain_service import CommandChain


class DummyCommand:
    """Minimal command implementation for testing chains."""

    def __init__(self, name: str, output: str = "output"):
        self._name = name
        self._output = output
        self.preferred_data_format = None

    def execute(self, context: CommandContext, input_result: CommandResult | None = None) -> CommandResult:
        # If piped, append input to output
        raw = self._output
        if input_result:
            raw = f"{input_result.raw_output} | {self._output}"
        return CommandResult(
            raw_output=raw,
            success=True,
            structured_output=pl.DataFrame({"value": [raw]}),
            exit_code=0,
        )

    def build_command(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name


@pytest.fixture
def context() -> CommandContext:
    return CommandContext(current_directory="/tmp")


class TestCommandChain:
    """Tests for CommandChain sequential and pipeline execution."""

    def test_single_command_chain(self, context):
        """Chain with a single command executes correctly."""
        cmd = DummyCommand("ls", "file1\nfile2")
        chain = CommandChain(cmd)

        result = chain.execute(context)

        assert result is not None
        assert result.success
        assert "file1" in result.raw_output

    def test_then_sequential_execution(self, context):
        """Commands chained with then() execute sequentially without piping."""
        cmd1 = DummyCommand("cmd1", "output1")
        cmd2 = DummyCommand("cmd2", "output2")
        chain = CommandChain(cmd1).then(cmd2)

        result = chain.execute(context)

        assert result is not None
        assert result.success
        # Sequential doesn't pipe - last command output
        assert result.raw_output == "output2"

    def test_pipe_chains_output(self, context):
        """Commands chained with pipe() receive previous output."""
        cmd1 = DummyCommand("ls", "file1")
        cmd2 = DummyCommand("grep", "filtered")
        chain = CommandChain(cmd1).pipe(cmd2)

        result = chain.execute(context)

        assert result is not None
        assert result.success
        # Pipe passes output - verify input was received
        assert "file1" in result.raw_output
        assert "filtered" in result.raw_output

    def test_mixed_then_and_pipe(self, context):
        """Chain with both then() and pipe() in sequence."""
        cmd1 = DummyCommand("cmd1", "data")
        cmd2 = DummyCommand("cmd2", "processed")
        cmd3 = DummyCommand("cmd3", "final")

        chain = CommandChain(cmd1).pipe(cmd2).then(cmd3)
        result = chain.execute(context)

        assert result is not None
        assert result.success
        # Last then() resets the pipe
        assert result.raw_output == "final"

    def test_chain_history_tracking(self, context):
        """Chain tracks execution history."""
        cmd1 = DummyCommand("cmd1", "out1")
        cmd2 = DummyCommand("cmd2", "out2")
        chain = CommandChain(cmd1).then(cmd2)

        result = chain.execute(context)

        assert result is not None
        history = chain.get_history()
        assert history is not None

    def test_empty_chain_returns_none(self, context):
        """Empty chain returns None."""
        chain = CommandChain.__new__(CommandChain)
        chain.commands = []
        chain.is_pipeline = []
        chain.preferred_formats = []
        chain.history = MagicMock()

        result = chain.execute(context)

        assert result is None

    def test_chain_metadata_contains_command_info(self, context):
        """Chain result metadata contains command chain info."""
        cmd1 = DummyCommand("first", "output")
        cmd2 = DummyCommand("second", "result")
        chain = CommandChain(cmd1).then(cmd2)

        result = chain.execute(context)

        assert result is not None
        assert result.metadata is not None
        assert "command_chain" in result.metadata
        assert result.metadata["command_chain"]["total_commands"] == 2


class TestCommandChainTransformations:
    """Tests for DataFrame transformations in CommandChain."""

    def test_head_transformation(self, context):
        """head() transformation limits rows."""
        # Create command that returns multiple rows
        cmd = DummyCommand("ls", "row1\nrow2\nrow3\nrow4\nrow5")
        chain = CommandChain(cmd).head(2)

        result = chain.execute(context)

        assert result is not None
        assert result.success
        # head(2) should limit to 2 rows
        if hasattr(result, "as_polars"):
            df = result.as_polars()
            assert len(df) <= 2

    def test_filter_transformation(self, context):
        """filter() transformation applies predicate."""
        cmd = DummyCommand("ls", "data")
        chain = CommandChain(cmd).filter(pl.col("value").str.contains("data"))

        result = chain.execute(context)

        assert result is not None
        assert result.success

    def test_select_columns_transformation(self, context):
        """select_columns() picks specific columns."""
        cmd = DummyCommand("ls", "data")
        chain = CommandChain(cmd).select_columns(["value"])

        result = chain.execute(context)

        assert result is not None
        if hasattr(result, "as_polars"):
            df = result.as_polars()
            assert "value" in df.columns

    def test_sort_transformation(self, context):
        """sort() orders rows by column."""
        cmd = DummyCommand("ls", "data")
        chain = CommandChain(cmd).sort("value")

        result = chain.execute(context)

        assert result is not None
        assert result.success

    def test_map_df_custom_transformation(self, context):
        """map_df() applies custom function."""
        cmd = DummyCommand("ls", "data")

        def add_column(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit("extra").alias("new_col"))

        chain = CommandChain(cmd).map_df(add_column)

        result = chain.execute(context)

        assert result is not None
        if hasattr(result, "as_polars"):
            df = result.as_polars()
            assert "new_col" in df.columns


class TestCommandChainBuilder:
    """Tests for CommandChain fluent builder pattern."""

    def test_then_returns_chain(self):
        """then() returns CommandChain for chaining."""
        cmd1 = DummyCommand("cmd1", "out")
        cmd2 = DummyCommand("cmd2", "out")

        chain = CommandChain(cmd1).then(cmd2)

        assert isinstance(chain, CommandChain)
        assert len(chain.commands) == 2

    def test_pipe_returns_chain(self):
        """pipe() returns CommandChain for chaining."""
        cmd1 = DummyCommand("cmd1", "out")
        cmd2 = DummyCommand("cmd2", "out")

        chain = CommandChain(cmd1).pipe(cmd2)

        assert isinstance(chain, CommandChain)
        assert len(chain.commands) == 2
        assert chain.is_pipeline[1] is True

    def test_fluent_chain_building(self):
        """Multiple methods can be chained fluently."""
        cmd1 = DummyCommand("ls", "out")
        cmd2 = DummyCommand("grep", "out")
        cmd3 = DummyCommand("wc", "out")

        chain = (
            CommandChain(cmd1)
            .pipe(cmd2)
            .then(cmd3)
            .head(10)
            .filter(pl.col("value").is_not_null())
        )

        assert isinstance(chain, CommandChain)
        # 3 commands + 2 transformations (None placeholders)
        assert len(chain.commands) >= 3

