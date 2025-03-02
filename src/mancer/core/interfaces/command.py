from abc import ABC, abstractmethod
from typing import List, Any, TypeVar, Generic, Dict, Optional, Union

T = TypeVar('T', bound='CommandBuilder')

class CommandBuilder(ABC, Generic[T]):
    """Interface for command builders using method chaining."""
    
    @abstractmethod
    def build_command(self) -> List[str]:
        """Build command as list of arguments."""
        pass
    
    @abstractmethod
    def validate(self) -> Dict[str, str]:
        """Validate command parameters."""
        pass
    
    def is_valid(self) -> bool:
        """Check if command is valid."""
        return len(self.validate()) == 0
    
    def run(self) -> Any:
        """Build and execute the command."""
        errors = self.validate()
        if errors:
            from mancer.core.exceptions import ValidationError
            raise ValidationError(errors)
            
        return self._execute()
    
    @abstractmethod
    def _execute(self) -> Any:
        """Execute the built command."""
        pass
