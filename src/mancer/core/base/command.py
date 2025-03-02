from ..interfaces.command import CommandBuilder
from ..interfaces.executor import Executor
from typing import Dict, List, Any, Optional

class BaseCommand(CommandBuilder):
    """Base implementation for commands."""
    
    def __init__(self, executor: Optional[Executor] = None):
        from ..base.executor import DefaultExecutor
        self.executor = executor or DefaultExecutor()
    
    def _execute(self) -> Any:
        """Execute the built command."""
        return self.executor.run(self.build_command())