#!/usr/bin/env python3
"""
Punkt wejściowy dla modułu SystemdInspector.
Umożliwia uruchamianie jako: python -m mancer.application.systemd_inspector
"""

from .cli import main

if __name__ == "__main__":
    main()
