from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Iterator
from .execution_step import ExecutionStep

@dataclass
class ExecutionHistory:
    """Model historii wykonania komend"""
    steps: List[ExecutionStep] = field(default_factory=list)
    
    def add_step(self, step: ExecutionStep) -> None:
        """Dodaje krok do historii"""
        self.steps.append(step)
    
    def get_step(self, index: int) -> Optional[ExecutionStep]:
        """Pobiera krok o podanym indeksie"""
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None
    
    def get_last_step(self) -> Optional[ExecutionStep]:
        """Pobiera ostatni krok"""
        if not self.steps:
            return None
        return self.steps[-1]
    
    def get_steps_count(self) -> int:
        """Zwraca liczbę kroków"""
        return len(self.steps)
    
    def all_successful(self) -> bool:
        """Sprawdza czy wszystkie kroki zakończyły się sukcesem"""
        if not self.steps:
            return True
        return all(step.success for step in self.steps)
    
    def __iter__(self) -> Iterator[ExecutionStep]:
        """Iteracja po krokach"""
        return iter(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje historię do słownika"""
        return {
            'steps': [step.to_dict() for step in self.steps],
            'total_steps': len(self.steps),
            'all_successful': self.all_successful()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ExecutionHistory':
        """Tworzy historię ze słownika"""
        history = ExecutionHistory()
        for step_data in data.get('steps', []):
            history.add_step(ExecutionStep.from_dict(step_data))
        return history 