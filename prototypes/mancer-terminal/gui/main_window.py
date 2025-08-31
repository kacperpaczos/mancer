"""
Główne okno aplikacji Mancer Terminal
"""

import os
import queue
import threading
import uuid
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import yaml
from PyQt6.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .connection_dialog import ConnectionDialog
from .file_transfer_widget import FileTransferWidget
from .profile_manager_widget import ProfileManagerWidget
from .session_manager_widget import SessionManagerWidget
from .terminal_widget import TerminalWidget


class MancerTerminalWindow(QMainWindow):
    """Główne okno aplikacji Mancer Terminal"""

    # Sygnał do wyświetlenia dialogu fingerprint w głównym wątku
    fingerprint_request = pyqtSignal(str, int, str, int, object)
    # Sygnał do wyświetlenia dialogu hasła w głównym wątku
    password_request = pyqtSignal(str, str, object)
    # Sygnały wyniku tworzenia sesji
    session_created = pyqtSignal(str)
    session_creation_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mancer Terminal - SSH Terminal Emulator")
        self.setGeometry(100, 100, 1400, 900)

        # Inicjalizacja loggera
        self.setup_logger()

        # Inicjalizacja UI
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()

        # Połączenie sygnału fingerprint do slotu obsługującego w głównym wątku
        self.fingerprint_request.connect(self._on_fingerprint_request)
        # Połączenie sygnału hasła do slotu obsługującego w głównym wątku
        self.password_request.connect(self._on_password_request)
        # Połączenie sygnałów tworzenia sesji
        self.session_created.connect(self._on_session_created)
        self.session_creation_failed.connect(self._on_session_creation_failed)

        # Załaduj konfigurację terminala
        self.gui_config = self._load_terminal_config()
        if hasattr(self, "logger") and self.logger:
            self.logger.info("Terminal config loaded for GUI")

    def _load_terminal_config(self) -> dict:
        """Ładuje konfigurację terminala z pliku YAML; zwraca pusty dict w razie błędu"""
        try:
            cfg_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "config", "terminal.yaml"
            )
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data
        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Nie udało się załadować terminal.yaml: {e}")
            return {}

    def setup_logger(self):
        """Konfiguruje logger dla głównego okna"""
        try:
            from mancer.infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
            self.logger.info("MancerTerminalWindow - inicjalizacja")
        except Exception as e:
            print(f"Błąd konfiguracji loggera: {e}")
            self.logger = None

        # Timer do aktualizacji statusu
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Aktualizuj co sekundę

    def init_ui(self):
        """Inicjalizuje główny interfejs użytkownika"""
        # Centralny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Główny layout
        main_layout = QHBoxLayout(central_widget)

        # Splitter dla lewej i prawej strony
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Lewa strona - Panel sesji i transferów
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Prawa strona - Terminal i zakładki
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Ustaw proporcje splittera
        splitter.setSizes([400, 1000])

    def create_left_panel(self):
        """Tworzy lewy panel z sesjami i transferami"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Manager sesji
        self.session_manager = SessionManagerWidget()
        left_layout.addWidget(self.session_manager)

        # Manager transferów plików
        self.file_transfer = FileTransferWidget()
        left_layout.addWidget(self.file_transfer)

        # Połącz sygnały
        self.session_manager.session_selected.connect(self.on_session_selected)
        self.session_manager.new_session_requested.connect(
            self.on_new_session_requested
        )

        return left_widget

    def create_right_panel(self):
        """Tworzy prawy panel z terminalem"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Zakładki terminali
        self.terminal_tabs = QTabWidget()
        self.terminal_tabs.setTabsClosable(True)
        self.terminal_tabs.tabCloseRequested.connect(self.close_terminal_tab)
        right_layout.addWidget(self.terminal_tabs)

        # Dodaj zakładkę "Profile" na początku
        self.profile_tab = QWidget()
        profile_layout = QVBoxLayout(self.profile_tab)

        # Widget zarządzania profilami
        self.profile_manager = ProfileManagerWidget()
        profile_layout.addWidget(self.profile_manager)

        # Połącz sygnał wyboru profilu
        self.profile_manager.profile_selected.connect(self.on_profile_selected)

        # Dodaj zakładkę Profile
        self.terminal_tabs.insertTab(0, self.profile_tab, "Profile")

        # Przyciski kontrolne
        control_layout = QHBoxLayout()

        self.new_terminal_btn = QPushButton("Nowy Terminal")
        self.new_terminal_btn.clicked.connect(self.create_new_terminal)
        control_layout.addWidget(self.new_terminal_btn)

        self.clear_btn = QPushButton("Wyczyść")
        self.clear_btn.clicked.connect(self.clear_current_terminal)
        control_layout.addWidget(self.clear_btn)

        control_layout.addStretch()
        right_layout.addLayout(control_layout)

        return right_widget

    def init_menu(self):
        """Inicjalizuje menu główne"""
        menubar = self.menuBar()

        # Menu Plik
        file_menu = menubar.addMenu("&Plik")

        new_session_action = QAction("&Nowa Sesja SSH", self)
        new_session_action.setShortcut(QKeySequence.StandardKey.New)
        new_session_action.triggered.connect(self.on_new_session_requested)
        file_menu.addAction(new_session_action)

        file_menu.addSeparator()

        exit_action = QAction("&Wyjście", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menu Sesja
        session_menu = menubar.addMenu("&Sesja")

        connect_action = QAction("&Połącz", self)
        connect_action.setShortcut("Ctrl+Shift+C")
        connect_action.triggered.connect(self.on_new_session_requested)
        session_menu.addAction(connect_action)

        disconnect_action = QAction("&Rozłącz", self)
        disconnect_action.setShortcut("Ctrl+Shift+D")
        disconnect_action.triggered.connect(self.disconnect_current_session)
        session_menu.addAction(disconnect_action)

        # Menu Transfer
        transfer_menu = menubar.addMenu("&Transfer")

        upload_action = QAction("&Upload Pliku", self)
        upload_action.setShortcut("Ctrl+Shift+U")
        upload_action.triggered.connect(self.upload_file)
        transfer_menu.addAction(upload_action)

        download_action = QAction("&Download Pliku", self)
        download_action.setShortcut("Ctrl+Shift+L")
        download_action.triggered.connect(self.download_file)
        transfer_menu.addAction(download_action)

        # Menu Profile
        profile_menu = menubar.addMenu("&Profile")

        master_key_action = QAction("&Ustaw klucz główny", self)
        master_key_action.triggered.connect(self.set_master_key)
        profile_menu.addAction(master_key_action)

        verify_key_action = QAction("&Weryfikuj klucz główny", self)
        verify_key_action.triggered.connect(self.verify_master_key)
        profile_menu.addAction(verify_key_action)

        # Menu Pomoc
        help_menu = menubar.addMenu("&Pomoc")

        about_action = QAction("&O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def init_toolbar(self):
        """Inicjalizuje pasek narzędzi"""
        toolbar = self.addToolBar("Główne narzędzia")

        # Nowa sesja
        new_session_action = QAction("Nowa Sesja", self)
        new_session_action.triggered.connect(self.on_new_session_requested)
        toolbar.addAction(new_session_action)

        toolbar.addSeparator()

        # Upload/Download
        upload_action = QAction("Upload", self)
        upload_action.triggered.connect(self.upload_file)
        toolbar.addAction(upload_action)

        download_action = QAction("Download", self)
        download_action.triggered.connect(self.download_file)
        toolbar.addAction(download_action)

    def init_statusbar(self):
        """Inicjalizuje pasek statusu"""
        self.statusbar = self.statusBar()

        # Status połączenia
        self.connection_status = QLabel("Brak połączenia")
        self.statusbar.addWidget(self.connection_status)

        self.statusbar.addPermanentWidget(QLabel("|"))

        # Liczba sesji
        self.sessions_count = QLabel("Sesje: 0")
        self.statusbar.addPermanentWidget(self.sessions_count)

        self.statusbar.addPermanentWidget(QLabel("|"))

        # Liczba transferów
        self.transfers_count = QLabel("Transfery: 0")
        self.statusbar.addPermanentWidget(self.transfers_count)

    def update_status(self):
        """Aktualizuje status w pasku statusu"""
        # Aktualizuj liczbę sesji
        sessions = self.session_manager.get_sessions_count()
        self.sessions_count.setText(f"Sesje: {sessions}")

        # Aktualizuj liczbę transferów
        transfers = self.file_transfer.get_transfers_count()
        self.transfers_count.setText(f"Transfery: {transfers}")

        # Aktualizuj status połączenia
        active_session = self.session_manager.get_active_session()
        if active_session:
            self.connection_status.setText(f"Połączony: {active_session}")
        else:
            self.connection_status.setText("Brak połączenia")

    def on_new_session_requested(self):
        """Obsługuje żądanie nowej sesji"""
        try:
            if self.logger:
                self.logger.info("Użytkownik żąda nowej sesji SSH")

            dialog = ConnectionDialog(self)
            if dialog.exec():
                # Pobierz dane połączenia
                connection_data = dialog.get_connection_data()

                if self.logger:
                    self.logger.info(
                        f"Tworzenie sesji SSH: {connection_data['username']}@{connection_data['hostname']}:{connection_data['port']}"
                    )

                # Użyj wspólnej metody do tworzenia sesji (z obsługą fingerprinta)
                self.create_session_from_data(connection_data)
            else:
                if self.logger:
                    self.logger.info("Użytkownik anulował tworzenie sesji")

        except Exception as e:
            error_msg = f"Błąd podczas tworzenia sesji: {e}"
            if self.logger:
                self.logger.error(error_msg)
            QMessageBox.critical(self, "Błąd", error_msg)

    def request_password(self, hostname: str, username: str) -> str:
        """Wyświetla okno hasła i zwraca wprowadzone hasło"""
        try:
            if self.logger:
                self.logger.info(f"Wyświetlanie okna hasła dla {username}@{hostname}")

            from .password_dialog import PasswordDialog

            dialog = PasswordDialog(hostname, username, self)
            if dialog.exec():
                password = dialog.get_password()
                if self.logger:
                    self.logger.info(f"Hasło wprowadzone dla {username}@{hostname}")
                return password
            else:
                if self.logger:
                    self.logger.info(
                        f"Użytkownik anulował wprowadzanie hasła dla {username}@{hostname}"
                    )
                return ""

        except Exception as e:
            error_msg = f"Błąd okna hasła dla {username}@{hostname}: {e}"
            if self.logger:
                self.logger.error(error_msg)
            return ""

    def on_session_selected(self, session_id: str):
        """Obsługuje wybór sesji"""
        # Przełącz na terminal dla tej sesji
        self.switch_to_terminal(session_id)

    def create_terminal_for_session(self, session_id: str):
        """Tworzy nowy terminal dla sesji"""
        # Przekaż SSH service do terminala
        terminal = TerminalWidget(session_id, self.session_manager.ssh_service)

        # Dodaj do zakładek
        tab_index = self.terminal_tabs.addTab(terminal, f"Terminal {session_id[:8]}")

        # Przełącz na nową zakładkę
        self.terminal_tabs.setCurrentIndex(tab_index)

        # Połącz sygnały
        terminal.session_closed.connect(lambda: self.on_terminal_closed(session_id))

    def switch_to_terminal(self, session_id: str):
        """Przełącza na terminal dla danej sesji"""
        for i in range(self.terminal_tabs.count()):
            terminal = self.terminal_tabs.widget(i)
            if hasattr(terminal, "session_id") and terminal.session_id == session_id:
                self.terminal_tabs.setCurrentIndex(i)
                return

    def create_new_terminal(self):
        """Tworzy nowy terminal"""
        active_session = self.session_manager.get_active_session()
        if active_session:
            self.create_terminal_for_session(active_session)
        else:
            QMessageBox.warning(self, "Ostrzeżenie", "Brak aktywnej sesji")

    def clear_current_terminal(self):
        """Czyści aktualny terminal"""
        current_terminal = self.terminal_tabs.currentWidget()
        if current_terminal and hasattr(current_terminal, "clear"):
            current_terminal.clear()

    def close_terminal_tab(self, index: int):
        """Zamyka zakładkę terminala"""
        terminal = self.terminal_tabs.widget(index)
        if terminal and hasattr(terminal, "close_session"):
            terminal.close_session()

        self.terminal_tabs.removeTab(index)

    def on_terminal_closed(self, session_id: str):
        """Obsługuje zamknięcie terminala"""
        # Usuń sesję
        self.session_manager.close_session(session_id)

    def disconnect_current_session(self):
        """Rozłącza aktualną sesję"""
        active_session = self.session_manager.get_active_session()
        if active_session:
            self.session_manager.disconnect_session(active_session)

    def upload_file(self):
        """Upload pliku"""
        active_session = self.session_manager.get_active_session()
        if not active_session:
            QMessageBox.warning(self, "Ostrzeżenie", "Brak aktywnej sesji")
            return

        # Wybierz plik lokalny
        local_file, _ = QFileDialog.getOpenFileName(self, "Wybierz plik do upload")
        if not local_file:
            return

        # Pobierz ścieżkę zdalną
        remote_path, ok = QInputDialog.getText(
            self, "Ścieżka zdalna", "Podaj ścieżkę zdalną:"
        )
        if not ok or not remote_path:
            return

        # Rozpocznij upload
        self.file_transfer.start_upload(active_session, local_file, remote_path)

    def download_file(self):
        """Download pliku"""
        active_session = self.session_manager.get_active_session()
        if not active_session:
            QMessageBox.warning(self, "Ostrzeżenie", "Brak aktywnej sesji")
            return

        # Pobierz ścieżkę zdalną
        remote_path, ok = QInputDialog.getText(
            self, "Ścieżka zdalna", "Podaj ścieżkę zdalną:"
        )
        if not ok or not remote_path:
            return

        # Wybierz lokalizację
        local_file, _ = QFileDialog.getSaveFileName(self, "Zapisz plik jako")
        if not local_file:
            return

        # Rozpocznij download
        self.file_transfer.start_download(active_session, remote_path, local_file)

    def on_profile_selected(self, profile):
        """Obsługuje wybór profilu SSH"""
        if self.logger:
            self.logger.info(
                f"Wybrano profil: {profile.name} ({profile.hostname}:{profile.port})"
            )

        # Otwórz dialog połączenia z wypełnionymi danymi z profilu
        dialog = ConnectionDialog(self)
        dialog.hostname_edit.setText(profile.hostname)
        dialog.username_edit.setText(profile.username)
        dialog.port_spin.setValue(profile.port)

        if profile.key_filename:
            dialog.key_filename_edit.setText(profile.key_filename)

        # Ustaw flagę zapisywania hasła
        if profile.save_password:
            dialog.save_password_check.setChecked(True)

        # Pokaż dialog
        if dialog.exec() == dialog.DialogCode.Accepted:
            connection_data = dialog.get_connection_data()

            # Dodaj dane z profilu
            connection_data.update(
                {
                    "proxy_config": profile.proxy_config,
                    "ssh_options": profile.ssh_options,
                }
            )

            # Usuń fingerprint_callback z connection_data żeby nie trafiło do SshBackend
            if "fingerprint_callback" in connection_data:
                del connection_data["fingerprint_callback"]
            if (
                "ssh_options" in connection_data
                and "fingerprint_callback" in connection_data["ssh_options"]
            ):
                del connection_data["ssh_options"]["fingerprint_callback"]

            # Stwórz sesję
            self.create_session_from_data(connection_data)

    def create_session_from_data(self, connection_data):
        """Create SSH session from connection data with fingerprint handling"""
        try:
            hostname = connection_data["hostname"]
            username = connection_data["username"]
            port = connection_data["port"]

            if self.logger:
                self.logger.info(f"Creating SSH session for {hostname}:{port}")

            # Pobierz ustawienia z pliku konfiguracyjnego
            sessions_cfg = self.gui_config.get("sessions") or {}
            security_cfg = self.gui_config.get("security") or {}
            proxy_cfg = self.gui_config.get("proxy") or {}

            # Timeout backendu
            connect_timeout = sessions_cfg.get("default_timeout", 30)

            # SSH options
            ssh_options = {}
            if "strict_host_key_checking" in security_cfg:
                ssh_options["StrictHostKeyChecking"] = (
                    "yes" if security_cfg.get("strict_host_key_checking") else "no"
                )
            if "known_hosts_file" in security_cfg:
                ssh_options["UserKnownHostsFile"] = os.path.expanduser(
                    security_cfg.get("known_hosts_file")
                )
            # Przenieś opcje z connection_data (mają priorytet)
            if connection_data.get("ssh_options"):
                ssh_options.update(connection_data.get("ssh_options"))

            # Proxy z profilu/danych połączenia ma priorytet nad globalnym
            final_proxy = connection_data.get("proxy_config") or proxy_cfg or None

            # Przygotuj callback z częściowymi argumentami
            fingerprint_handler = partial(
                self.handle_ssh_fingerprint, hostname=hostname, port=port
            )

            # Uruchom tworzenie sesji w wątku roboczym, aby nie blokować GUI
            def worker():
                try:
                    session_id = self.session_manager.create_session(
                        connection_data,
                        request_password_callback=self.request_password_threadsafe,
                        fingerprint_callback=fingerprint_handler,
                        timeout=connect_timeout,
                        ssh_options=ssh_options,
                        proxy_config=final_proxy,
                    )
                    if session_id:
                        self.session_created.emit(session_id)
                    else:
                        self.session_creation_failed.emit(
                            "Nie udało się utworzyć sesji SSH"
                        )
                except Exception as e:
                    self.session_creation_failed.emit(str(e))

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            error_msg = f"Błąd tworzenia sesji: {e}"
            if self.logger:
                self.logger.error(f"MancerTerminalWindow - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def _on_session_created(self, session_id: str):
        """Slot: sesja utworzona pomyślnie - UI aktualizacja na głównym wątku"""
        try:
            # Stwórz terminal dla sesji
            self.create_terminal_for_session(session_id)
            # Połącz sesję
            self.session_manager.connect_session(session_id)
            if self.logger:
                self.logger.info(f"Sesja SSH utworzona pomyślnie: {session_id}")
        except Exception as e:
            QMessageBox.critical(
                self, "Błąd", f"Nie udało się dokończyć konfiguracji sesji: {e}"
            )

    def _on_session_creation_failed(self, message: str):
        """Slot: błąd tworzenia sesji"""
        if self.logger:
            self.logger.error(f"Błąd tworzenia sesji: {message}")
        QMessageBox.critical(self, "Błąd", message)

    def request_password_threadsafe(self, hostname: str, username: str) -> str:
        """Wyświetla okno hasła w głównym wątku i zwraca hasło (bezpieczne dla wątków)"""
        try:
            resp_q: "queue.Queue[str]" = queue.Queue()
            self.password_request.emit(hostname, username, resp_q)
            password = resp_q.get()
            return password
        except Exception:
            return ""

    def handle_ssh_fingerprint(self, fingerprint: str, hostname: str, port: int) -> str:
        """Handle SSH fingerprint prompt - show dialog and return user decision"""
        try:
            if self.logger:
                self.logger.info(
                    f"SSH fingerprint prompt for {hostname}:{port} - {fingerprint}"
                )

            # Użyj kolejki do uzyskania wyniku z głównego wątku
            response_queue: "queue.Queue[str]" = queue.Queue()

            # Timeout dialogu z configu
            fingerprint_timeout = (
                (self.gui_config.get("security") or {}).get("fingerprint_timeout")
                or (self.gui_config.get("sessions") or {}).get("default_timeout")
                or 60
            )

            # Wyemituj sygnał do głównego wątku z danymi i kolejką na wynik
            self.fingerprint_request.emit(
                hostname, port, fingerprint, int(fingerprint_timeout), response_queue
            )

            # Zaczekaj synchronicznie na decyzję użytkownika (wątek roboczy)
            decision = response_queue.get()
            return decision

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error handling SSH fingerprint: {e}")
            return "no"  # Default to reject on error

    def _on_fingerprint_request(
        self,
        hostname: str,
        port: int,
        fingerprint: str,
        timeout_seconds: int,
        response_queue: object,
    ):
        """Slot wykonywany w głównym wątku - pokazuje dialog i odkłada decyzję do kolejki"""
        try:
            from .ssh_fingerprint_dialog import SSHFingerprintDialog

            dialog = SSHFingerprintDialog(
                hostname=hostname,
                port=port,
                fingerprint=fingerprint,
                key_type="unknown",
                timeout_seconds=timeout_seconds,
                parent=self,
            )

            if dialog.exec() == dialog.DialogCode.Accepted:
                accepted, save_permanently = dialog.get_result()

                if accepted:
                    response = "yes"
                else:
                    response = "no"
            else:
                response = "cancel"

            # Zwróć decyzję do wątku roboczego
            try:
                # type: ignore[attr-defined]
                response_queue.put(response)
            except Exception:
                pass
        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Failed to show fingerprint dialog: {e}")
            try:
                response_queue.put("no")
            except Exception:
                pass

    def _on_password_request(
        self, hostname: str, username: str, response_queue: object
    ):
        """Slot w głównym wątku: pokazuje okno hasła i odkłada wynik do kolejki"""
        try:
            from .password_dialog import PasswordDialog

            dialog = PasswordDialog(hostname, username, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                password = dialog.get_password()
            else:
                password = ""
            try:
                response_queue.put(password)
            except Exception:
                pass
        except Exception as e:
            if hasattr(self, "logger") and self.logger:
                self.logger.error(f"Failed to show password dialog: {e}")
            try:
                response_queue.put("")
            except Exception:
                pass

    # Zapisy do known_hosts realizuje backend (preflight)

    def set_master_key(self):
        """Ustawia klucz główny dla CredentialStore"""
        try:
            from .master_key_dialog import MasterKeyDialog

            # Pobierz CredentialStore z ProfileManagerWidget
            credential_store = self.profile_manager.profile_service.credential_store

            dialog = MasterKeyDialog(credential_store, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                if self.logger:
                    self.logger.info("Klucz główny został ustawiony")
                QMessageBox.information(self, "Sukces", "Klucz główny został ustawiony")

        except Exception as e:
            error_msg = f"Błąd ustawiania klucza głównego: {e}"
            if self.logger:
                self.logger.error(f"MancerTerminalWindow - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def verify_master_key(self):
        """Weryfikuje klucz główny dla CredentialStore"""
        try:
            from .master_key_dialog import MasterKeyPromptDialog

            # Pobierz CredentialStore z ProfileManagerWidget
            credential_store = self.profile_manager.profile_service.credential_store

            dialog = MasterKeyPromptDialog(credential_store, self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                if self.logger:
                    self.logger.info("Klucz główny został zweryfikowany")
                QMessageBox.information(
                    self, "Sukces", "Klucz główny został zweryfikowany"
                )

        except Exception as e:
            error_msg = f"Błąd weryfikacji klucza głównego: {e}"
            if self.logger:
                self.logger.error(f"MancerTerminalWindow - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def show_about(self):
        """Pokazuje okno 'O programie'"""
        QMessageBox.about(
            self,
            "O programie",
            "Mancer Terminal v1.0.0\n\n"
            "SSH Terminal Emulator zintegrowany z frameworkiem Mancer\n"
            "Obsługuje zarządzanie sesjami SSH, transfer plików przez SCP\n"
            "i proxy SSH.",
        )

    def closeEvent(self, event):
        """Obsługuje zamknięcie aplikacji"""
        # Zamknij wszystkie sesje
        self.session_manager.close_all_sessions()
        event.accept()
