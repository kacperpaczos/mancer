"""
Mancer Systemd Prototype
Zaawansowany TUI do zarządzania systemd z integracją frameworka Mancer
"""

__version__ = "0.1.0"
__author__ = "Mancer Team"
__description__ = "Zaawansowany TUI do zarządzania systemd"

from .main import SystemdTUI, main

__all__ = ["SystemdTUI", "main"]
