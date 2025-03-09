from typing import List, Any, Optional, Dict
from ..base_command import BaseCommand
from ...backend.bash_backend import BashBackend
from ....domain.model.command_result import CommandResult
from ....domain.model.command_context import CommandContext

class SystemctlCommand(BaseCommand):
    """Komenda systemctl - zarządza usługami systemowymi"""
    
    def __init__(self):
        super().__init__("systemctl")
        self.backend = BashBackend()
    
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę systemctl"""
        # Budujemy komendę
        cmd_str = self.build_command()
        
        # Wykonujemy komendę
        result = self.backend.execute_command(
            cmd_str, 
            working_dir=context.current_directory
        )
        
        # Parsujemy wynik dla określonych podkomend
        if result.success and "operation" in self.parameters:
            operation = self.parameters.get("operation")
            if operation == "status" or operation == "list-units":
                result.structured_output = self._parse_units_output(result.raw_output)
        
        return result
    
    def _get_additional_args(self) -> List[str]:
        """Dodaje argumenty specyficzne dla systemctl"""
        args = []
        
        # Dodaj operację
        if "operation" in self.parameters:
            args.append(self.parameters["operation"])
        
        # Dodaj nazwę usługi, jeśli istnieje
        if "service" in self.parameters:
            args.append(self.parameters["service"])
        
        return args
    
    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla systemctl"""
        if name == "operation" or name == "service":
            return ""  # Te parametry są obsługiwane przez _get_additional_args
        return super()._format_parameter(name, value)
    
    def _parse_units_output(self, raw_output: str) -> List[Dict[str, str]]:
        """Parsuje wynik statusu usług systemowych"""
        result = []
        lines = raw_output.strip().split('\n')
        
        # Pomijamy pierwszą linię, jeśli to nagłówek
        start_idx = 0
        if len(lines) > 0 and lines[0].strip().startswith("UNIT"):
            start_idx = 1
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
                
            # Podziel linię na kolumny
            parts = line.split(None, 4)  # Maksymalnie 5 kolumn
            
            if len(parts) >= 5:
                unit_info = {
                    "unit": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": parts[4]
                }
                result.append(unit_info)
            elif len(parts) >= 1:
                # Jakiś inny format, zachowujemy co możemy
                result.append({"unit": parts[0]})
        
        return result
    
    # Metody specyficzne dla systemctl
    
    def start(self, service: str) -> 'SystemctlCommand':
        """Uruchamia usługę"""
        return self.with_param("operation", "start").with_param("service", service)
    
    def stop(self, service: str) -> 'SystemctlCommand':
        """Zatrzymuje usługę"""
        return self.with_param("operation", "stop").with_param("service", service)
    
    def restart(self, service: str) -> 'SystemctlCommand':
        """Restartuje usługę"""
        return self.with_param("operation", "restart").with_param("service", service)
    
    def status(self, service: str = None) -> 'SystemctlCommand':
        """Sprawdza status usługi lub wszystkich usług"""
        cmd = self.with_param("operation", "status")
        if service:
            cmd = cmd.with_param("service", service)
        return cmd
    
    def enable(self, service: str) -> 'SystemctlCommand':
        """Włącza usługę przy starcie systemu"""
        return self.with_param("operation", "enable").with_param("service", service)
    
    def disable(self, service: str) -> 'SystemctlCommand':
        """Wyłącza usługę przy starcie systemu"""
        return self.with_param("operation", "disable").with_param("service", service)
    
    def list_units(self) -> 'SystemctlCommand':
        """Wyświetla listę jednostek systemowych"""
        return self.with_param("operation", "list-units")
    
    def with_type(self, unit_type: str) -> 'SystemctlCommand':
        """Filtruje jednostki według typu (service, socket, etc.)"""
        return self.with_param("type", unit_type)
