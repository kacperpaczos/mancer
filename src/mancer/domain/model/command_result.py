from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..service.data_converter_service import DataFormatConverter
from .data_format import DataFormat
from .execution_history import ExecutionHistory


@dataclass
class CommandResult:
    """Represents the result of a command execution.

    Attributes:
        raw_output: Raw stdout/stderr captured as a single string.
        success: True if the command succeeded (exit_code==0 by convention).
        structured_output: Structured representation (typically a list of records).
        exit_code: Process exit code.
        error_message: Optional error message if available.
        metadata: Optional metadata associated with execution.
        data_format: Declared data format of structured_output.
        history: Execution history with steps and metadata.
    """

    raw_output: str
    success: bool
    structured_output: List[Any]
    exit_code: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data_format: DataFormat = DataFormat.LIST
    history: ExecutionHistory = field(default_factory=ExecutionHistory)

    def __str__(self) -> str:
        return self.raw_output

    def is_success(self) -> bool:
        return self.success

    def get_structured(self) -> List[Any]:
        """Return the structured_output as-is."""
        return self.structured_output

    def get_format(self) -> DataFormat:
        """Return the current data format of structured_output."""
        return self.data_format

    def get_history(self) -> ExecutionHistory:
        """Return the execution history for this result."""
        return self.history

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
        """Extract a column by key from structured_output when it is a list of dicts."""
        if not self.structured_output or not isinstance(
            self.structured_output[0], dict
        ):
            return []
        return [
            item.get(field_name)
            for item in self.structured_output
            if field_name in item
        ]

    def to_format(self, target_format: DataFormat) -> "CommandResult":
        """Konwertuje dane do innego formatu"""
        if self.data_format == target_format:
            return self

        converted_data = DataFormatConverter.convert(
            self.structured_output, self.data_format, target_format
        )

        if converted_data is None:
            return CommandResult(
                raw_output=self.raw_output,
                structured_output=None,
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
