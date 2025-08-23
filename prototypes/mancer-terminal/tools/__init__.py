"""
Narzędzia Mancer Terminal
Skrypty pomocnicze do uruchamiania i zarządzania aplikacją
"""

__version__ = "1.0.0"
__description__ = "Narzędzia pomocnicze dla Mancer Terminal"

# Lista dostępnych narzędzi
AVAILABLE_TOOLS = [
    "run_terminal.sh",  # Skrypt bash do uruchomienia
    "run_terminal.py",  # Skrypt Python do uruchomienia
    "test_setup.sh",  # Test setupu środowiska
    "README.md",  # Dokumentacja narzędzi
]


def list_tools():
    """Wyświetla listę dostępnych narzędzi"""
    print("🛠️ Dostępne narzędzia Mancer Terminal:")
    print("=" * 50)

    for tool in AVAILABLE_TOOLS:
        if tool.endswith(".sh"):
            print(f"  🔧 {tool} - Skrypt bash")
        elif tool.endswith(".py"):
            print(f"  🐍 {tool} - Skrypt Python")
        elif tool.endswith(".md"):
            print(f"  📚 {tool} - Dokumentacja")
        else:
            print(f"  📁 {tool}")

    print("\n💡 Użycie:")
    print("  ./tools/run_terminal.sh --help     # Pomoc dla skryptu bash")
    print("  python3 tools/run_terminal.py --help  # Pomoc dla skryptu Python")
    print("  ./tools/test_setup.sh              # Test setupu")


if __name__ == "__main__":
    list_tools()
