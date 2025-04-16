#!/usr/bin/env python3
"""
Narzędzie do aktualizacji dozwolonych wersji komend bash w Mancer.

Umożliwia:
- Wyświetlanie aktualnie dozwolonych wersji narzędzi
- Dodawanie nowych wersji narzędzi
- Automatyczne wykrywanie i dodawanie wersji z bieżącego systemu
- Usuwanie wersji narzędzi

Przykłady użycia:
- ./update_versions.py list
- ./update_versions.py add ls 9.2
- ./update_versions.py detect --all
- ./update_versions.py detect ls grep
- ./update_versions.py remove df 2.34
"""

import os
import sys
import argparse
import logging
from typing import List, Set, Dict, Any, Optional

# Dodaj ścieżkę projektu do PYTHONPATH
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

try:
    from src.mancer.domain.model.config_manager import ConfigManager
    from src.mancer.domain.service.tool_version_service import ToolVersionService
except ImportError:
    print("Błąd: Nie można zaimportować modułów Mancer.")
    print("Upewnij się, że framework jest zainstalowany lub uruchom skrypt z katalogu projektu.")
    sys.exit(1)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def setup_argparse() -> argparse.ArgumentParser:
    """Konfiguruje parser argumentów linii poleceń."""
    parser = argparse.ArgumentParser(
        description="Narzędzie do aktualizacji dozwolonych wersji komend bash w Mancer."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Komenda do wykonania")
    
    # Komenda 'list' - wyświetlanie dozwolonych wersji
    list_parser = subparsers.add_parser("list", help="Wyświetl dozwolone wersje narzędzi")
    list_parser.add_argument(
        "tool_name", nargs="?", 
        help="Nazwa narzędzia (opcjonalnie - jeśli nie podano, wyświetla wszystkie)"
    )
    
    # Komenda 'add' - dodawanie wersji
    add_parser = subparsers.add_parser("add", help="Dodaj dozwoloną wersję narzędzia")
    add_parser.add_argument("tool_name", help="Nazwa narzędzia")
    add_parser.add_argument("version", help="Wersja narzędzia")
    
    # Komenda 'detect' - wykrywanie i dodawanie wersji z systemu
    detect_parser = subparsers.add_parser(
        "detect", 
        help="Wykryj i dodaj wersję narzędzia z bieżącego systemu"
    )
    detect_parser.add_argument(
        "tool_names", nargs="*", 
        help="Nazwy narzędzi (jeśli nie podano, użyj --all)"
    )
    detect_parser.add_argument(
        "--all", action="store_true", 
        help="Wykryj i dodaj wersje wszystkich znanych narzędzi"
    )
    
    # Komenda 'remove' - usuwanie wersji
    remove_parser = subparsers.add_parser("remove", help="Usuń dozwoloną wersję narzędzia")
    remove_parser.add_argument("tool_name", help="Nazwa narzędzia")
    remove_parser.add_argument("version", help="Wersja narzędzia")
    
    return parser

def list_allowed_versions(config_manager: ConfigManager, tool_name: Optional[str] = None) -> None:
    """
    Wyświetla dozwolone wersje narzędzi.
    
    Args:
        config_manager: Instancja ConfigManager
        tool_name: Nazwa narzędzia (opcjonalnie)
    """
    tools_config = config_manager._config["tool_versions"].get("tools", {})
    
    if tool_name:
        if tool_name not in tools_config:
            logger.info(f"Narzędzie {tool_name} nie ma zdefiniowanych dozwolonych wersji.")
            return
            
        versions = tools_config[tool_name]
        logger.info(f"Dozwolone wersje narzędzia {tool_name}:")
        for version in versions:
            logger.info(f"  - {version}")
    else:
        logger.info("Dozwolone wersje narzędzi:")
        for tool, versions in tools_config.items():
            logger.info(f"{tool}:")
            for version in versions:
                logger.info(f"  - {version}")

def add_allowed_version(
    tool_version_service: ToolVersionService, 
    tool_name: str, 
    version: str
) -> None:
    """
    Dodaje dozwoloną wersję narzędzia.
    
    Args:
        tool_version_service: Instancja ToolVersionService
        tool_name: Nazwa narzędzia
        version: Wersja narzędzia
    """
    tool_version_service.register_allowed_version(tool_name, version)
    logger.info(f"Dodano wersję {version} dla narzędzia {tool_name}.")

def detect_and_add_versions(
    tool_version_service: ToolVersionService, 
    tool_names: Optional[List[str]] = None,
    all_tools: bool = False
) -> None:
    """
    Wykrywa i dodaje wersje narzędzi z bieżącego systemu.
    
    Args:
        tool_version_service: Instancja ToolVersionService
        tool_names: Lista nazw narzędzi (opcjonalnie)
        all_tools: Czy wykryć wszystkie znane narzędzia
    """
    config_manager = ConfigManager()
    
    if all_tools:
        # Pobierz wszystkie znane narzędzia z konfiguracji
        tool_names = list(config_manager._config["tool_versions"].get("tools", {}).keys())
    
    if not tool_names:
        logger.info("Nie podano nazw narzędzi. Użyj argumentu --all, aby wykryć wszystkie znane narzędzia.")
        return
    
    for tool_name in tool_names:
        logger.info(f"Wykrywanie wersji narzędzia {tool_name}...")
        tool_version = tool_version_service.detect_tool_version(tool_name)
        
        if tool_version:
            logger.info(f"Wykryto wersję {tool_version.version} dla narzędzia {tool_name}.")
            
            # Sprawdź, czy wersja jest już dozwolona
            allowed_versions = config_manager.get_allowed_tool_versions(tool_name)
            if tool_version.version in allowed_versions:
                logger.info(f"Wersja {tool_version.version} jest już dozwolona dla narzędzia {tool_name}.")
            else:
                # Dodaj wykrytą wersję do dozwolonych
                tool_version_service.register_allowed_version(tool_name, tool_version.version)
                logger.info(f"Dodano wersję {tool_version.version} dla narzędzia {tool_name}.")
        else:
            logger.info(f"Nie udało się wykryć wersji narzędzia {tool_name}.")

def remove_allowed_version(
    config_manager: ConfigManager, 
    tool_name: str, 
    version: str
) -> None:
    """
    Usuwa dozwoloną wersję narzędzia.
    
    Args:
        config_manager: Instancja ConfigManager
        tool_name: Nazwa narzędzia
        version: Wersja narzędzia
    """
    # Pobierz aktualne dozwolone wersje
    allowed_versions = config_manager.get_allowed_tool_versions(tool_name)
    
    if not allowed_versions:
        logger.info(f"Narzędzie {tool_name} nie ma zdefiniowanych dozwolonych wersji.")
        return
    
    if version not in allowed_versions:
        logger.info(f"Wersja {version} nie jest dozwolona dla narzędzia {tool_name}.")
        return
    
    # Usuń wersję
    allowed_versions.remove(version)
    
    # Zaktualizuj konfigurację
    config_manager.set_allowed_tool_versions(tool_name, allowed_versions)
    logger.info(f"Usunięto wersję {version} dla narzędzia {tool_name}.")

def main() -> None:
    """Główna funkcja programu."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    config_manager = ConfigManager()
    tool_version_service = ToolVersionService()
    
    if args.command == "list":
        list_allowed_versions(config_manager, args.tool_name)
    elif args.command == "add":
        add_allowed_version(tool_version_service, args.tool_name, args.version)
    elif args.command == "detect":
        detect_and_add_versions(
            tool_version_service, 
            args.tool_names if hasattr(args, "tool_names") else None,
            getattr(args, "all", False)
        )
    elif args.command == "remove":
        remove_allowed_version(config_manager, args.tool_name, args.version)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 