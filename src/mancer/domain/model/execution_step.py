from datetime import datetime
from typing import Any, Dict, cast

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .data_format import DataFormat


class ExecutionStepDict(TypedDict, total=False):
    """TypedDict representation of execution step for serialization."""

    command_string: str
    command_type: str
    timestamp: datetime
    data_format: DataFormat
    success: bool
    exit_code: int
    structured_sample: Any
    metadata: Dict[str, Any]


class ExecutionStep(BaseModel):
    """Single command execution step model."""

    command_string: str  # Command string
    command_type: str  # Command class name
    timestamp: datetime = Field(default_factory=datetime.now)
    data_format: DataFormat = DataFormat.POLARS
    success: bool = True
    exit_code: int = 0
    structured_sample: Any = None  # Structured data sample
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> ExecutionStepDict:
        """Convert execution step to a dictionary."""
        return cast(ExecutionStepDict, self.model_dump())

    @classmethod
    def from_dict(cls, data: ExecutionStepDict) -> "ExecutionStep":
        """Create an execution step from a dictionary."""
        return cls(**data)
