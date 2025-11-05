#!/usr/bin/env python3
"""
Skrypt do automatycznego dodawania przepisanych metod buildera do wszystkich klas komend.
Naprawia błędy mypy związane z kowariantnością typów.
"""

import re
from pathlib import Path


def find_command_files():
    """Znajdź wszystkie pliki komend."""
    command_dir = Path("src/mancer/infrastructure/command")
    command_files = []

    for file_path in command_dir.rglob("*_command.py"):
        if file_path.name != "base_command.py":
            command_files.append(file_path)

    return command_files


def get_class_name_from_file(file_path):
    """Wyciągnij nazwę klasy z pliku."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Znajdź definicję klasy
    class_match = re.search(r"class\s+(\w+Command)\s*\(", content)
    if class_match:
        return class_match.group(1)
    return None


def add_builder_methods(file_path, class_name):
    """Dodaj przepisane metody buildera do klasy."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Sprawdź czy metody buildera już istnieją
    if f'def with_option(self, option: str) -> "{class_name}":' in content:
        print(f"  {file_path.name}: Metody buildera już istnieją, pomijam")
        return False

    # Znajdź miejsce gdzie dodać metody buildera (po execute)
    execute_match = re.search(r"(def execute\([^}]+return result\s*)\s*(\n\s*def)", content, re.DOTALL)
    if not execute_match:
        # Spróbuj znaleźć po execute bez komentarza - szukaj po return result
        execute_match = re.search(r"(return result\s*)\s*(\n\s*def)", content, re.DOTALL)
    if execute_match:
        insert_point = execute_match.end(1)
        before_methods = content[:insert_point]
        after_methods = content[insert_point:]

        # Dodaj import DataFormat jeśli nie istnieje
        if "from ....domain.model.data_format import DataFormat" not in content:
            import_match = re.search(r"(from \.\.\.\.domain\.model\.command_result import CommandResult)", content)
            if import_match:
                content = content.replace(
                    import_match.group(1),
                    import_match.group(1) + "\nfrom ....domain.model.data_format import DataFormat",
                )

        # Dodaj metody buildera
        builder_methods = f'''

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "{class_name}":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "{class_name}":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "{class_name}":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "{class_name}":
        """Return a new instance marked to require sudo."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "{class_name}":
        """Return a new instance with an added positional argument."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "{class_name}":
        """Return a new instance with a preferred output data format."""
        new_instance: {class_name} = self.clone()  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

'''

        new_content = before_methods + builder_methods + after_methods

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"  {file_path.name}: Dodano metody buildera")
        return True

    print(f"  {file_path.name}: Nie znaleziono miejsca do wstawienia metod")
    return False


def main():
    """Główna funkcja skryptu."""
    print("Naprawianie typów w klasach komend...")

    command_files = find_command_files()
    print(f"Znaleziono {len(command_files)} plików komend")

    modified_count = 0
    for file_path in command_files:
        class_name = get_class_name_from_file(file_path)
        if class_name:
            print(f"Przetwarzam {file_path.name} (klasa: {class_name})")
            if add_builder_methods(file_path, class_name):
                modified_count += 1
        else:
            print(f"  {file_path.name}: Nie znaleziono nazwy klasy")

    print(f"\nZmodyfikowano {modified_count} plików")


if __name__ == "__main__":
    main()
