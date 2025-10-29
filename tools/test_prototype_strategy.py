#!/usr/bin/env python3
"""
Test Strategii Prototypów - weryfikuje działanie całego systemu prototypów

Ten skrypt testuje:
1. Działanie menedżera prototypów
2. Tworzenie nowego prototypu
3. Uruchamianie prototypu
4. Generowanie raportów
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, capture_output=True):
    """Uruchamia komendę i zwraca wynik."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True, shell=True)
        return result
    except Exception as e:
        print(f"❌ Błąd uruchamiania komendy '{cmd}': {e}")
        return None


def test_prototype_manager():
    """Testuje menedżer prototypów."""
    print("🧪 Testowanie menedżera prototypów...")

    # Test listy prototypów
    result = run_command("python tools/prototype_manager.py list")
    if result and result.returncode == 0:
        print("✅ Lista prototypów działa")
    else:
        print("❌ Lista prototypów nie działa")
        return False

    # Test raportu
    result = run_command("python tools/prototype_manager.py report")
    if result and result.returncode == 0:
        print("✅ Generowanie raportów działa")
    else:
        print("❌ Generowanie raportów nie działa")
        return False

    return True


def test_prototype_creation():
    """Testuje tworzenie nowego prototypu."""
    print("\n🧪 Testowanie tworzenia prototypu...")

    test_name = "test-prototype"
    test_description = "Prototyp testowy do weryfikacji strategii"

    # Usuń istniejący prototyp testowy jeśli istnieje
    test_path = Path("prototypes") / test_name
    if test_path.exists():
        shutil.rmtree(test_path)

    # Utwórz nowy prototyp
    cmd = f'python tools/prototype_manager.py create --name "{test_name}" ' f'--description "{test_description}"'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print("✅ Tworzenie prototypu działa")

        # Sprawdź czy pliki zostały utworzone
        if test_path.exists():
            required_files = [
                "README.md",
                "main.py",
                "requirements.txt",
                "pyproject.toml",
            ]
            missing_files = [f for f in required_files if not (test_path / f).exists()]

            if not missing_files:
                print("✅ Wszystkie wymagane pliki zostały utworzone")
                return test_name
            else:
                print(f"❌ Brakujące pliki: {missing_files}")
                return None
        else:
            print("❌ Katalog prototypu nie został utworzony")
            return None
    else:
        print("❌ Tworzenie prototypu nie działa")
        return None


def test_prototype_execution(prototype_name):
    """Testuje uruchamianie prototypu."""
    print(f"\n🧪 Testowanie uruchamiania prototypu '{prototype_name}'...")

    # Sprawdź czy prototyp istnieje
    prototype_path = Path("prototypes") / prototype_name
    if not prototype_path.exists():
        print(f"❌ Prototyp {prototype_name} nie istnieje")
        return False

    # Uruchom prototyp
    cmd = f'python tools/prototype_manager.py run --name "{prototype_name}"'
    result = run_command(cmd)

    if result and result.returncode == 0:
        print("✅ Uruchamianie prototypu działa")
        return True
    else:
        print("❌ Uruchamianie prototypu nie działa")
        if result and result.stderr:
            print(f"Błąd: {result.stderr}")
        return False


def test_framework_integration(prototype_name):
    """Testuje integrację prototypu z frameworkiem."""
    print("\n🧪 Testowanie integracji z frameworkiem...")

    prototype_path = Path("prototypes") / prototype_name
    main_py = prototype_path / "main.py"

    if not main_py.exists():
        print("❌ Brak pliku main.py")
        return False

    try:
        # Sprawdź czy kod importuje framework
        content = main_py.read_text()

        if "from mancer" in content or "import mancer" in content:
            print("✅ Prototyp importuje framework")
        else:
            print("❌ Prototyp nie importuje frameworka")
            return False

        if "sys.path.insert" in content:
            print("✅ Prototyp ma poprawną konfigurację ścieżek")
        else:
            print("❌ Prototyp nie ma konfiguracji ścieżek")
            return False

        return True

    except Exception as e:
        print(f"❌ Błąd analizy kodu: {e}")
        return False


def cleanup_test_prototype(prototype_name):
    """Usuwa testowy prototyp."""
    print(f"\n🧹 Czyszczenie testowego prototypu '{prototype_name}'...")

    test_path = Path("prototypes") / prototype_name
    if test_path.exists():
        shutil.rmtree(test_path)
        print("✅ Testowy prototyp został usunięty")
    else:
        print("⚠️  Testowy prototyp już nie istnieje")


def run_integration_tests():
    """Uruchamia testy integracyjne."""
    print("\n🧪 Testy integracyjne...")

    # Sprawdź czy framework jest dostępny
    framework_path = Path("src/mancer")
    if not framework_path.exists():
        print("❌ Katalog frameworka nie istnieje")
        return False

    # Sprawdź czy szablon prototypu istnieje
    template_path = Path("prototypes/template")
    if not template_path.exists():
        print("❌ Szablon prototypu nie istnieje")
        return False

    print("✅ Podstawowa struktura jest poprawna")
    return True


def main():
    """Główna funkcja testów."""
    print("🚀 TEST STRATEGII PROTOTYPÓW FRAMEWORKA MANCER")
    print("=" * 60)

    # Sprawdź czy jesteśmy w odpowiednim katalogu
    if not Path("src/mancer").exists():
        print("❌ Uruchom skrypt z głównego katalogu projektu")
        sys.exit(1)

    # Testy integracyjne
    if not run_integration_tests():
        sys.exit(1)

    # Test menedżera prototypów
    if not test_prototype_manager():
        print("\n❌ Testy menedżera prototypów nie przeszły")
        sys.exit(1)

    # Test tworzenia prototypu
    prototype_name = test_prototype_creation()
    if not prototype_name:
        print("\n❌ Test tworzenia prototypu nie przeszedł")
        sys.exit(1)

    # Test integracji z frameworkiem
    if not test_framework_integration(prototype_name):
        print("\n❌ Test integracji z frameworkiem nie przeszedł")
        cleanup_test_prototype(prototype_name)
        sys.exit(1)

    # Test uruchamiania prototypu
    if not test_prototype_execution(prototype_name):
        print("\n❌ Test uruchamiania prototypu nie przeszedł")
        cleanup_test_prototype(prototype_name)
        sys.exit(1)

    # Czyszczenie
    cleanup_test_prototype(prototype_name)

    print("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
    print("✅ Strategia prototypów działa poprawnie")
    print("✅ Framework jest gotowy do użycia w prototypach")
    print("✅ Menedżer prototypów funkcjonuje")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
