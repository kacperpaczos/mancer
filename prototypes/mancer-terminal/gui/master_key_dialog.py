"""
Dialog ustawienia klucza głównego dla CredentialStore
"""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from mancer.domain.model.credential_store import CredentialStore


class MasterKeyDialog(QDialog):
    """Dialog ustawienia klucza głównego"""

    def __init__(self, credential_store: CredentialStore, parent=None):
        super().__init__(parent)
        self.credential_store = credential_store
        self.setWindowTitle("Ustawienie klucza głównego")
        self.setModal(True)
        self.setFixedSize(400, 200)

        self.init_ui()

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Nagłówek
        header = QLabel("Ustawienie klucza głównego")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Opis
        description = QLabel(
            "Klucz główny służy do szyfrowania haseł SSH.\n"
            "Zapamiętaj go - bez niego nie będzie można odczytać zapisanych haseł."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Formularz
        form_layout = QFormLayout()

        # Klucz główny
        self.master_key_edit = QLineEdit()
        self.master_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_key_edit.setPlaceholderText("Wprowadź klucz główny")
        form_layout.addRow("Klucz główny:", self.master_key_edit)

        # Potwierdzenie klucza
        self.confirm_key_edit = QLineEdit()
        self.confirm_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_key_edit.setPlaceholderText("Potwierdź klucz główny")
        form_layout.addRow("Potwierdzenie:", self.confirm_key_edit)

        # Pokaż klucz
        self.show_key_check = QCheckBox("Pokaż klucz")
        self.show_key_check.toggled.connect(self.toggle_key_visibility)
        form_layout.addRow("", self.show_key_check)

        layout.addLayout(form_layout)

        # Przyciski
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.set_key_btn = QPushButton("Ustaw klucz")
        self.set_key_btn.clicked.connect(self.set_master_key)
        button_layout.addWidget(self.set_key_btn)

        layout.addLayout(button_layout)

        # Połącz sygnały
        self.master_key_edit.textChanged.connect(self.validate_input)
        self.confirm_key_edit.textChanged.connect(self.validate_input)

    def toggle_key_visibility(self, show: bool):
        """Przełącza widoczność klucza"""
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.master_key_edit.setEchoMode(mode)
        self.confirm_key_edit.setEchoMode(mode)

    def validate_input(self):
        """Waliduje wprowadzone dane"""
        master_key = self.master_key_edit.text()
        confirm_key = self.confirm_key_edit.text()

        # Sprawdź długość klucza
        if len(master_key) < 8:
            self.set_key_btn.setEnabled(False)
            return

        # Sprawdź czy klucze są identyczne
        if master_key == confirm_key:
            self.set_key_btn.setEnabled(True)
        else:
            self.set_key_btn.setEnabled(False)

    def set_master_key(self):
        """Ustawia klucz główny"""
        master_key = self.master_key_edit.text()
        confirm_key = self.confirm_key_edit.text()

        # Sprawdź długość
        if len(master_key) < 8:
            QMessageBox.warning(self, "Ostrzeżenie", "Klucz musi mieć co najmniej 8 znaków")
            return

        # Sprawdź czy klucze są identyczne
        if master_key != confirm_key:
            QMessageBox.warning(self, "Błąd", "Klucze nie są identyczne")
            return

        try:
            # Ustaw klucz główny
            self.credential_store.set_master_key(master_key)

            QMessageBox.information(self, "Sukces", "Klucz główny został ustawiony")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się ustawić klucza: {e}")


class MasterKeyPromptDialog(QDialog):
    """Dialog wprowadzania klucza głównego"""

    def __init__(self, credential_store: CredentialStore, parent=None):
        super().__init__(parent)
        self.credential_store = credential_store
        self.setWindowTitle("Wprowadź klucz główny")
        self.setModal(True)
        self.setFixedSize(350, 150)

        self.init_ui()

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Opis
        description = QLabel("Wprowadź klucz główny aby odczytać zapisane hasła:")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Formularz
        form_layout = QFormLayout()

        # Klucz główny
        self.master_key_edit = QLineEdit()
        self.master_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.master_key_edit.setPlaceholderText("Wprowadź klucz główny")
        self.master_key_edit.returnPressed.connect(self.verify_key)
        form_layout.addRow("Klucz główny:", self.master_key_edit)

        layout.addLayout(form_layout)

        # Przyciski
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.verify_btn = QPushButton("Weryfikuj")
        self.verify_btn.clicked.connect(self.verify_key)
        button_layout.addWidget(self.verify_btn)

        layout.addLayout(button_layout)

        # Ustaw focus na pole klucza
        self.master_key_edit.setFocus()

    def verify_key(self):
        """Weryfikuje klucz główny"""
        master_key = self.master_key_edit.text()

        if not master_key:
            QMessageBox.warning(self, "Ostrzeżenie", "Wprowadź klucz główny")
            return

        try:
            # Ustaw klucz główny
            self.credential_store.set_master_key(master_key)

            # Sprawdź czy można odczytać poświadczenia
            credentials = self.credential_store.list_credentials()
            if credentials:
                # Spróbuj odczytać pierwsze poświadczenie
                first_cred = credentials[0]
                password = self.credential_store.get_password(first_cred.profile_id)
                if password is not None:
                    QMessageBox.information(self, "Sukces", "Klucz główny został zweryfikowany")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Błąd", "Nieprawidłowy klucz główny")
            else:
                # Brak poświadczeń - klucz jest poprawny
                QMessageBox.information(self, "Sukces", "Klucz główny został zweryfikowany")
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd weryfikacji klucza: {e}")
