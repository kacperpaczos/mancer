"""Shared fixtures for unit tests."""

from __future__ import annotations

from typing import Callable
from unittest.mock import MagicMock

import polars as pl
import pytest

from mancer.domain.model.command_context import CommandContext
from mancer.domain.model.command_result import CommandResult


@pytest.fixture
def context() -> CommandContext:
    """Standard command context fixture."""
    return CommandContext(current_directory="/tmp/test")


@pytest.fixture
def mock_backend() -> MagicMock:
    """Pre-configured mock backend returning success by default."""
    backend = MagicMock()
    backend.execute.return_value = (0, "", "")
    return backend


def make_result(
    output: str = "",
    success: bool = True,
    exit_code: int = 0,
    error: str | None = None,
) -> CommandResult:
    """Helper to create CommandResult with defaults."""
    return CommandResult(
        raw_output=output,
        success=success,
        structured_output=pl.DataFrame({"raw_line": [output]}) if output else pl.DataFrame(),
        exit_code=exit_code,
        error_message=error,
    )


@pytest.fixture
def result_factory() -> Callable[..., CommandResult]:
    """Factory fixture for creating CommandResult instances."""
    return make_result

