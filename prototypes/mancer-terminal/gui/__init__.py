"""
Pakiet GUI dla Mancer Terminal
"""

try:
    from .connection_dialog import ConnectionDialog
    from .file_transfer_widget import FileTransferWidget
    from .main_window import MancerTerminalWindow
    from .master_key_dialog import MasterKeyDialog, MasterKeyPromptDialog
    from .profile_manager_widget import ProfileManagerWidget
    from .session_manager_widget import SessionManagerWidget
    from .ssh_fingerprint_dialog import SSHFingerprintDialog, SSHHostKeyManager
    from .terminal_widget import TerminalWidget

    __all__ = [
        "MancerTerminalWindow",
        "TerminalWidget",
        "SessionManagerWidget",
        "FileTransferWidget",
        "ConnectionDialog",
        "ProfileManagerWidget",
        "MasterKeyDialog",
        "MasterKeyPromptDialog",
        "SSHFingerprintDialog",
        "SSHHostKeyManager",
    ]
except ImportError as e:
    # Jeśli import się nie powiedzie, eksportuj tylko podstawowe informacje
    __all__ = []
    print(f"Warning: Could not import GUI components: {e}")
