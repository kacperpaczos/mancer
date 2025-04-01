import subprocess
import shlex
from typing import Dict, List, Any, Optional
from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult

class BashBackend(BackendInterface):
    """Backend wykonujący komendy w bashu"""
    
    def execute_command(self, command: str, working_dir: Optional[str] = None, 
                       env_vars: Optional[Dict[str, str]] = None, 
                       context_params: Optional[Dict[str, Any]] = None,
                       stdin: Optional[str] = None) -> CommandResult:
        """Wykonuje komendę w bashu"""
        try:
            # Przygotowanie środowiska
            process_env = None
            if env_vars:
                # Kopiujemy bieżące środowisko i dodajemy nowe zmienne
                import os
                process_env = os.environ.copy()
                process_env.update(env_vars)
            
            # Sprawdź, czy używamy live output
            use_live_output = False
            live_output_interval = 0.1  # domyślnie odświeżaj co 0.1 sekundy
            
            if context_params:
                use_live_output = context_params.get("live_output", False)
                live_output_interval = context_params.get("live_output_interval", 0.1)
            
            # Wykonanie komendy
            if use_live_output:
                import time
                import sys
                import threading
                import queue
                
                # Utwórz kolejkę dla wyjścia
                output_queue = queue.Queue()
                error_queue = queue.Queue()
                
                # Uruchom proces z pipe'ami
                process = subprocess.Popen(
                    command,
                    shell=True,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE if stdin else None,
                    cwd=working_dir,
                    env=process_env,
                    bufsize=1,  # line buffered
                    universal_newlines=True
                )
                
                # Jeśli mamy dane wejściowe, przekazujemy je do procesu
                if stdin:
                    process.stdin.write(stdin)
                    process.stdin.flush()
                    process.stdin.close()
                
                # Flagi do sygnalizacji zakończenia wątków
                stdout_done = threading.Event()
                stderr_done = threading.Event()
                
                # Funkcja do odczytu wyjścia
                def read_output(pipe, done_event, output_queue):
                    for line in iter(pipe.readline, ''):
                        output_queue.put(line)
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    done_event.set()
                
                # Funkcja do odczytu błędów
                def read_error(pipe, done_event, error_queue):
                    for line in iter(pipe.readline, ''):
                        error_queue.put(line)
                        sys.stderr.write(line)
                        sys.stderr.flush()
                    done_event.set()
                
                # Uruchom wątki do odczytu wyjścia
                stdout_thread = threading.Thread(
                    target=read_output,
                    args=(process.stdout, stdout_done, output_queue)
                )
                stderr_thread = threading.Thread(
                    target=read_error,
                    args=(process.stderr, stderr_done, error_queue)
                )
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()
                
                # Poczekaj na zakończenie procesu
                exit_code = process.wait()
                
                # Poczekaj na zakończenie wątków
                stdout_done.wait()
                stderr_done.wait()
                
                # Zbierz całe wyjście
                raw_output = ""
                while not output_queue.empty():
                    raw_output += output_queue.get()
                
                error_output = ""
                while not error_queue.empty():
                    error_output += error_queue.get()
                
                # Zamknij pipe'y
                process.stdout.close()
                process.stderr.close()
                
                # Parsowanie wyniku
                return self.parse_output(
                    command,
                    raw_output,
                    exit_code,
                    error_output
                )
            else:
                # Standardowe wykonanie bez live output
                process = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    cwd=working_dir,
                    env=process_env,
                    input=stdin
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
            import traceback
            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=f"{str(e)}\n{traceback.format_exc()}"
            )
    
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
