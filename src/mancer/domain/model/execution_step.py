from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field

from .data_format import DataFormat


class ExecutionStep(BaseModel):
    """Single command execution step model."""

    command_string: str  # Command string
    command_type: str  # Command class name
    timestamp: datetime = Field(default_factory=datetime.now)
    data_format: DataFormat = DataFormat.LIST
    success: bool = True
    exit_code: int = 0
    structured_sample: Any = None  # Structured data sample
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize execution step to a dictionary."""
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        data["data_format"] = DataFormat.to_string(self.data_format)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionStep":
        """Create an execution step from a dictionary."""
        processed_data = data.copy()

        # Parsuj datę
        if isinstance(processed_data.get("timestamp"), str):
            processed_data["timestamp"] = datetime.fromisoformat(processed_data["timestamp"])

        # Parsuj data_format
        data_format_str = processed_data.get("data_format", "LIST")
        data_format = DataFormat.from_string(data_format_str)
        if data_format is None:
            data_format = DataFormat.LIST
        processed_data["data_format"] = data_format

        return cls.model_validate(processed_data)
