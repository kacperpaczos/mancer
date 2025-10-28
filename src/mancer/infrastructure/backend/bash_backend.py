import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from ...domain.interface.backend_interface import BackendInterface
from ...domain.model.command_result import CommandResult


class BashBackend(BackendInterface):
    """Backend executing commands in the local bash shell."""

    def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        context_params: Optional[Dict[str, Any]] = None,
        stdin: Optional[str] = None,
    ) -> CommandResult:
        """Execute a command in bash."""
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
                import queue
                import sys
                import threading

                # Utwórz kolejkę dla wyjścia
                output_queue: queue.Queue[str] = queue.Queue()
                error_queue: queue.Queue[str] = queue.Queue()

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
                    universal_newlines=True,
                )

                # Jeśli mamy dane wejściowe, przekazujemy je do procesu
                if stdin and process.stdin:
                    process.stdin.write(stdin)
                    process.stdin.flush()
                    process.stdin.close()

                # Flagi do sygnalizacji zakończenia wątków
                stdout_done = threading.Event()
                stderr_done = threading.Event()

                # Funkcja do odczytu wyjścia
                def read_output(pipe, done_event, output_queue):
                    for line in iter(pipe.readline, ""):
                        output_queue.put(line)
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    done_event.set()

                # Funkcja do odczytu błędów
                def read_error(pipe, done_event, error_queue):
                    for line in iter(pipe.readline, ""):
                        error_queue.put(line)
                        sys.stderr.write(line)
                        sys.stderr.flush()
                    done_event.set()

                # Uruchom wątki do odczytu wyjścia
                stdout_thread = threading.Thread(
                    target=read_output, args=(process.stdout, stdout_done, output_queue)
                )
                stderr_thread = threading.Thread(
                    target=read_error, args=(process.stderr, stderr_done, error_queue)
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
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()

                # Parsowanie wyniku
                return self.parse_output(command, raw_output, exit_code, error_output)
            else:
                # Standardowe wykonanie bez live output
                completed_process = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=True,
                    cwd=working_dir,
                    env=process_env,
                    input=stdin,
                )

                # Parsowanie wyniku
                return self.parse_output(
                    command,
                    completed_process.stdout or "",
                    completed_process.returncode,
                    completed_process.stderr or "",
                )

        except Exception as e:
            # Obsługa błędów
            import traceback

            return CommandResult(
                raw_output="",
                success=False,
                structured_output=[],
                exit_code=-1,
                error_message=f"{str(e)}\n{traceback.format_exc()}",
            )

    def execute(
        self,
        command: str,
        input_data: Optional[str] = None,
        working_dir: Optional[str] = None,
        timeout: Optional[int] = 10,
    ) -> Tuple[int, str, str]:
        """Execute the command and return (exit_code, stdout, stderr).

        Used by Command classes.

        Args:
            command: The command to execute.
            input_data: Optional input data to pass to stdin.
            working_dir: Optional working directory.
            timeout: Optional timeout in seconds (default 10).

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Log the execution
            import time

            start_time = time.time()
            print(f"Executing command: {command[:100]}{' ...' if len(command) > 100 else ''}")

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
                cwd=working_dir,
                bufsize=1,  # Line buffered
            )

            # Send input data if provided and wait for completion with timeout
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                exit_code = process.returncode

                # Log completion
                duration = time.time() - start_time
                print(f"Command completed in {duration:.2f}s with exit code {exit_code}")

            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                print(f"Command timed out after {timeout}s: {command[:50]}...")
                process.kill()
                stdout, stderr = process.communicate()
                return (
                    -1,
                    stdout,
                    f"Command timed out after {timeout} seconds: {command}",
                )
            except KeyboardInterrupt:
                # Handle keyboard interrupt gracefully
                print("Command interrupted by user")
                process.kill()
                return -1, "", "Command interrupted by user"

            return exit_code, stdout, stderr
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            return -1, "", str(e)

    def parse_output(
        self, command: str, raw_output: str, exit_code: int, error_output: str = ""
    ) -> CommandResult:
        """Parse command output into a standard CommandResult."""
        success = exit_code == 0

        # Basic line-splitting structure
        structured_output = []
        if raw_output:
            structured_output = raw_output.strip().split("\n")
            structured_output = [line for line in structured_output if line]

        return CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_output if not success else None,
        )

    def build_command_string(
        self,
        command_name: str,
        options: List[str],
        params: Dict[str, Any],
        flags: List[str],
    ) -> str:
        """Build a bash-compatible command string."""
        parts = [command_name]
        parts.extend(options)
        parts.extend(flags)
        for name, value in params.items():
            if len(name) == 1:
                parts.append(f"-{name}")
                parts.append(shlex.quote(str(value)))
            else:
                parts.append(f"--{name}={shlex.quote(str(value))}")
        return " ".join(parts)
