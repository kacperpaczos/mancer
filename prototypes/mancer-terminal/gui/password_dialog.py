"""
Dialog wprowadzania hasła SSH
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class PasswordDialog(QDialog):
    """Dialog wprowadzania hasła SSH"""

    def __init__(self, hostname: str, username: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hasło SSH")
        self.setModal(True)
        self.setFixedSize(400, 200)

        self.hostname = hostname
        self.username = username
        self.password = ""

        self.init_ui()

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Informacja o połączeniu
        info_label = QLabel(f"Połączenie z: {self.username}@{self.hostname}")
        info_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Separator
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator)

        # Formularz
        form_layout = QFormLayout()

        # Hasło
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Wprowadź hasło")
        self.password_edit.returnPressed.connect(self.accept_password)
        form_layout.addRow("Hasło:", self.password_edit)

        layout.addLayout(form_layout)

        # Przyciski
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.accept_password)
        button_layout.addWidget(self.connect_btn)

        layout.addLayout(button_layout)

        # Ustaw focus na pole hasła
        self.password_edit.setFocus()

    def accept_password(self):
        """Akceptuje hasło i zamyka dialog"""
        self.password = self.password_edit.text()
        if self.password:
            self.accept()
        else:
            QMessageBox.warning(self, "Błąd", "Wprowadź hasło!")

    def get_password(self) -> str:
        """Zwraca wprowadzone hasło"""
        return self.password
