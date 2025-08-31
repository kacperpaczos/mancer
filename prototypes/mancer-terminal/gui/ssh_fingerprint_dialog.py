"""
Dialog obsługi fingerprintów SSH
"""

from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class SSHFingerprintDialog(QDialog):
    """Dialog do obsługi fingerprintów SSH"""

    def __init__(
        self,
        hostname: str,
        port: int,
        fingerprint: str,
        key_type: str = "ED25519",
        timeout_seconds: int = 60,
        parent=None,
    ):
        super().__init__(parent)
        self.hostname = hostname
        self.port = port
        self.fingerprint = fingerprint
        self.key_type = key_type
        self.accepted = False
        self.save_permanently = False
        self.timeout_seconds = max(5, int(timeout_seconds))

        self.setWindowTitle("Weryfikacja klucza SSH")
        self.setModal(True)
        self.setFixedSize(600, 400)

        self.init_ui()
        self._init_timer()

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Nagłówek z ikoną ostrzeżenia
        header_layout = QHBoxLayout()

        # Ikona ostrzeżenia
        warning_label = QLabel("⚠️")
        warning_label.setFont(QFont("Arial", 24))
        header_layout.addWidget(warning_label)

        # Tytuł
        title_label = QLabel("Nieznany klucz hosta SSH")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Opis problemu
        description = QLabel(
            f"Autentyczność hosta '{self.hostname}' nie może zostać potwierdzona.\n"
            f"Klucz {self.key_type} nie jest znany w żadnej innej nazwie."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Fingerprint
        fingerprint_layout = QVBoxLayout()

        fingerprint_label = QLabel("Fingerprint klucza:")
        fingerprint_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        fingerprint_layout.addWidget(fingerprint_label)

        self.fingerprint_display = QTextEdit()
        self.fingerprint_display.setPlainText(
            f"{self.key_type} key fingerprint is {self.fingerprint}"
        )
        self.fingerprint_display.setMaximumHeight(60)
        self.fingerprint_display.setReadOnly(True)
        self.fingerprint_display.setFont(QFont("Courier", 10))
        fingerprint_layout.addWidget(self.fingerprint_display)

        layout.addLayout(fingerprint_layout)

        # Pytanie
        self.question_label = QLabel("Czy na pewno chcesz kontynuować połączenie?")
        self.question_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.question_label)

        # Licznik czasu
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        layout.addWidget(self.timer_label)

        # Checkbox do zapisania na stałe
        self.save_checkbox = QCheckBox(
            "Zapisz ten klucz na stałe (dodaj do known_hosts)"
        )
        self.save_checkbox.setChecked(True)
        layout.addWidget(self.save_checkbox)

        # Informacja bezpieczeństwa
        security_info = QLabel(
            "⚠️ UWAGA: Akceptuj tylko jeśli jesteś pewien, że łączysz się z właściwym serwerem!\n"
            "Nieprawidłowe klucze mogą oznaczać atak man-in-the-middle."
        )
        security_info.setWordWrap(True)
        security_info.setStyleSheet(
            "color: #d32f2f; background-color: #ffebee; padding: 10px; border-radius: 5px;"
        )
        layout.addWidget(security_info)

        # Przyciski
        button_layout = QHBoxLayout()

        # Przycisk odrzuć
        self.reject_btn = QPushButton("Odrzuć połączenie")
        self.reject_btn.clicked.connect(self.reject_connection)
        self.reject_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; }"
        )
        button_layout.addWidget(self.reject_btn)

        button_layout.addStretch()

        # Przycisk akceptuj jednorazowo
        self.accept_once_btn = QPushButton("Akceptuj jednorazowo")
        self.accept_once_btn.clicked.connect(self.accept_once)
        self.accept_once_btn.setStyleSheet(
            "QPushButton { background-color: #ff9800; color: white; }"
        )
        button_layout.addWidget(self.accept_once_btn)

        # Przycisk akceptuj na stałe
        self.accept_permanent_btn = QPushButton("Akceptuj i zapisz")
        self.accept_permanent_btn.clicked.connect(self.accept_permanent)
        self.accept_permanent_btn.setStyleSheet(
            "QPushButton { background-color: #4caf50; color: white; }"
        )
        button_layout.addWidget(self.accept_permanent_btn)

        layout.addLayout(button_layout)

        # Informacja o lokalizacji known_hosts
        import os

        known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
        info_label = QLabel(f"Klucze są zapisywane w: {known_hosts_path}")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(info_label)

    def _init_timer(self):
        """Inicjalizuje licznik odliczający decyzję użytkownika"""
        self._remaining = self.timeout_seconds
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._update_timer_label()
        self._timer.start()

    def _on_tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            # Auto-odrzuć po czasie
            self.reject_connection()
            return
        self._update_timer_label()

    def _update_timer_label(self):
        self.timer_label.setText(
            f"Pozostały czas na podjęcie decyzji: {self._remaining}s"
        )

    def reject_connection(self):
        """Odrzuca połączenie"""
        self.accepted = False
        self.save_permanently = False
        self.reject()

    def accept_once(self):
        """Akceptuje połączenie jednorazowo"""
        self.accepted = True
        self.save_permanently = False
        self.accept()

    def accept_permanent(self):
        """Akceptuje połączenie i zapisuje klucz na stałe"""
        self.accepted = True
        self.save_permanently = self.save_checkbox.isChecked()
        self.accept()

    def get_result(self) -> tuple[bool, bool]:
        """Zwraca wynik dialogu (accepted, save_permanently)"""
        return self.accepted, self.save_permanently


class SSHHostKeyManager:
    """Zarządza kluczami hostów SSH"""

    def __init__(self):
        import os

        self.known_hosts_file = os.path.expanduser("~/.ssh/known_hosts")
        self.ensure_ssh_dir()

    def ensure_ssh_dir(self):
        """Upewnia się, że katalog ~/.ssh istnieje"""
        import os

        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700)

    def is_host_known(self, hostname: str, port: int = 22) -> bool:
        """Sprawdza czy host jest znany w known_hosts"""
        try:
            import os

            if not os.path.exists(self.known_hosts_file):
                return False

            host_entry = f"[{hostname}]:{port}" if port != 22 else hostname

            with open(self.known_hosts_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == host_entry:
                            return True

            return False
        except Exception:
            return False

    def add_host_key(
        self, hostname: str, port: int, key_type: str, key_data: str
    ) -> bool:
        """Dodaje klucz hosta do known_hosts"""
        try:
            host_entry = f"[{hostname}]:{port}" if port != 22 else hostname
            key_line = f"{host_entry} {key_type} {key_data}\n"

            with open(self.known_hosts_file, "a") as f:
                f.write(key_line)

            # Ustaw odpowiednie uprawnienia
            import os

            os.chmod(self.known_hosts_file, 0o600)

            return True
        except Exception as e:
            print(f"Błąd dodawania klucza hosta: {e}")
            return False

    def extract_fingerprint_from_error(
        self, error_message: str
    ) -> Optional[tuple[str, str]]:
        """Wyciąga fingerprint z komunikatu błędu SSH"""
        import re

        # Wzorzec dla fingerprinta w formacie SHA256
        sha256_pattern = r"(\w+) key fingerprint is (SHA256:[A-Za-z0-9+/=]+)"
        match = re.search(sha256_pattern, error_message)

        if match:
            key_type = match.group(1)
            fingerprint = match.group(2)
            return key_type, fingerprint

        return None
