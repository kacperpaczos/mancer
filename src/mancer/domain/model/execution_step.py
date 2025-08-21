from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from .data_format import DataFormat


@dataclass
class ExecutionStep:
    """Single command execution step model."""

    command_string: str  # Command string
    command_type: str  # Command class name
    timestamp: datetime = field(default_factory=datetime.now)
    data_format: DataFormat = DataFormat.LIST
    success: bool = True
    exit_code: int = 0
    structured_sample: Any = None  # Structured data sample
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize execution step to a dictionary."""
        return {
            "command_string": self.command_string,
            "command_type": self.command_type,
            "timestamp": self.timestamp.isoformat(),
            "data_format": DataFormat.to_string(self.data_format),
            "success": self.success,
            "exit_code": self.exit_code,
            "structured_sample": self.structured_sample,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ExecutionStep":
        """Create an execution step from a dictionary."""
        return ExecutionStep(
            command_string=data["command_string"],
            command_type=data["command_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data_format=DataFormat.from_string(data["data_format"]),
            success=data["success"],
            exit_code=data["exit_code"],
            structured_sample=data["structured_sample"],
            metadata=data.get("metadata", {}),
        )
