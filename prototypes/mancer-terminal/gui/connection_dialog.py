"""
Dialog konfiguracji połączenia SSH
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ConnectionDialog(QDialog):
    """Dialog konfiguracji połączenia SSH"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nowa Sesja SSH")
        self.setModal(True)
        self.setFixedSize(500, 600)

        # Dane połączenia
        self.connection_data = {}

        # Inicjalizacja UI
        self.init_ui()

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Zakładki
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Zakładka podstawowa
        basic_tab = self.create_basic_tab()
        tabs.addTab(basic_tab, "Podstawowe")

        # Zakładka uwierzytelniania
        auth_tab = self.create_auth_tab()
        tabs.addTab(auth_tab, "Uwierzytelnianie")

        # Zakładka proxy
        proxy_tab = self.create_proxy_tab()
        tabs.addTab(proxy_tab, "Proxy")

        # Zakładka zaawansowane
        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "Zaawansowane")

        # Przyciski
        button_layout = QHBoxLayout()

        self.parse_ssh_btn = QPushButton("Parsuj Komendę SSH")
        self.parse_ssh_btn.clicked.connect(self.parse_ssh_command)
        button_layout.addWidget(self.parse_ssh_btn)

        self.test_btn = QPushButton("Test Połączenia")
        self.test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.connect_btn)

        layout.addLayout(button_layout)

    def create_basic_tab(self):
        """Tworzy zakładkę podstawową"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Komenda SSH (alternatywa do pól poniżej)
        self.ssh_command_edit = QLineEdit()
        self.ssh_command_edit.setPlaceholderText("np. ssh -p 2222 user@192.168.1.100")
        layout.addRow("Komenda SSH:", self.ssh_command_edit)

        # Separator
        separator1 = QLabel("─" * 50)
        separator1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator1)

        # Hostname
        self.hostname_edit = QLineEdit()
        self.hostname_edit.setText("127.0.0.1")  # Domyślna wartość
        self.hostname_edit.setPlaceholderText("np. 192.168.1.100 lub server.example.com")
        layout.addRow("Hostname:", self.hostname_edit)

        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        layout.addRow("Port:", self.port_spin)

        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setText("pyroxar")  # Domyślna wartość
        self.username_edit.setPlaceholderText("np. admin lub root")
        layout.addRow("Username:", self.username_edit)
        layout.addRow("Port:", self.port_spin)

        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setText("pyroxar")  # Domyślna wartość
        self.username_edit.setPlaceholderText("np. admin")
        layout.addRow("Użytkownik:", self.username_edit)

        # Nazwa sesji
        self.session_name_edit = QLineEdit()
        self.session_name_edit.setPlaceholderText("Opcjonalna nazwa sesji")
        layout.addRow("Nazwa sesji:", self.session_name_edit)

        return widget

    def create_auth_tab(self):
        """Tworzy zakładkę uwierzytelniania"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Metoda uwierzytelniania
        self.auth_method_group = QGroupBox("Metoda uwierzytelniania")
        auth_layout = QVBoxLayout(self.auth_method_group)

        self.key_auth_checkbox = QCheckBox("Użyj klucza prywatnego")
        self.key_auth_checkbox.toggled.connect(self.on_auth_method_changed)
        auth_layout.addWidget(self.key_auth_checkbox)

        self.password_auth_checkbox = QCheckBox("Użyj hasła")
        self.password_auth_checkbox.toggled.connect(self.on_auth_method_changed)
        auth_layout.addWidget(self.password_auth_checkbox)

        layout.addRow(self.auth_method_group)

        # Ścieżka do klucza
        key_layout = QHBoxLayout()
        self.key_path_edit = QLineEdit()
        self.key_path_edit.setPlaceholderText("Ścieżka do klucza prywatnego")
        self.key_path_edit.setEnabled(False)
        key_layout.addWidget(self.key_path_edit)

        self.browse_key_btn = QPushButton("Przeglądaj")
        self.browse_key_btn.clicked.connect(self.browse_key_file)
        self.browse_key_btn.setEnabled(False)
        key_layout.addWidget(self.browse_key_btn)

        layout.addRow("Klucz prywatny:", key_layout)

        # Hasło
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Hasło SSH")
        self.password_edit.setEnabled(False)
        layout.addRow("Hasło:", self.password_edit)

        # Passphrase dla klucza
        self.passphrase_edit = QLineEdit()
        self.passphrase_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase_edit.setPlaceholderText("Passphrase dla klucza (jeśli wymagane)")
        self.passphrase_edit.setEnabled(False)
        layout.addRow("Passphrase:", self.passphrase_edit)

        # Opcje uwierzytelniania
        self.allow_agent_checkbox = QCheckBox("Użyj SSH agent")
        self.allow_agent_checkbox.setChecked(True)
        layout.addRow(self.allow_agent_checkbox)

        self.look_for_keys_checkbox = QCheckBox("Szukaj kluczy w ~/.ssh")
        self.look_for_keys_checkbox.setChecked(True)
        layout.addRow(self.look_for_keys_checkbox)

        # Zapisz hasło
        self.save_password_checkbox = QCheckBox("Zapisz hasło (szyfrowane)")
        self.save_password_checkbox.setChecked(False)
        layout.addRow(self.save_password_checkbox)

        return widget

    def create_proxy_tab(self):
        """Tworzy zakładkę proxy"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Użyj proxy
        self.use_proxy_checkbox = QCheckBox("Użyj proxy SSH")
        self.use_proxy_checkbox.toggled.connect(self.on_proxy_toggled)
        layout.addRow(self.use_proxy_checkbox)

        # Typ proxy
        self.proxy_type_group = QGroupBox("Typ proxy")
        proxy_type_layout = QVBoxLayout(self.proxy_type_group)

        self.http_proxy_radio = QCheckBox("HTTP Proxy")
        self.http_proxy_radio.setChecked(True)
        proxy_type_layout.addWidget(self.http_proxy_radio)

        self.socks_proxy_radio = QCheckBox("SOCKS Proxy")
        proxy_type_layout.addWidget(self.socks_proxy_radio)

        self.proxy_command_radio = QCheckBox("Proxy Command")
        proxy_type_layout.addWidget(self.proxy_command_radio)

        layout.addRow(self.proxy_type_group)

        # Konfiguracja proxy
        proxy_config_group = QGroupBox("Konfiguracja proxy")
        proxy_config_layout = QFormLayout(proxy_config_group)

        # Host proxy
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText("np. proxy.company.com")
        self.proxy_host_edit.setEnabled(False)
        proxy_config_layout.addRow("Host proxy:", self.proxy_host_edit)

        # Port proxy
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        self.proxy_port_spin.setEnabled(False)
        proxy_config_layout.addRow("Port proxy:", self.proxy_port_spin)

        # Użytkownik proxy
        self.proxy_user_edit = QLineEdit()
        self.proxy_user_edit.setPlaceholderText("Użytkownik proxy (jeśli wymagane)")
        self.proxy_user_edit.setEnabled(False)
        proxy_config_layout.addRow("Użytkownik proxy:", self.proxy_user_edit)

        # Hasło proxy
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.proxy_password_edit.setPlaceholderText("Hasło proxy (jeśli wymagane)")
        self.proxy_password_edit.setEnabled(False)
        proxy_config_layout.addRow("Hasło proxy:", self.proxy_password_edit)

        # Proxy command
        self.proxy_command_edit = QLineEdit()
        self.proxy_command_edit.setPlaceholderText("np. nc -X connect -x proxy:8080 %h %p")
        self.proxy_command_edit.setEnabled(False)
        proxy_config_layout.addRow("Proxy command:", self.proxy_command_edit)

        layout.addRow(proxy_config_group)

        return widget

    def create_advanced_tab(self):
        """Tworzy zakładkę zaawansowane"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" sekund")
        layout.addRow("Timeout połączenia:", self.timeout_spin)

        # Kompresja
        self.compress_checkbox = QCheckBox("Włącz kompresję")
        layout.addRow(self.compress_checkbox)

        # GSSAPI
        self.gssapi_group = QGroupBox("GSSAPI (Kerberos)")
        gssapi_layout = QVBoxLayout(self.gssapi_group)

        self.gssapi_auth_checkbox = QCheckBox("Uwierzytelnianie GSSAPI")
        gssapi_layout.addWidget(self.gssapi_auth_checkbox)

        self.gssapi_kex_checkbox = QCheckBox("Wymiana kluczy GSSAPI")
        gssapi_layout.addWidget(self.gssapi_kex_checkbox)

        self.gssapi_delegate_checkbox = QCheckBox("Delegowanie poświadczeń GSSAPI")
        gssapi_layout.addWidget(self.gssapi_delegate_checkbox)

        layout.addRow(self.gssapi_group)

        # Dodatkowe opcje SSH
        self.ssh_options_edit = QTextEdit()
        self.ssh_options_edit.setPlaceholderText(
            "Dodatkowe opcje SSH (jedna na linię)\nnp. StrictHostKeyChecking=no\nBatchMode=yes"
        )
        self.ssh_options_edit.setMaximumHeight(100)
        layout.addRow("Dodatkowe opcje SSH:", self.ssh_options_edit)

        return widget

    def on_auth_method_changed(self):
        """Obsługuje zmianę metody uwierzytelniania"""
        # Klucz prywatny
        key_enabled = self.key_auth_checkbox.isChecked()
        self.key_path_edit.setEnabled(key_enabled)
        self.browse_key_btn.setEnabled(key_enabled)
        self.passphrase_edit.setEnabled(key_enabled)

        # Hasło
        password_enabled = self.password_auth_checkbox.isChecked()
        self.password_edit.setEnabled(password_enabled)

    def on_proxy_toggled(self, enabled: bool):
        """Obsługuje włączenie/wyłączenie proxy"""
        self.proxy_host_edit.setEnabled(enabled)
        self.proxy_port_spin.setEnabled(enabled)
        self.proxy_user_edit.setEnabled(enabled)
        self.proxy_password_edit.setEnabled(enabled)
        self.proxy_command_edit.setEnabled(enabled)

    def browse_key_file(self):
        """Przegląda pliki kluczy"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz klucz prywatny",
            os.path.expanduser("~/.ssh"),
            "Klucze SSH (*.pem *.key *.id_rsa);;Wszystkie pliki (*)",
        )

        if file_path:
            self.key_path_edit.setText(file_path)

    def test_connection(self):
        """Testuje połączenie SSH"""
        # Pobierz dane połączenia
        connection_data = self.get_connection_data()

        if not connection_data:
            return

        # Tutaj można dodać test połączenia
        # Na razie pokazujemy informację
        QMessageBox.information(
            self,
            "Test połączenia",
            f"Test połączenia z {connection_data['hostname']}:{connection_data['port']}\n"
            f"Użytkownik: {connection_data['username']}\n\n"
            "Funkcja testowania będzie dostępna w przyszłych wersjach.",
        )

    def parse_ssh_command(self):
        """Parsuje komendę SSH i wypełnia pola"""
        try:
            from ..utils.ssh_command_parser import SSHCommandParser

            command = self.ssh_command_edit.text().strip()
            if not command:
                QMessageBox.warning(self, "Błąd", "Wprowadź komendę SSH!")
                return

            parser = SSHCommandParser()
            params = parser.parse_ssh_command(command)

            # Wypełnij pola
            if params.hostname:
                self.hostname_edit.setText(params.hostname)
            if params.username:
                self.username_edit.setText(params.username)
            if params.port != 22:
                self.port_spin.setValue(params.port)
            if params.key_filename:
                self.key_path_edit.setText(params.key_filename)

            QMessageBox.information(self, "Sukces", "Komenda SSH została sparsowana!")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd parsowania komendy SSH: {str(e)}")

    def get_connection_data(self) -> dict:
        """Pobiera dane połączenia z formularza"""
        # Sprawdź wymagane pola
        hostname = self.hostname_edit.text().strip()
        username = self.username_edit.text().strip()

        if not hostname:
            QMessageBox.warning(self, "Błąd", "Pole Hostname jest wymagane")
            return None

        if not username:
            QMessageBox.warning(self, "Błąd", "Pole Użytkownik jest wymagane")
            return None

        # Podstawowe dane
        data = {
            "hostname": hostname,
            "port": self.port_spin.value(),
            "username": username,
            "session_name": self.session_name_edit.text().strip(),
        }

        # Uwierzytelnianie
        if self.key_auth_checkbox.isChecked():
            data["key_filename"] = self.key_path_edit.text().strip()
            if self.passphrase_edit.text().strip():
                data["passphrase"] = self.passphrase_edit.text().strip()

        if self.password_auth_checkbox.isChecked():
            data["password"] = self.password_edit.text()

        # Opcje uwierzytelniania
        data["allow_agent"] = self.allow_agent_checkbox.isChecked()
        data["look_for_keys"] = self.look_for_keys_checkbox.isChecked()

        # Zapisz hasło
        data["save_password"] = self.save_password_checkbox.isChecked()

        # Proxy
        if self.use_proxy_checkbox.isChecked():
            proxy_config = {}

            if self.proxy_command_radio.isChecked():
                proxy_config["proxy_command"] = self.proxy_command_edit.text().strip()
            else:
                proxy_config["proxy_host"] = self.proxy_host_edit.text().strip()
                proxy_config["proxy_port"] = self.proxy_port_spin.value()

                if self.proxy_user_edit.text().strip():
                    proxy_config["proxy_user"] = self.proxy_user_edit.text().strip()

                if self.proxy_password_edit.text():
                    proxy_config["proxy_password"] = self.proxy_password_edit.text()

            data["proxy_config"] = proxy_config

        # Zaawansowane opcje
        data["timeout"] = self.timeout_spin.value()
        data["compress"] = self.compress_checkbox.isChecked()
        data["gssapi_auth"] = self.gssapi_auth_checkbox.isChecked()
        data["gssapi_kex"] = self.gssapi_kex_checkbox.isChecked()
        data["gssapi_delegate_creds"] = self.gssapi_delegate_checkbox.isChecked()

        # Dodatkowe opcje SSH
        ssh_options_text = self.ssh_options_edit.toPlainText().strip()
        if ssh_options_text:
            ssh_options = {}
            for line in ssh_options_text.split("\n"):
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    ssh_options[key.strip()] = value.strip()
            data["ssh_options"] = ssh_options

        return data

    def accept(self):
        """Obsługuje akceptację dialogu"""
        connection_data = self.get_connection_data()
        if connection_data:
            self.connection_data = connection_data
            super().accept()
        else:
            # Dane są nieprawidłowe, nie zamykaj dialogu
            pass
