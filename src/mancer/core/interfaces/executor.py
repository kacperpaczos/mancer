from abc import ABC, abstractmethod
from typing import List, Any

class Executor(ABC):
    """Interface for command executors."""
    
    @abstractmethod
    def run(self, command: List[str]) -> Any:
        """Run a command and return its result."""
        pass
