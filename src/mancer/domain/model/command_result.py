from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union

@dataclass
class CommandResult:
    """Model wyniku komendy"""
    raw_output: str
    success: bool
    structured_output: List[Any]  # Zawsze lista
    exit_code: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        return self.raw_output
    
    def is_success(self) -> bool:
        return self.success
    
    def get_structured(self) -> List[Any]:
        return self.structured_output
    
    # Metoda do łatwej ekstrakcji konkretnych pól z strukturalnych wyników
    def extract_field(self, field_name: str) -> List[Any]:
        """Ekstrahuje wartości konkretnego pola z listy słowników"""
        if not self.structured_output or not isinstance(self.structured_output[0], dict):
            return []
            
        return [item.get(field_name) for item in self.structured_output if field_name in item]
