from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from .data_format import DataFormat

@dataclass
class ExecutionStep:
    """Model pojedynczego kroku wykonania komendy"""
    command_string: str  # String komendy
    command_type: str  # Nazwa klasy komendy
    timestamp: datetime = field(default_factory=datetime.now)
    data_format: DataFormat = DataFormat.LIST
    success: bool = True
    exit_code: int = 0
    structured_sample: Any = None  # Próbka danych strukturalnych
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje krok wykonania do słownika"""
        return {
            'command_string': self.command_string,
            'command_type': self.command_type,
            'timestamp': self.timestamp.isoformat(),
            'data_format': DataFormat.to_string(self.data_format),
            'success': self.success,
            'exit_code': self.exit_code,
            'structured_sample': self.structured_sample,
            'metadata': self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ExecutionStep':
        """Tworzy krok wykonania ze słownika"""
        return ExecutionStep(
            command_string=data['command_string'],
            command_type=data['command_type'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            data_format=DataFormat.from_string(data['data_format']),
            success=data['success'],
            exit_code=data['exit_code'],
            structured_sample=data['structured_sample'],
            metadata=data.get('metadata', {})
        ) 