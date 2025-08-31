"""
Mancer Terminal - SSH Terminal Emulator
Zaawansowany emulator terminala SSH zintegrowany z frameworkiem Mancer
"""

__version__ = "1.0.0"
__author__ = "Mancer Team"
__description__ = "SSH Terminal Emulator with SCP support and SSH proxy"

# Import głównych komponentów
try:
    from .gui import (
        FileTransferWidget,
        MancerTerminalWindow,
        SessionManagerWidget,
        TerminalWidget,
    )

    __all__ = [
        "MancerTerminalWindow",
        "TerminalWidget",
        "SessionManagerWidget",
        "FileTransferWidget",
    ]
except ImportError:
    # Jeśli GUI nie jest dostępne, eksportuj tylko podstawowe informacje
    __all__ = []

# Informacje o pakiecie
PACKAGE_INFO = {
    "name": "mancer-terminal",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "requires": [
        "PyQt6>=6.4.0",
        "paramiko>=3.0.0",
        "asyncssh>=2.12.0",
        "cryptography>=3.4.8",
    ],
    "python_requires": ">=3.8",
}
