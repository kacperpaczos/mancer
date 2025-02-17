# Mancer

A Python library for executing shell commands and managing system operations.

## Description

This project provides a high-level interface for executing shell commands, managing directories, and handling command outputs in Python applications.

Basic information about the project:

- Project name: Mancer
- Version: 0.1.0
- Author: Kacper Paczos
- License: GNU GPLv3
- Python version: 3.10+
- Project status: Development

## Project Structure
<pre>
tests/
├── __init__.py
├── conftest.py                    # konfiguracja pytest, wspólne fixtures
├── unit/                         # testy jednostkowe
│   ├── __init__.py
│   ├── test_command.py          # testy klasy Command
│   ├── test_command_result.py   # testy klasy CommandResult
│   └── test_shell_utils.py      # testy pomocniczych funkcji
│
├── integration/                  # testy integracyjne
│   ├── __init__.py
│   ├── test_shell_commands.py   # integracja poleceń powłoki
│   └── test_systemd_ops.py      # integracja z systemd
│
├── e2e/                         # testy end-to-end
│   ├── __init__.py
│   ├── test_shell_scenarios.py  # pełne scenariusze użycia shell
│   └── test_systemd_flows.py    # pełne scenariusze systemd
│
├── functional/                  # testy funkcjonalne
│   ├── __init__.py
│   └── test_basic_operations.py
│
├── performance/                 # testy wydajnościowe
│   ├── __init__.py
│   └── test_command_perf.py
│
└── smoke/                      # testy smoke
    ├── __init__.py
    └── test_basic_setup.py
</pre>
# Wszystkie testy
pytest

# Bez testów wymagających uprawnień
pytest -v -m "not privileged"

# Tylko testy integracyjne
pytest -v -m integration