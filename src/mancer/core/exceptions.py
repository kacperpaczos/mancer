# core/exceptions.py
from typing import Dict

class ValidationError(Exception):
    """Exception raised when command validation fails."""
    
    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        message = "\n".join([f"{field}: {error}" for field, error in errors.items()])
        super().__init__(f"Command validation failed:\n{message}")