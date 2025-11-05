#!/usr/bin/env python3
"""
Przykład testowania core frameworka Mancer w Docker używając docker exec i bash commands

Ten przykład pokazuje jak:
1. Przetestować core komponenty frameworka Mancer w kontenerze Docker
2. Wykorzystać ShellRunner, BashBackend, CommandFactory
3. Zebrać wyniki i metryki wydajności frameworka
4. Przetestować funkcjonalność bash wrapper frameworka
5. Zapisać rezultaty testów frameworka

Wymagania:
- Uruchomiony system Docker test (./development/docker_test/start_test.sh)
- Zainstalowane dependencies: pip install pytest pytest-docker-compose
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Dodaj ścieżkę do testów
sys.path.append(str(Path(__file__).parent.parent / "tests" / "integration"))
from test_utils import MancerDockerTestUtils


class MancerFrameworkTester:
    """Klasa do testowania core frameworka Mancer przez docker exec i bash commands"""

    def __init__(self, container_name="mancer-test-1"):
        self.container_name = container_name
        self.results = {
            "session_start": datetime.now().isoformat(),
            "container_name": container_name,
            "framework_tests": [],
            "metrics": [],
            "errors": [],
        }

    def check_container_ready(self):
        """Sprawdź czy kontener jest gotowy"""
        try:
            ready = MancerDockerTestUtils.wait_for_container_ready(self.container_name, 30)
            if ready:
                print(f"✅ Kontener {self.container_name} jest gotowy")
                return True
            else:
                error_msg = f"❌ Kontener {self.container_name} nie jest gotowy"
                print(error_msg)
                self.results["errors"].append(error_msg)
                return False
        except Exception as e:
            error_msg = f"❌ Błąd sprawdzania kontenera: {e}"
            print(error_msg)
            self.results["errors"].append(error_msg)
            return False

    def test_framework_core_validation(self):
        """Test walidacji core komponentów frameworka"""
        print("\n🔧 Testowanie core komponentów frameworka Mancer...")

        test_result = {
            "test_name": "framework_core_validation",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            validation = MancerDockerTestUtils.validate_mancer_framework(self.container_name)

            # Sprawdź wszystkie core komponenty
            required_components = [
                "python_available",
                "mancer_importable",
                "shell_runner_available",
                "bash_backend_working",
                "command_factory_working",
            ]

            all_working = all(validation.get(comp, False) for comp in required_components)

            if all_working:
                test_result["status"] = "passed"
                test_result["details"] = validation
                print("  ✅ Wszystkie core komponenty frameworka działają")

                for comp, status in validation.items():
                    status_icon = "✅" if status else "❌"
                    print(f"    {status_icon} {comp}: {status}")
            else:
                test_result["status"] = "failed"
                test_result["details"] = validation
                print("  ❌ Niektóre core komponenty frameworka nie działają:")

                for comp, status in validation.items():
                    status_icon = "✅" if status else "❌"
                    print(f"    {status_icon} {comp}: {status}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas walidacji frameworka: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def test_shell_runner_functionality(self):
        """Test funkcjonalności ShellRunner - głównej klasy frameworka"""
        print("\n🧪 Testowanie ShellRunner - core frameworka...")

        test_result = {
            "test_name": "shell_runner_core_functionality",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            results = MancerDockerTestUtils.test_mancer_core_commands(self.container_name)

            if "error" not in results:
                test_result["status"] = "passed"
                test_result["details"] = results

                commands_tested = results.get("commands_tested", [])
                successful = len([cmd for cmd in commands_tested if cmd.get("success", False)])
                total = len(commands_tested)

                print(f"  ✅ ShellRunner core test: {successful}/{total} komend successful")

                for cmd in commands_tested:
                    cmd_name = cmd.get("command_name", "unknown")
                    success = cmd.get("success", False)
                    status_icon = "✅" if success else "❌"
                    print(f"    {status_icon} {cmd_name}: {success}")

            else:
                test_result["status"] = "failed"
                test_result["details"] = results
                print(f"  ❌ ShellRunner core test failed: {results}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas testu ShellRunner: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def test_bash_backend_directly(self):
        """Test bezpośredni BashBackend - core backend frameworka"""
        print("\n🔨 Testowanie BashBackend - core backend...")

        test_result = {
            "test_name": "bash_backend_direct_test",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            test_script = """
import sys
sys.path.append("/home/mancer1/mancer/src")
import json

try:
    from mancer.infrastructure.backend.bash_backend import BashBackend
    
    backend = BashBackend()
    
    # Test różnych komend bezpośrednio przez backend
    test_commands = [
        "echo 'backend_test'",
        "whoami", 
        "pwd",
        "ls /tmp",
        "hostname"
    ]
    
    results = []
    for cmd in test_commands:
        try:
            result = backend.execute_command(cmd)
            results.append({
                "command": cmd,
                "success": result.success,
                "exit_code": result.exit_code,
                "has_output": bool(result.raw_output.strip())
            })
        except Exception as e:
            results.append({
                "command": cmd,
                "success": False,
                "error": str(e)
            })
    
    print("BASH_BACKEND_DIRECT_RESULTS:", json.dumps(results))
    
except Exception as e:
    print("BASH_BACKEND_DIRECT_ERROR:", str(e))
"""

            stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                self.container_name, f"python3 -c '{test_script}'"
            )

            if "BASH_BACKEND_DIRECT_RESULTS:" in stdout:
                json_part = stdout.split("BASH_BACKEND_DIRECT_RESULTS:")[1].strip()
                results = json.loads(json_part)

                successful = [r for r in results if r.get("success", False)]
                total = len(results)

                if len(successful) > 0:
                    test_result["status"] = "passed"
                    test_result["details"] = {
                        "results": results,
                        "successful": len(successful),
                        "total": total,
                    }
                    print(f"  ✅ BashBackend direct test: {len(successful)}/{total} komend successful")
                else:
                    test_result["status"] = "failed"
                    test_result["details"] = {
                        "results": results,
                        "error": "No commands succeeded",
                    }
                    print("  ❌ BashBackend direct test: żadne komendy nie przeszły")

            else:
                test_result["status"] = "failed"
                test_result["details"] = {"stdout": stdout, "stderr": stderr}
                print(f"  ❌ BashBackend direct test failed: {stderr}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas testu BashBackend: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def test_command_factory_functionality(self):
        """Test funkcjonalności CommandFactory - core factory frameworka"""
        print("\n🏭 Testowanie CommandFactory - core factory...")

        test_result = {
            "test_name": "command_factory_functionality",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            test_script = """
import sys
sys.path.append("/home/mancer1/mancer/src")
import json

try:
    from mancer.infrastructure.factory.command_factory import CommandFactory
    
    factory = CommandFactory("bash")
    
    # Test tworzenia różnych typów komend frameworka
    command_types = ["ls", "echo", "hostname", "df", "ps", "cat", "grep"]
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
"""

            stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                self.container_name, f"python3 -c '{test_script}'"
            )

            if "COMMAND_FACTORY_RESULTS:" in stdout:
                json_part = stdout.split("COMMAND_FACTORY_RESULTS:")[1].strip()
                results = json.loads(json_part)

                created = [r for r in results if r.get("created", False)]
                total = len(results)

                if len(created) > 0:
                    test_result["status"] = "passed"
                    test_result["details"] = {
                        "results": results,
                        "created": len(created),
                        "total": total,
                    }
                    print(f"  ✅ CommandFactory test: {len(created)}/{total} komend utworzonych")

                    for r in results:
                        cmd_type = r.get("command_type", "unknown")
                        created_status = r.get("created", False)
                        status_icon = "✅" if created_status else "❌"
                        class_name = r.get("class_name", "None")
                        print(f"    {status_icon} {cmd_type}: {class_name}")
                else:
                    test_result["status"] = "failed"
                    test_result["details"] = {
                        "results": results,
                        "error": "No commands created",
                    }
                    print("  ❌ CommandFactory test: żadne komendy nie zostały utworzone")

            else:
                test_result["status"] = "failed"
                test_result["details"] = {"stdout": stdout, "stderr": stderr}
                print(f"  ❌ CommandFactory test failed: {stderr}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas testu CommandFactory: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def test_framework_cache_functionality(self):
        """Test funkcjonalności cache frameworka"""
        print("\n💾 Testowanie cache frameworka...")

        test_result = {
            "test_name": "framework_cache_functionality",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            cache_results = MancerDockerTestUtils.test_framework_cache_functionality(self.container_name)

            if "error" not in cache_results:
                test_result["status"] = "passed"
                test_result["details"] = cache_results

                cache_tests = cache_results.get("cache_tests", [])
                successful_tests = len([t for t in cache_tests if t.get("success", False)])

                print(f"  ✅ Framework cache test: {successful_tests}/{len(cache_tests)} testów successful")

                if "cache_stats" in cache_results:
                    print(f"  📊 Cache stats: {cache_results['cache_stats']}")
            else:
                test_result["status"] = "failed"
                test_result["details"] = cache_results
                print(f"  ❌ Framework cache test failed: {cache_results}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas testu cache: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def collect_framework_performance_metrics(self):
        """Zbierz metryki wydajności frameworka"""
        print("\n📊 Zbieranie metryk wydajności frameworka...")

        try:
            metrics = MancerDockerTestUtils.collect_container_metrics(self.container_name)
            metrics["collection_time"] = datetime.now().isoformat()
            metrics["framework_focus"] = True

            print(f"  📈 CPU usage: {metrics.get('cpu_usage', 'N/A')}")
            print(f"  🧠 Memory usage: {metrics.get('memory_usage', 'N/A')}")
            print(f"  🔢 Process count: {metrics.get('process_count', 'N/A')}")

            self.results["metrics"].append(metrics)
            return metrics

        except Exception as e:
            error_msg = f"Błąd zbierania metryk frameworka: {e}"
            print(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return None

    def run_framework_end_to_end_test(self):
        """Uruchom kompletny test end-to-end frameworka"""
        print("\n🚀 Testowanie frameworka end-to-end...")

        test_result = {
            "test_name": "framework_end_to_end",
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "details": {},
        }

        try:
            # Kompletny test e2e frameworka
            test_script = """
import sys
sys.path.append("/home/mancer1/mancer/src")
import json
from datetime import datetime

try:
    # Import wszystkich core komponentów frameworka
    from mancer.application.shell_runner import ShellRunner
    from mancer.infrastructure.backend.bash_backend import BashBackend
    from mancer.infrastructure.factory.command_factory import CommandFactory
    
    # Test kompletnej integracji frameworka
    results = {
        "framework_e2e": True,
        "timestamp": datetime.now().isoformat(),
        "integration_tests": []
    }
    
    # Test 1: ShellRunner + CommandFactory integration
    try:
        runner = ShellRunner(backend_type="bash")
        echo_cmd = runner.create_command("echo").text("E2E test")
        result = runner.execute(echo_cmd)
        
        results["integration_tests"].append({
            "test": "shellrunner_commandfactory_integration",
            "success": result.success and "E2E test" in result.raw_output
        })
    except Exception as e:
        results["integration_tests"].append({
            "test": "shellrunner_commandfactory_integration",
            "success": False,
            "error": str(e)
        })
    
    # Test 2: Direct BashBackend test
    try:
        backend = BashBackend()
        result = backend.execute_command("echo 'Direct backend test'")
        
        results["integration_tests"].append({
            "test": "direct_bashbackend",
            "success": result.success and "Direct backend test" in result.raw_output
        })
    except Exception as e:
        results["integration_tests"].append({
            "test": "direct_bashbackend", 
            "success": False,
            "error": str(e)
        })
    
    # Test 3: Multiple commands through framework
    try:
        runner = ShellRunner(backend_type="bash")
        commands = ["ls", "hostname", "whoami"]
        all_successful = True
        
        for cmd_name in commands:
            cmd = runner.create_command(cmd_name)
            result = runner.execute(cmd)
            if not result.success:
                all_successful = False
                break
        
        results["integration_tests"].append({
            "test": "multiple_commands_framework",
            "success": all_successful
        })
    except Exception as e:
        results["integration_tests"].append({
            "test": "multiple_commands_framework",
            "success": False,
            "error": str(e)
        })
    
    print("FRAMEWORK_E2E_RESULTS:", json.dumps(results))
    
except Exception as e:
    error_result = {
        "framework_e2e": False,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    }
    print("FRAMEWORK_E2E_ERROR:", json.dumps(error_result))
"""

            stdout, stderr, exit_code = MancerDockerTestUtils.execute_bash_command_in_container(
                self.container_name, f"python3 -c '{test_script}'"
            )

            if "FRAMEWORK_E2E_RESULTS:" in stdout:
                json_part = stdout.split("FRAMEWORK_E2E_RESULTS:")[1].strip()
                results = json.loads(json_part)

                integration_tests = results.get("integration_tests", [])
                successful = [t for t in integration_tests if t.get("success", False)]

                if len(successful) > 0:
                    test_result["status"] = "passed"
                    test_result["details"] = results
                    print(f"  ✅ Framework E2E: {len(successful)}/{len(integration_tests)} testów successful")

                    for test in integration_tests:
                        test_name = test.get("test", "unknown")
                        success = test.get("success", False)
                        status_icon = "✅" if success else "❌"
                        print(f"    {status_icon} {test_name}: {success}")
                else:
                    test_result["status"] = "failed"
                    test_result["details"] = results
                    print("  ❌ Framework E2E: żadne testy nie przeszły")

            elif "FRAMEWORK_E2E_ERROR:" in stdout:
                error_part = stdout.split("FRAMEWORK_E2E_ERROR:")[1].strip()
                error_results = json.loads(error_part)
                test_result["status"] = "failed"
                test_result["details"] = error_results
                print(f"  ❌ Framework E2E failed: {error_results}")
            else:
                test_result["status"] = "failed"
                test_result["details"] = {"stdout": stdout, "stderr": stderr}
                print("  ❌ Framework E2E: brak wyników")

        except Exception as e:
            test_result["status"] = "error"
            test_result["details"]["exception"] = str(e)
            print(f"  ❌ Wyjątek podczas E2E test: {e}")

        self.results["framework_tests"].append(test_result)
        return test_result

    def save_results(self, filename="mancer_framework_test_results.json"):
        """Zapisz wyniki testów frameworka do pliku"""
        self.results["session_end"] = datetime.now().isoformat()

        output_path = Path("logs") / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Wyniki frameworka zapisane do: {output_path}")

        # Podsumowanie testów frameworka
        total_tests = len(self.results["framework_tests"])
        passed_tests = len([t for t in self.results["framework_tests"] if t["status"] == "passed"])
        failed_tests = len([t for t in self.results["framework_tests"] if t["status"] == "failed"])

        print("\n📋 Podsumowanie testów frameworka Mancer:")
        print(f"  📊 Łącznie testów: {total_tests}")
        print(f"  ✅ Przeszło: {passed_tests}")
        print(f"  ❌ Nie przeszło: {failed_tests}")
        print(f"  🔍 Metryki zebrane: {len(self.results['metrics'])}")
        print(f"  ⚠️ Błędy: {len(self.results['errors'])}")


def main():
    """Główna funkcja przykładu testowania frameworka"""
    print("🐳 Przykład testowania core frameworka Mancer w Docker")
    print("=" * 60)

    # Sprawdź czy Docker test environment jest uruchomiony
    print("🔍 Sprawdzanie środowiska Docker...")

    tester = MancerFrameworkTester()

    if not tester.check_container_ready():
        print("❌ Kontener nie jest gotowy. Upewnij się, że:")
        print("  1. Docker test environment jest uruchomione")
        print("  2. Uruchom: cd development/docker_test && sudo ./start_test.sh")
        return 1

    try:
        # Test 1: Walidacja core frameworka
        tester.test_framework_core_validation()

        # Test 2: ShellRunner functionality
        tester.test_shell_runner_functionality()

        # Test 3: BashBackend direct test
        tester.test_bash_backend_directly()

        # Test 4: CommandFactory functionality
        tester.test_command_factory_functionality()

        # Test 5: Framework cache functionality
        tester.test_framework_cache_functionality()

        # Test 6: Framework E2E test
        tester.run_framework_end_to_end_test()

        # Zbierz metryki wydajności
        tester.collect_framework_performance_metrics()

        # Zapisz wyniki
        tester.save_results()

    except KeyboardInterrupt:
        print("\n⏹️ Test frameworka przerwany przez użytkownika")
        tester.save_results("interrupted_framework_test_results.json")
        return 130
    except Exception as e:
        print(f"\n💥 Nieoczekiwany błąd testowania frameworka: {e}")
        tester.results["errors"].append(f"Unexpected error: {e}")
        tester.save_results("error_framework_test_results.json")
        return 1

    print("\n🏁 Test frameworka Mancer zakończony pomyślnie!")
    return 0


if __name__ == "__main__":
    exit(main())
