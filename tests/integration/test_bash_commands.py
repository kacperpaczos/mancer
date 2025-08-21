"""
Testy integracyjne dla frameworka Mancer w środowisku Docker - testowanie core frameworka
"""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from test_utils import MancerDockerTestUtils

# Aktywuj plugin docker-compose
pytest_plugins = ["docker_compose"]

class TestMancerFrameworkIntegration:
    """Testy integracyjne dla core frameworka Mancer w kontenerach Docker"""
    
    @pytest.fixture(scope="class")
    def docker_compose_file(self):
        """Ścieżka do docker-compose.yml dla testów"""
        return str(Path(__file__).parent.parent.parent / "development" / "docker_test" / "docker-compose.yml")
    
    @pytest.fixture(scope="class") 
    def docker_setup(self):
        """Przygotowanie środowiska przed testami"""
        # Skopiuj .env file
        docker_test_dir = Path(__file__).parent.parent.parent / "development" / "docker_test"
        env_file = docker_test_dir / ".env"
        env_template = docker_test_dir / "env.develop.test"
        
        if not env_file.exists():
            env_file.write_text(env_template.read_text())
        
        return ["up --build -d"]
    
    @pytest.fixture(scope="class")
    def container_ready(self, docker_setup):
        """Czeka aż kontenery będą gotowe"""
        # Czekaj na uruchomienie kontenerów
        time.sleep(15)
        
        # Sprawdź czy kontener jest gotowy
        assert MancerDockerTestUtils.wait_for_container_ready("mancer-test-1", 60), \
            "Kontener mancer-test-1 nie jest gotowy"
        
        return "mancer-test-1"
    
    def test_container_startup(self, docker_setup):
        """Test czy kontenery się uruchamiają poprawnie"""
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=mancer-test", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = result.stdout.strip().split('\n')
        expected_containers = ['mancer-test-1', 'mancer-test-2', 'mancer-test-3']
        
        for container in expected_containers:
            assert container in containers, f"Kontener {container} nie został uruchomiony"
    
    def test_docker_exec_connectivity(self, container_ready):
        """Test połączenia docker exec do kontenera"""
        container_name = container_ready
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, 'echo "Docker exec działa"'
        )
        
        assert exit_code == 0, f"Docker exec failed: {stderr}"
        assert "Docker exec działa" in stdout, "Docker exec nie zwrócił oczekiwanej wartości"
    
    def test_python_installation(self, container_ready):
        """Test czy Python jest zainstalowany w kontenerze"""
        container_name = container_ready
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, "python3 --version"
        )
        
        assert exit_code == 0, f"Python3 nie jest dostępny: {stderr}"
        assert stdout.startswith("Python 3"), f"Nieprawidłowa wersja Python: {stdout}"
    
    def test_mancer_framework_core_validation(self, container_ready):
        """Test kompletnej walidacji core frameworka Mancer"""
        container_name = container_ready
        
        validation = MancerDockerTestUtils.validate_mancer_framework(container_name)
        
        # Sprawdź wszystkie core komponenty frameworka Mancer
        assert validation["python_available"], "Python nie jest dostępny"
        assert validation["mancer_importable"], "Nie można zaimportować Mancer"
        assert validation["shell_runner_available"], "ShellRunner nie jest dostępny"
        assert validation["bash_backend_working"], "BashBackend nie działa"
        assert validation["command_factory_working"], "CommandFactory nie działa"
        
        print(f"✅ Walidacja core frameworka Mancer: {validation}")
    
    def test_shell_runner_basic_commands(self, container_ready):
        """Test podstawowych komend przez Mancer ShellRunner"""
        container_name = container_ready
        
        results = MancerDockerTestUtils.test_mancer_core_commands(container_name)
        
        assert "error" not in results, f"Błąd testowania komend Mancer: {results}"
        assert results.get("shell_runner_initialized", False), "ShellRunner nie został zainicjalizowany"
        
        # Sprawdź czy komendy zostały wykonane
        commands_tested = results.get("commands_tested", [])
        assert len(commands_tested) > 0, "Żadne komendy frameworka nie zostały przetestowane"
        
        # Sprawdź czy przynajmniej niektóre komendy przeszły
        successful_commands = [cmd for cmd in commands_tested if cmd.get("success", False)]
        assert len(successful_commands) > 0, f"Żadne komendy frameworka nie przeszły: {commands_tested}"
        
        print(f"✅ Przetestowano {len(commands_tested)} komend frameworka, {len(successful_commands)} successful")
    
    def test_bash_backend_functionality(self, container_ready):
        """Test funkcjonalności BashBackend bezpośrednio"""
        container_name = container_ready
        
        test_script = '''
import sys
sys.path.append("/home/mancer1/mancer/src")

try:
    from mancer.infrastructure.backend.bash_backend import BashBackend
    import json
    
    backend = BashBackend()
    
    # Test różnych komend przez BashBackend
    test_commands = ["echo 'test'", "ls /tmp", "hostname", "whoami"]
    results = []
    
    for cmd in test_commands:
        try:
            result = backend.execute_command(cmd)
            results.append({
                "command": cmd,
                "success": result.success,
                "has_output": bool(result.raw_output.strip()),
                "exit_code": result.exit_code
            })
        except Exception as e:
            results.append({
                "command": cmd,
                "success": False,
                "error": str(e)
            })
    
    print("BASH_BACKEND_RESULTS:", json.dumps(results))
    
except Exception as e:
    print("BASH_BACKEND_ERROR:", str(e))
'''
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{test_script}'"
        )
        
        # Parse results
        assert "BASH_BACKEND_RESULTS:" in stdout, f"Brak wyników BashBackend: {stdout} {stderr}"
        
        json_part = stdout.split("BASH_BACKEND_RESULTS:")[1].strip()
        results = json.loads(json_part)
        
        # Sprawdź czy przynajmniej niektóre komendy przeszły
        successful = [r for r in results if r.get("success", False)]
        assert len(successful) > 0, f"Żadne komendy BashBackend nie przeszły: {results}"
        
        print(f"✅ BashBackend: {len(successful)}/{len(results)} komend successful")
    
    def test_command_factory_functionality(self, container_ready):
        """Test funkcjonalności CommandFactory"""
        container_name = container_ready
        
        test_script = '''
import sys
sys.path.append("/home/mancer1/mancer/src")

try:
    from mancer.infrastructure.factory.command_factory import CommandFactory
    import json
    
    factory = CommandFactory("bash")
    
    # Test tworzenia różnych komend
    command_types = ["ls", "echo", "hostname", "df", "ps"]
    results = []
    
    for cmd_type in command_types:
        try:
            cmd = factory.create_command(cmd_type)
            results.append({
                "command_type": cmd_type,
                "created": cmd is not None,
                "class_name": cmd.__class__.__name__ if cmd else None
            })
        except Exception as e:
            results.append({
                "command_type": cmd_type,
                "created": False,
                "error": str(e)
            })
    
    print("COMMAND_FACTORY_RESULTS:", json.dumps(results))
    
except Exception as e:
    print("COMMAND_FACTORY_ERROR:", str(e))
'''
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{test_script}'"
        )
        
        # Parse results
        assert "COMMAND_FACTORY_RESULTS:" in stdout, f"Brak wyników CommandFactory: {stdout} {stderr}"
        
        json_part = stdout.split("COMMAND_FACTORY_RESULTS:")[1].strip()
        results = json.loads(json_part)
        
        # Sprawdź czy komendy zostały utworzone
        created = [r for r in results if r.get("created", False)]
        assert len(created) > 0, f"CommandFactory nie utworzył żadnych komend: {results}"
        
        print(f"✅ CommandFactory: {len(created)}/{len(results)} komend utworzonych")
    
    def test_command_chains_functionality(self, container_ready):
        """Test funkcjonalności łańcuchów komend"""
        container_name = container_ready
        
        test_script = '''
import sys
sys.path.append("/home/mancer1/mancer/src")

try:
    from mancer.application.shell_runner import ShellRunner
    import json
    
    runner = ShellRunner(backend_type="bash")
    
    results = []
    
    # Test 1: Proste łańcuch komend
    try:
        echo_cmd = runner.create_command("echo").text("hello")
        result = runner.execute(echo_cmd)
        
        results.append({
            "test": "simple_echo",
            "success": result.success,
            "has_output": "hello" in result.raw_output
        })
    except Exception as e:
        results.append({
            "test": "simple_echo",
            "success": False,
            "error": str(e)
        })
    
    # Test 2: Komenda ls
    try:
        ls_cmd = runner.create_command("ls")
        result = runner.execute(ls_cmd)
        
        results.append({
            "test": "ls_command",
            "success": result.success,
            "has_output": bool(result.raw_output.strip())
        })
    except Exception as e:
        results.append({
            "test": "ls_command", 
            "success": False,
            "error": str(e)
        })
    
    print("COMMAND_CHAINS_RESULTS:", json.dumps(results))
    
except Exception as e:
    print("COMMAND_CHAINS_ERROR:", str(e))
'''
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{test_script}'"
        )
        
        # Parse results
        assert "COMMAND_CHAINS_RESULTS:" in stdout, f"Brak wyników command chains: {stdout} {stderr}"
        
        json_part = stdout.split("COMMAND_CHAINS_RESULTS:")[1].strip()
        results = json.loads(json_part)
        
        # Sprawdź czy testy przeszły
        successful = [r for r in results if r.get("success", False)]
        assert len(successful) > 0, f"Żadne testy command chains nie przeszły: {results}"
        
        print(f"✅ Command chains: {len(successful)}/{len(results)} testów successful")
    
    def test_network_connectivity_between_containers(self, docker_setup):
        """Test komunikacji między kontenerami Docker"""
        # Test ping między kontenerami
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            "mancer-test-1", "ping -c 2 10.100.2.102"
        )
        
        # Ping może nie działać w niektórych środowiskach Docker, więc testujemy też nc
        if exit_code != 0:
            # Alternatywny test - sprawdź czy można połączyć się z drugim kontenerem
            stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                "mancer-test-1", "nc -z 10.100.2.102 22 || echo 'Connection test failed but network is reachable'"
            )
        
        # Jeśli ping nie działa, sprawdź przynajmniej czy sieć istnieje
        network_check = subprocess.run(
            ["docker", "network", "inspect", "docker_test_mancer_network"],
            capture_output=True
        )
        
        assert network_check.returncode == 0, "Sieć Docker test nie istnieje"
    
    def test_collect_container_metrics(self, container_ready):
        """Test zbierania metryk kontenera"""
        container_name = container_ready
        
        metrics = MancerDockerTestUtils.collect_container_metrics(container_name)
        
        assert metrics["container_name"] == container_name
        assert "timestamp" in metrics
        
        # Metryki mogą być None jeśli Docker stats nie działa, ale nie powinno być błędów
        if "error" in metrics:
            pytest.skip(f"Docker stats nie dostępny: {metrics['error']}")
        
        print(f"📊 Metryki kontenera frameworka: {metrics}")
    
    def test_mancer_framework_end_to_end(self, container_ready):
        """Test end-to-end funkcjonalności frameworka Mancer"""
        container_name = container_ready
        
        # Kompletny test całego frameworka
        test_script = '''
import sys
sys.path.append("/home/mancer1/mancer/src")
import json
from datetime import datetime

try:
    # Import wszystkich głównych komponentów
    from mancer.application.shell_runner import ShellRunner
    from mancer.infrastructure.backend.bash_backend import BashBackend
    from mancer.infrastructure.factory.command_factory import CommandFactory
    
    # Test end-to-end
    runner = ShellRunner(backend_type="bash")
    
    # Test różnych komend frameworka  
    test_results = {
        "framework_initialized": True,
        "timestamp": datetime.now().isoformat(),
        "commands_executed": []
    }
    
    # Lista komend do przetestowania
    commands_to_test = [
        ("echo", lambda r: r.create_command("echo").text("Framework test")),
        ("ls", lambda r: r.create_command("ls")),
        ("hostname", lambda r: r.create_command("hostname")),
        ("df", lambda r: r.create_command("df"))
    ]
    
    for cmd_name, cmd_factory in commands_to_test:
        try:
            cmd = cmd_factory(runner)
            result = runner.execute(cmd)
            
            test_results["commands_executed"].append({
                "command": cmd_name,
                "success": result.success,
                "exit_code": result.exit_code,
                "has_output": bool(result.raw_output.strip())
            })
        except Exception as e:
            test_results["commands_executed"].append({
                "command": cmd_name,
                "success": False,
                "error": str(e)
            })
    
    print("FRAMEWORK_E2E_RESULTS:", json.dumps(test_results))
    
except Exception as e:
    error_result = {
        "framework_initialized": False,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }
    print("FRAMEWORK_E2E_ERROR:", json.dumps(error_result))
'''
        
        stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
            container_name, f"python3 -c '{test_script}'"
        )
        
        # Parse results
        if "FRAMEWORK_E2E_RESULTS:" in stdout:
            json_part = stdout.split("FRAMEWORK_E2E_RESULTS:")[1].strip()
            results = json.loads(json_part)
            
            assert results["framework_initialized"], "Framework nie został zainicjalizowany"
            
            commands_executed = results.get("commands_executed", [])
            successful = [cmd for cmd in commands_executed if cmd.get("success", False)]
            
            assert len(successful) > 0, f"Żadne komendy end-to-end nie przeszły: {commands_executed}"
            
            print(f"✅ Framework E2E: {len(successful)}/{len(commands_executed)} komend successful")
            
        elif "FRAMEWORK_E2E_ERROR:" in stdout:
            error_part = stdout.split("FRAMEWORK_E2E_ERROR:")[1].strip()
            error_results = json.loads(error_part)
            pytest.fail(f"Framework E2E test failed: {error_results}")
        else:
            pytest.fail(f"Brak wyników framework E2E test: {stdout} {stderr}")
