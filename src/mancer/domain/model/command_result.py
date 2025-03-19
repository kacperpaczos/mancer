from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from .data_format import DataFormat
from .execution_history import ExecutionHistory

@dataclass
class CommandResult:
    """Model wyniku komendy"""
    raw_output: str
    success: bool
    structured_output: List[Any]  # Zawsze lista
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
        return self.structured_output
    
    def get_format(self) -> DataFormat:
        """Zwraca format danych"""
        return self.data_format
    
    def get_history(self) -> ExecutionHistory:
        """Zwraca historię wykonania komendy"""
        return self.history
    
    def add_to_history(self, command_string: str, command_type: str, 
                      structured_sample: Any = None, **kwargs) -> None:
        """Dodaje krok do historii wykonania"""
        from .execution_step import ExecutionStep
        
        step = ExecutionStep(
            command_string=command_string,
            command_type=command_type,
            success=self.success,
            exit_code=self.exit_code,
            data_format=self.data_format,
            structured_sample=structured_sample,
            metadata={**(self.metadata or {}), **kwargs}
        )
        
        self.history.add_step(step)
    
    # Metoda do łatwej ekstrakcji konkretnych pól z strukturalnych wyników
    def extract_field(self, field_name: str) -> List[Any]:
        """Ekstrahuje wartości konkretnego pola z listy słowników"""
        if not self.structured_output or not isinstance(self.structured_output[0], dict):
            return []
            
        return [item.get(field_name) for item in self.structured_output if field_name in item]
    
    def to_format(self, target_format: DataFormat) -> 'CommandResult':
        """Konwertuje wynik do innego formatu danych"""
        if self.data_format == target_format:
            return self
            
        if not DataFormat.is_convertible(self.data_format, target_format):
            raise ValueError(f"Konwersja z {self.data_format} do {target_format} nie jest możliwa")
            
        # Implementacja konwersji będzie dodana w DataFormatConverter
        from ..service.data_format_converter import DataFormatConverter
        converted_data = DataFormatConverter.convert(
            self.structured_output, 
            source_format=self.data_format,
            target_format=target_format
        )
        
        # Tworzymy nowy CommandResult z skonwertowanymi danymi
        result = CommandResult(
            raw_output=self.raw_output,
            success=self.success,
            structured_output=converted_data,
            exit_code=self.exit_code,
            error_message=self.error_message,
            metadata=self.metadata,
            data_format=target_format,
            history=self.history  # Historia zostaje zachowana
        )
        
        return result
