#!/usr/bin/env python3
"""
Menedżer Prototypów - narzędzie do zarządzania prototypami frameworka Mancer

Umożliwia:
- Tworzenie nowych prototypów
- Uruchamianie prototypów
- Testowanie integracji z frameworkiem
- Generowanie raportów użycia frameworka
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PrototypeInfo:
    """Informacje o prototypie."""
    name: str
    path: Path
    description: str
    requirements: List[str]
    framework_usage: List[str]
    status: str = "unknown"


class PrototypeManager:
    """Główna klasa menedżera prototypów."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.prototypes_path = workspace_path / "prototypes"
        self.framework_path = workspace_path / "src"
        
    def discover_prototypes(self) -> List[PrototypeInfo]:
        """Odkrywa wszystkie prototypy w katalogu."""
        prototypes = []
        
        if not self.prototypes_path.exists():
            return prototypes
            
        for item in self.prototypes_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                info = self._analyze_prototype(item)
                if info:
                    prototypes.append(info)
                    
        return prototypes
    
    def _analyze_prototype(self, prototype_path: Path) -> Optional[PrototypeInfo]:
        """Analizuje pojedynczy prototyp."""
        readme_path = prototype_path / "README.md"
        requirements_path = prototype_path / "requirements.txt"
        
        if not readme_path.exists():
            return None
            
        # Wczytaj opis z README
        description = self._extract_description(readme_path)
        
        # Wczytaj wymagania
        requirements = []
        if requirements_path.exists():
            requirements = self._load_requirements(requirements_path)
            
        # Sprawdź użycie frameworka
        framework_usage = self._detect_framework_usage(prototype_path)
        
        return PrototypeInfo(
            name=prototype_path.name,
            path=prototype_path,
            description=description,
            requirements=requirements,
            framework_usage=framework_usage,
            status="ready"
        )
    
    def _extract_description(self, readme_path: Path) -> str:
        """Wyciąga opis z pliku README."""
        try:
            content = readme_path.read_text()
            lines = content.split('\n')
            for line in lines:
                if line.startswith('## Opis') or line.startswith('# '):
                    # Znajdź następną linię z opisem
                    for i, next_line in enumerate(lines[lines.index(line)+1:], 1):
                        if next_line.strip() and not next_line.startswith('#'):
                            return next_line.strip()
            return "Brak opisu"
        except Exception:
            return "Błąd odczytu opisu"
    
    def _load_requirements(self, requirements_path: Path) -> List[str]:
        """Wczytuje listę wymagań."""
        try:
            content = requirements_path.read_text()
            return [line.strip() for line in content.split('\n') 
                   if line.strip() and not line.startswith('#')]
        except Exception:
            return []
    
    def _detect_framework_usage(self, prototype_path: Path) -> List[str]:
        """Wykrywa użycie frameworka w kodzie."""
        usage = []
        python_files = list(prototype_path.rglob("*.py"))
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                if "from mancer" in content or "import mancer" in content:
                    usage.append(f"Import w {py_file.name}")
                if "mancer" in content:
                    usage.append(f"Użycie w {py_file.name}")
            except Exception:
                continue
                
        return usage
    
    def create_prototype(self, name: str, description: str) -> bool:
        """Tworzy nowy prototyp na podstawie szablonu."""
        template_path = self.prototypes_path / "template"
        if not template_path.exists():
            print(f"❌ Szablon nie istnieje: {template_path}")
            return False
            
        target_path = self.prototypes_path / name
        if target_path.exists():
            print(f"❌ Prototyp {name} już istnieje")
            return False
            
        try:
            # Skopiuj szablon
            import shutil
            shutil.copytree(template_path, target_path)
            
            # Zaktualizuj pliki
            self._customize_prototype(target_path, name, description)
            
            print(f"✅ Utworzono prototyp: {name}")
            print(f"   Ścieżka: {target_path}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd tworzenia prototypu: {e}")
            return False
    
    def _customize_prototype(self, prototype_path: Path, name: str, description: str):
        """Dostosowuje szablon prototypu."""
        # Zaktualizuj README
        readme_path = prototype_path / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            content = content.replace("Nazwa Prototypu", name)
            content = content.replace("Krótki opis tego, co robi prototyp", description)
            readme_path.write_text(content)
        
        # Zaktualizuj pyproject.toml
        pyproject_path = prototype_path / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            content = content.replace("prototype-template", f"prototype-{name}")
            content = content.replace("Szablon prototypu", description)
            pyproject_path.write_text(content)
    
    def run_prototype(self, name: str) -> bool:
        """Uruchamia prototyp."""
        prototype_path = self.prototypes_path / name
        if not prototype_path.exists():
            print(f"❌ Prototyp {name} nie istnieje")
            return False
            
        main_path = prototype_path / "main.py"
        if not main_path.exists():
            print(f"❌ Brak pliku main.py w prototypie {name}")
            return False
            
        try:
            print(f"🚀 Uruchamianie prototypu: {name}")
            
            # Uruchom w kontekście frameworka
            env = os.environ.copy()
            env['PYTHONPATH'] = f"{self.framework_path}:{env.get('PYTHONPATH', '')}"
            
            result = subprocess.run(
                [sys.executable, str(main_path)],
                cwd=prototype_path,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print("📤 Output:")
                print(result.stdout)
                
            if result.stderr:
                print("⚠️  Errors:")
                print(result.stderr)
                
            if result.returncode == 0:
                print(f"✅ Prototyp {name} zakończony pomyślnie")
                return True
            else:
                print(f"❌ Prototyp {name} zakończony z błędem (kod: {result.returncode})")
                return False
                
        except Exception as e:
            print(f"❌ Błąd uruchamiania prototypu: {e}")
            return False
    
    def generate_report(self) -> Dict:
        """Generuje raport o prototypach i ich użyciu frameworka."""
        prototypes = self.discover_prototypes()
        
        report = {
            "workspace": str(self.workspace_path),
            "framework_path": str(self.framework_path),
            "prototypes_count": len(prototypes),
            "prototypes": [],
            "framework_usage_summary": {}
        }
        
        for proto in prototypes:
            proto_info = {
                "name": proto.name,
                "description": proto.description,
                "requirements_count": len(proto.requirements),
                "framework_usage_count": len(proto.framework_usage),
                "status": proto.status
            }
            report["prototypes"].append(proto_info)
            
            # Podsumowanie użycia frameworka
            for usage in proto.framework_usage:
                if usage not in report["framework_usage_summary"]:
                    report["framework_usage_summary"][usage] = 0
                report["framework_usage_summary"][usage] += 1
        
        return report
    
    def print_report(self):
        """Wyświetla raport w konsoli."""
        report = self.generate_report()
        
        print("📊 RAPORT PROTOTYPÓW FRAMEWORKA MANCER")
        print("=" * 50)
        print(f"Workspace: {report['workspace']}")
        print(f"Framework: {report['framework_path']}")
        print(f"Liczba prototypów: {report['prototypes_count']}")
        print()
        
        if report["prototypes"]:
            print("📋 LISTA PROTOTYPÓW:")
            for proto in report["prototypes"]:
                print(f"  • {proto['name']}")
                print(f"    Opis: {proto['description']}")
                print(f"    Wymagania: {proto['requirements_count']}")
                print(f"    Użycie frameworka: {proto['framework_usage_count']}")
                print(f"    Status: {proto['status']}")
                print()
        
        if report["framework_usage_summary"]:
            print("🔧 UŻYCIE FRAMEWORKA:")
            for usage, count in report["framework_usage_summary"].items():
                print(f"  • {usage}: {count} prototypów")


def main():
    """Główna funkcja CLI."""
    parser = argparse.ArgumentParser(description="Menedżer Prototypów Frameworka Mancer")
    parser.add_argument("command", choices=["list", "create", "run", "report"], 
                       help="Komenda do wykonania")
    parser.add_argument("--name", help="Nazwa prototypu")
    parser.add_argument("--description", help="Opis prototypu")
    parser.add_argument("--workspace", default=".", help="Ścieżka do workspace")
    
    args = parser.parse_args()
    
    workspace_path = Path(args.workspace).resolve()
    manager = PrototypeManager(workspace_path)
    
    if args.command == "list":
        prototypes = manager.discover_prototypes()
        if prototypes:
            print("📁 ZNALEZIONE PROTOTYPY:")
            for proto in prototypes:
                print(f"  • {proto.name}: {proto.description}")
        else:
            print("📁 Brak prototypów")
            
    elif args.command == "create":
        if not args.name:
            print("❌ Podaj nazwę prototypu: --name")
            sys.exit(1)
        if not args.description:
            print("❌ Podaj opis prototypu: --description")
            sys.exit(1)
            
        success = manager.create_prototype(args.name, args.description)
        if not success:
            sys.exit(1)
            
    elif args.command == "run":
        if not args.name:
            print("❌ Podaj nazwę prototypu: --name")
            sys.exit(1)
            
        success = manager.run_prototype(args.name)
        if not success:
            sys.exit(1)
            
    elif args.command == "report":
        manager.print_report()


if __name__ == "__main__":
    import os
    main()
