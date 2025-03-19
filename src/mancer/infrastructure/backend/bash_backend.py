import subprocess
import shlex
from typing import Dict, List, Any, Optional, Tuple
from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult

class BashBackend(BackendInterface):
    """Backend wykonujący komendy w bashu"""
    
    def execute_command(self, command: str, working_dir: Optional[str] = None, 
                       env_vars: Optional[Dict[str, str]] = None) -> CommandResult:
        """Wykonuje komendę w bashu"""
        try:
            # Przygotowanie środowiska
            process_env = None
            if env_vars:
                # Kopiujemy bieżące środowisko i dodajemy nowe zmienne
                import os
                process_env = os.environ.copy()
                process_env.update(env_vars)
            
            # Wykonanie komendy
            process = subprocess.run(
                command,
                shell=True,
                text=True,
                capture_output=True,
                cwd=working_dir,
                env=process_env
            )
            
            # Parsowanie wyniku
            return self.parse_output(
                command,
                process.stdout,
                process.returncode,
                process.stderr
            )
            
        except Exception as e:
            # Obsługa błędów
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=str(e)
            )
    
    def execute(self, command: str, input_data: Optional[str] = None, 
               working_dir: Optional[str] = None) -> Tuple[int, str, str]:
        """
        Executes a command and returns exit code, stdout, and stderr.
        This method is used by Command classes.
        
        Args:
            command: The command to execute
            input_data: Optional input data to pass to stdin
            working_dir: Optional working directory
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Prepare stdin if provided
            stdin = None
            if input_data:
                stdin = subprocess.PIPE
            
            # Execute the command
            process = subprocess.Popen(
                command,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=stdin,
                cwd=working_dir
            )
            
            # Send input data if provided
            stdout, stderr = process.communicate(input=input_data)
            exit_code = process.returncode
            
            return exit_code, stdout, stderr
        except Exception as e:
            return -1, "", str(e)
    
    def parse_output(self, command: str, raw_output: str, exit_code: int, 
                    error_output: str = "") -> CommandResult:
        """Parsuje wyjście komendy do standardowego formatu"""
        # Domyślnie zwracamy sukces, jeśli kod wyjścia jest 0
        success = exit_code == 0
        
        # Niektóre komendy mogą zwracać niepusty error_output nawet przy sukcesie
        # np. grep zwraca kod 1 gdy nie znaleziono wzorca, co nie jest faktycznym błędem
        
        # Próbujemy podstawowe strukturyzowanie wyniku (linie tekstu)
        structured_output = []
        if raw_output:
            structured_output = raw_output.strip().split('\n')
            # Usuwamy puste linie
            structured_output = [line for line in structured_output if line]
        
        return CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_output if not success else None
        )
    
    def build_command_string(self, command_name: str, options: List[str], 
                           params: Dict[str, Any], flags: List[str]) -> str:
        """Buduje string komendy zgodny z bashem"""
        parts = [command_name]
        
        # Opcje (krótkie, np. -l)
        parts.extend(options)
        
        # Flagi (długie, np. --recursive)
        parts.extend(flags)
        
        # Parametry (--name=value lub -n value)
        for name, value in params.items():
            if len(name) == 1:
                # Krótka opcja
                parts.append(f"-{name}")
                parts.append(shlex.quote(str(value)))
            else:
                # Długa opcja
                parts.append(f"--{name}={shlex.quote(str(value))}")
        
        return " ".join(parts)
