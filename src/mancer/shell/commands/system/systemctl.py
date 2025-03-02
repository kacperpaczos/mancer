# shell/commands/system/systemctl.py
from mancer.core.base.command import BaseCommand
from typing import Dict, List, Any, Optional, Union

class SystemctlCommand(BaseCommand):
    """Systemctl command implementation."""
    
    VALID_ACTIONS = ["start", "stop", "restart", "reload", "enable", "disable", "status", "is-active", "is-enabled"]
    
    def __init__(self, executor=None):
        super().__init__(executor)
        self.action = None
        self.service = None
        self.user_mode = False
        self.no_pager = False
        self.quiet = False
        self.options = {}
    
    def set_action(self, action: str) -> 'SystemctlCommand':
        """Set systemctl action."""
        self.action = action
        return self
    
    def set_service(self, service: str) -> 'SystemctlCommand':
        """Set service name."""
        self.service = service
        return self
    
    def set_user_mode(self, user_mode: bool = True) -> 'SystemctlCommand':
        """Run in user mode."""
        self.user_mode = user_mode
        return self
    
    def set_no_pager(self, no_pager: bool = True) -> 'SystemctlCommand':
        """Do not pipe output into a pager."""
        self.no_pager = no_pager
        return self
    
    def set_quiet(self, quiet: bool = True) -> 'SystemctlCommand':
        """Suppress output."""
        self.quiet = quiet
        return self
    
    def set_option(self, key: str, value: Any) -> 'SystemctlCommand':
        """Set additional systemctl option."""
        self.options[key] = value
        return self
    
    def validate(self) -> Dict[str, str]:
        """Validate command parameters."""
        errors = {}
        
        if not self.action:
            errors["action"] = "Action must be specified"
        elif self.action not in self.VALID_ACTIONS:
            errors["action"] = f"Invalid action: {self.action}. Valid actions are: {', '.join(self.VALID_ACTIONS)}"
        
        if not self.service and self.action not in ["list-units", "list-unit-files"]:
            errors["service"] = "Service must be specified"
        
        return errors
    
    def build_command(self) -> List[str]:
        """Build systemctl command as list of arguments."""
        cmd = ["systemctl"]
        
        # Add options
        if self.user_mode:
            cmd.append("--user")
        
        if self.no_pager:
            cmd.append("--no-pager")
        
        if self.quiet:
            cmd.append("--quiet")
        
        # Add other options
        for key, value in self.options.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not None:
                cmd.extend([f"--{key}", str(value)])
        
        # Add action and service
        cmd.append(self.action)
        
        if self.service:
            cmd.append(self.service)
        
        return cmd