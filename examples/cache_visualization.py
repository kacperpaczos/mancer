import json
import random
import time

from mancer.application.shell_runner import ShellRunner

# Usunięto całą sekcję importu matplotlib
VISUALIZATION_AVAILABLE = False


def simulate_commands(runner, count=20, interval=0.5):
    """Symuluje wykonanie różnych komend dla celów demonstracyjnych"""
    # Używamy wszystkich dostępnych komend
    commands = [
        runner.create_command("ls").long(),
        runner.create_command("ps").aux(),
        runner.create_command("hostname"),
        runner.create_command("netstat").with_param("options", "all"),
        runner.create_command("systemctl").with_param("command", "status").with_param("service", "ssh"),
        runner.create_command("df").human_readable(),
        runner.create_command("echo").text("Hello from visualization example!"),
        runner.create_command("cat").file("/etc/hostname"),
        runner.create_command("grep").pattern("root").file("/etc/passwd"),
        runner.create_command("tail").lines(5).file("/var/log/syslog"),
        runner.create_command("head").lines(5).file("/etc/passwd"),
    ]

    for i in range(count):
        cmd = random.choice(commands)

        # Pobierz nazwę polecenia przed wykonaniem
        cmd_name = cmd.name if hasattr(cmd, "name") else "unknown"
        cmd_type = runner.get_command_type_name(cmd_name)

        # Pobierz pełne polecenie
        cmd_string = cmd.build_command() if hasattr(cmd, "build_command") else str(cmd)

        # Wykonujemy komendę z dodatkowymi metadanymi
        print(f"Wykonuję komendę: {cmd_string}")
        result = runner.execute(cmd)

        print(f"Wykonano komendę {i+1}/{count}: {cmd_type}")
        print(f"  Status: {'Sukces' if result.is_success() else 'Błąd'}")
        print(f"  Exit Code: {result.exit_code}")
        if result.raw_output:
            # Jeśli jest wyjście, wyświetl pierwsze 3 linie (lub mniej)
            output_lines = result.raw_output.strip().split("\n")
            if output_lines and output_lines[0]:
                sample = "\n    ".join(output_lines[:3])
                print(f"  Wyjście (fragment): {sample}")
                if len(output_lines) > 3:
                    print(f"    ... (oraz {len(output_lines) - 3} więcej linii)")
        print()

        time.sleep(interval)


def main():
    # Inicjalizacja runnera z włączonym cache
    runner = ShellRunner(
        backend_type="bash",
        enable_cache=True,
        cache_max_size=200,
        cache_auto_refresh=True,
        cache_refresh_interval=10,
        language="pl",  # Ustawiamy język polski dla nazw komend
    )

    print("=== Demonstracja cache w ShellRunner (z obsługą języków) ===\n")

    # Wyświetlamy dostępne języki
    available_languages = runner.get_available_languages()
    print(f"Dostępne języki: {', '.join(available_languages)}")
    print(f"Aktualny język: {runner.language}\n")

    # Symulujemy komendy
    print("Symulacja wykonania komend...")
    simulate_commands(runner, count=5, interval=0.5)

    # Wyświetlamy statystyki cache
    print("\nStatystyki cache:")
    stats = runner.get_cache_statistics()
    print(json.dumps(stats, indent=2))

    # Wyświetlamy historię komend
    print("\nHistoria wykonanych komend:")
    history = runner.get_command_history()

    for i, (cmd_id, timestamp, success) in enumerate(history):
        # Wyświetlamy podstawowe informacje
        print(f"{i+1}. ID: {cmd_id[:8]}...")
        print(f"   Czas: {timestamp}")
        print(f"   Status: {'Sukces' if success else 'Błąd'}")

        # Pobieramy wynik z cache
        result = runner.get_cached_result(cmd_id)
        if result and hasattr(result, "metadata") and result.metadata:
            # Pobieramy typ komendy z metadanych
            cmd_type = result.metadata.get("command_type", "unknown")
            cmd_string = result.metadata.get("command_string", "unknown")

            # Wyświetlamy polską nazwę komendy, używając metody z frameworka
            polish_cmd_name = runner.get_command_type_name(cmd_type)
            print(f"   Typ komendy: {polish_cmd_name}")
            print(f"   Polecenie: {cmd_string}")

            # Wyświetlamy exit code i fragmenty wyniku
            print(f"   Exit Code: {result.exit_code}")
            if result.raw_output:
                # Jeśli jest wyjście, wyświetl pierwsze 2 linie (lub mniej)
                output_lines = result.raw_output.strip().split("\n")
                if output_lines and output_lines[0]:
                    sample = "\n    ".join(output_lines[:2])
                    print(f"   Wyjście (fragment): {sample}")
                    if len(output_lines) > 2:
                        print(f"    ... (oraz {len(output_lines) - 2} więcej linii)")
        print()

    # Przykład zmiany języka
    print("\nZmiana języka na angielski:")
    runner.set_language("en")

    # Wyświetlamy to samo polecenie w innym języku
    if history and len(history) > 0:
        cmd_id = history[0][0]
        result = runner.get_cached_result(cmd_id)
        if result and result.metadata and "command_type" in result.metadata:
            cmd_type = result.metadata["command_type"]
            pl_name = runner.get_command_type_name(cmd_type, "pl")
            en_name = runner.get_command_type_name(cmd_type, "en")
            print(f"Polecenie {cmd_type}:")
            print(f"   - po polsku: {pl_name}")
            print(f"   - po angielsku: {en_name}")


if __name__ == "__main__":
    main()
