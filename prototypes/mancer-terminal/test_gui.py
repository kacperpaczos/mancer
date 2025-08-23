#!/usr/bin/env python3
"""
Prosty test GUI dla Mancer Terminal
"""

import os
import sys
from pathlib import Path

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_imports():
    """Testuje importy"""
    try:
        from PyQt6.QtWidgets import QApplication

        print("✅ PyQt6 import successful")
    except ImportError as e:
        print(f"❌ PyQt6 import failed: {e}")
        return False

    try:
        from gui.main_window import MancerTerminalWindow

        print("✅ MancerTerminalWindow import successful")
    except ImportError as e:
        print(f"❌ MancerTerminalWindow import failed: {e}")
        return False

    try:
        from gui.terminal_widget import TerminalWidget

        print("✅ TerminalWidget import successful")
    except ImportError as e:
        print(f"❌ TerminalWidget import failed: {e}")
        return False

    try:
        from gui.session_manager_widget import SessionManagerWidget

        print("✅ SessionManagerWidget import successful")
    except ImportError as e:
        print(f"❌ SessionManagerWidget import failed: {e}")
        return False

    try:
        from gui.file_transfer_widget import FileTransferWidget

        print("✅ FileTransferWidget import successful")
    except ImportError as e:
        print(f"❌ FileTransferWidget import failed: {e}")
        return False

    try:
        from gui.connection_dialog import ConnectionDialog

        print("✅ ConnectionDialog import successful")
    except ImportError as e:
        print(f"❌ ConnectionDialog import failed: {e}")
        return False

    return True


def test_mancer_integration():
    """Testuje integrację z Mancer"""
    try:
        from mancer.infrastructure.backend.ssh_backend import (
            SCPTransfer,
            SshBackend,
            SSHSession,
        )

        print("✅ Mancer SSH Backend import successful")
    except ImportError as e:
        print(f"❌ Mancer SSH Backend import failed: {e}")
        return False

    try:
        from mancer.domain.service.ssh_session_service import SSHSessionService

        print("✅ Mancer SSH Session Service import successful")
    except ImportError as e:
        print(f"❌ Mancer SSH Session Service import failed: {e}")
        return False

    return True


def main():
    """Główna funkcja testowa"""
    print("🧪 Testing Mancer Terminal GUI...")
    print("=" * 50)

    # Test importów GUI
    print("\n📱 Testing GUI imports:")
    gui_ok = test_imports()

    # Test integracji z Mancer
    print("\n🔌 Testing Mancer integration:")
    mancer_ok = test_mancer_integration()

    # Podsumowanie
    print("\n" + "=" * 50)
    if gui_ok and mancer_ok:
        print("🎉 All tests passed! Mancer Terminal is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
