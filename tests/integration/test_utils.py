"""
Utilities do testów integracyjnych Docker dla Mancer - używające docker exec i bash commands
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Dodaj ścieżkę do Mancer
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))


class MancerDockerTestUtils:
    """Klasa pomocnicza do testów Mancer w Docker używająca docker exec"""

    @staticmethod
    def wait_for_container_ready(container_name: str, max_wait: int = 60) -> bool:
        """
        Czeka aż kontener będzie gotowy do pracy

        Args:
            container_name: Nazwa kontenera
            max_wait: Maksymalny czas oczekiwania w sekundach

        Returns:
            True jeśli kontener jest gotowy, False w przeciwnym razie
        """
        for _ in range(max_wait):
            try:
                result = subprocess.run(
                    ["docker", "exec", container_name, "echo", "ready"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                pass
            time.sleep(1)
        return False

    @staticmethod
    def execute_bash_command_in_container(
        container_name: str, command: str, working_dir: str = "/home/mancer1/mancer"
    ) -> Tuple[str, str, int]:
        """
        Wykonuje bash command w kontenerze przez docker exec

        Args:
            container_name: Nazwa kontenera Docker
            command: Bash command do wykonania
            working_dir: Katalog roboczy

        Returns:
            Tuple (stdout, stderr, return_code)
        """
        try:
            # Użyj docker exec do wykonania bash command
            docker_command = [
                "docker",
                "exec",
                "-w",
                working_dir,  # Set working directory
                container_name,
                "bash",
                "-c",
                command,
            ]

            result = subprocess.run(docker_command, capture_output=True, text=True, timeout=30)

            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            return "", "Command timeout", 124
        except Exception as e:
            return "", f"Docker exec error: {e}", 1

    @staticmethod
    def execute_mancer_app_with_shell_runner(
        container_name: str, app_path: str, test_commands: List[str] = None
    ) -> Dict:
        """
        Uruchamia aplikację Mancer używając ShellRunner w kontenerze

        Args:
            container_name: Nazwa kontenera Docker
            app_path: Ścieżka do aplikacji względem /home/mancer1/mancer/
            test_commands: Lista komend bash do wykonania w aplikacji

        Returns:
            Dict z wynikami testów
        """
        results = {
            "app_path": app_path,
            "timestamp": time.time(),
            "shell_runner_test": None,
            "commands_executed": [],
            "mancer_framework_status": "unknown",
        }

        try:
            # Test 1: Sprawdź czy można zaimportować ShellRunner
            import_test = """
import sys
sys.path.append("/home/mancer1/mancer/src")
try:
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type="bash")
    print("MANCER_SHELL_RUNNER_SUCCESS")
except Exception as e:
    print(f"MANCER_SHELL_RUNNER_ERROR: {e}")
"""

            stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                container_name,
                f"python3 -c '{import_test}'",
                f"/home/mancer1/mancer/{app_path}",
            )

            if "MANCER_SHELL_RUNNER_SUCCESS" in stdout:
                results["shell_runner_test"] = "success"
                results["mancer_framework_status"] = "operational"
            else:
                results["shell_runner_test"] = f"failed: {stdout} {stderr}"
                results["mancer_framework_status"] = "error"

            # Test 2: Wykonaj komendy testowe jeśli podane
            if test_commands:
                for cmd in test_commands:
                    cmd_result = {"command": cmd, "timestamp": time.time()}

                    stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                        container_name, cmd, f"/home/mancer1/mancer/{app_path}"
                    )

                    cmd_result.update(
                        {
                            "stdout": stdout[:500],  # Limit output
                            "stderr": stderr[:500] if stderr else None,
                            "exit_code": exit_code,
                            "success": exit_code == 0,
                        }
                    )

                    results["commands_executed"].append(cmd_result)

        except Exception as e:
            results["exception"] = str(e)

        return results

    @staticmethod
    def test_mancer_bash_commands(container_name: str) -> Dict:
        """
        Testuje podstawowe bash commands przez Mancer ShellRunner

        Args:
            container_name: Nazwa kontenera Docker

        Returns:
            Dict z wynikami testów Mancer commands
        """
        test_script = """
import sys
sys.path.append("/home/mancer1/mancer/src")

try:
    from mancer.application.shell_runner import ShellRunner
    import json
    
    # Inicjalizuj ShellRunner
    runner = ShellRunner(backend_type="bash")
    
    results = {
        "shell_runner_initialized": True,
        "commands_tested": []
    }
    
    # Test różnych komend Mancer
    test_commands = [
        ("ls", "ls -la"),
        ("echo", "echo 'Hello from Mancer'"),
        ("hostname", "hostname"),
        ("df", "df -h")
    ]
    
    for cmd_name, expected_bash in test_commands:
        try:
            # Utwórz komendę przez Mancer
            if cmd_name == "ls":
                cmd = runner.create_command("ls").long().all()
            elif cmd_name == "echo":
                cmd = runner.create_command("echo").text("Hello from Mancer")
            elif cmd_name == "hostname":
                cmd = runner.create_command("hostname")
            elif cmd_name == "df":
                cmd = runner.create_command("df").human_readable()
            else:
                continue
            
            # Wykonaj komendę
            result = runner.execute(cmd)
            
            cmd_result = {
                "command_name": cmd_name,
                "success": result.success,
                "output_length": len(result.raw_output),
                "has_output": bool(result.raw_output.strip())
            }
            
            results["commands_tested"].append(cmd_result)
            
        except Exception as e:
            results["commands_tested"].append({
                "command_name": cmd_name,
                "success": False,
                "error": str(e)
            })
    
    print("MANCER_TEST_RESULTS:", json.dumps(results))
    
except Exception as e:
    print("MANCER_TEST_ERROR:", str(e))
"""

        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{test_script}'"
        )

        # Parse results
        try:
            if "MANCER_TEST_RESULTS:" in stdout:
                json_part = stdout.split("MANCER_TEST_RESULTS:")[1].strip()
                return json.loads(json_part)
            else:
                return {
                    "error": "No test results found",
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                }
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse test results",
                "raw_output": stdout,
                "stderr": stderr,
            }

    @staticmethod
    def collect_container_metrics(container_name: str) -> Dict:
        """
        Zbiera metryki wydajności kontenera

        Args:
            container_name: Nazwa kontenera

        Returns:
            Słownik z metrykami
        """
        metrics = {
            "container_name": container_name,
            "timestamp": time.time(),
            "cpu_usage": None,
            "memory_usage": None,
            "process_count": None,
        }

        try:
            # Zbierz statystyki Docker
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    container_name,
                    "--no-stream",
                    "--format",
                    "{{.CPUPerc}},{{.MemUsage}},{{.PIDs}}",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                stats = result.stdout.strip().split(",")
                if len(stats) >= 3:
                    metrics["cpu_usage"] = stats[0].replace("%", "")
                    metrics["memory_usage"] = stats[1]
                    metrics["process_count"] = stats[2]

        except Exception as e:
            metrics["error"] = str(e)

        return metrics

    @staticmethod
    def save_test_results(results: Dict, output_file: str = "mancer_docker_test_results.json"):
        """
        Zapisuje wyniki testów do pliku JSON

        Args:
            results: Słownik z wynikami testów
            output_file: Nazwa pliku wyjściowego
        """
        output_path = Path("logs") / output_file
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def validate_mancer_installation(container_name: str) -> Dict[str, bool]:
        """
        Sprawdza czy Mancer jest poprawnie zainstalowany w kontenerze

        Args:
            container_name: Nazwa kontenera Docker

        Returns:
            Słownik z wynikami walidacji
        """
        validation_results = {
            "python_available": False,
            "mancer_importable": False,
            "shell_runner_available": False,
            "bash_backend_working": False,
            "command_factory_working": False,
        }

        # Test Python
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, "python3 --version"
        )
        if exit_code == 0 and stdout.startswith("Python 3"):
            validation_results["python_available"] = True

        # Test importu Mancer
        import_test = """
import sys
sys.path.append("/home/mancer1/mancer/src")
try:
    import mancer
    print("MANCER_IMPORT_SUCCESS")
except Exception as e:
    print(f"MANCER_IMPORT_ERROR: {e}")
"""

        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{import_test}'"
        )
        if "MANCER_IMPORT_SUCCESS" in stdout:
            validation_results["mancer_importable"] = True

        # Test ShellRunner
        runner_test = """
import sys
sys.path.append("/home/mancer1/mancer/src")
try:
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type="bash")
    print("SHELL_RUNNER_SUCCESS")
except Exception as e:
    print(f"SHELL_RUNNER_ERROR: {e}")
"""

        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{runner_test}'"
        )
        if "SHELL_RUNNER_SUCCESS" in stdout:
            validation_results["shell_runner_available"] = True

        # Test BashBackend
        backend_test = """
import sys
sys.path.append("/home/mancer1/mancer/src")
try:
    from mancer.infrastructure.backend.bash_backend import BashBackend
    backend = BashBackend()
    result = backend.execute_command("echo test")
    if result.success and "test" in result.raw_output:
        print("BASH_BACKEND_SUCCESS")
    else:
        print("BASH_BACKEND_FAILED")
except Exception as e:
    print(f"BASH_BACKEND_ERROR: {e}")
"""

        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{backend_test}'"
        )
        if "BASH_BACKEND_SUCCESS" in stdout:
            validation_results["bash_backend_working"] = True

        # Test CommandFactory
        factory_test = """
import sys  
sys.path.append("/home/mancer1/mancer/src")
try:
    from mancer.infrastructure.factory.command_factory import CommandFactory
    factory = CommandFactory("bash")
    ls_cmd = factory.create_command("ls")
    if ls_cmd is not None:
        print("COMMAND_FACTORY_SUCCESS")
    else:
        print("COMMAND_FACTORY_FAILED")
except Exception as e:
    print(f"COMMAND_FACTORY_ERROR: {e}")
"""

        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{factory_test}'"
        )
        if "COMMAND_FACTORY_SUCCESS" in stdout:
            validation_results["command_factory_working"] = True

        return validation_results
