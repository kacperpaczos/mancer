"""
Widget zarządzania sesjami SSH
"""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from mancer.domain.service.ssh_session_service import SSHSessionService
from mancer.infrastructure.backend.ssh_backend import SSHSession


class SessionManagerWidget(QWidget):
    """Widget zarządzania sesjami SSH"""

    session_selected = pyqtSignal(str)  # Emituje ID sesji
    new_session_requested = pyqtSignal()  # Emituje żądanie nowej sesji

    def __init__(self):
        super().__init__()

        # Inicjalizacja loggera
        self.setup_logger()

        # Inicjalizacja SSH service
        self.ssh_service = SSHSessionService()

        # Aktywna sesja
        self.active_session = None

        # Inicjalizacja UI
        self.init_ui()

        # Timer do aktualizacji listy sesji
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_sessions_list)
        self.update_timer.start(3000)  # Aktualizuj co 3 sekundy

    def setup_logger(self):
        """Konfiguruje logger dla managera sesji"""
        try:
            from mancer.infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
            self.logger.info("SessionManagerWidget - inicjalizacja")
        except Exception as e:
            print(f"Błąd konfiguracji loggera SessionManager: {e}")
            self.logger = None

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Nagłówek
        header = QLabel("Zarządzanie Sesjami SSH")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Panel przycisków
        button_panel = self.create_button_panel()
        layout.addWidget(button_panel)

        # Lista sesji
        sessions_group = QGroupBox("Aktywne Sesje")
        sessions_layout = QVBoxLayout(sessions_group)

        self.sessions_tree = QTreeWidget()
        self.sessions_tree.setHeaderLabels(["Sesja", "Status", "Host", "Użytkownik"])
        self.sessions_tree.setColumnWidth(0, 120)
        self.sessions_tree.setColumnWidth(1, 80)
        self.sessions_tree.setColumnWidth(2, 120)
        self.sessions_tree.setColumnWidth(3, 100)

        # Połącz sygnały
        self.sessions_tree.itemClicked.connect(self.on_session_selected)
        self.sessions_tree.itemDoubleClicked.connect(self.on_session_double_clicked)

        sessions_layout.addWidget(self.sessions_tree)
        layout.addWidget(sessions_group)

        # Panel szczegółów sesji
        details_group = QGroupBox("Szczegóły Sesji")
        details_layout = QVBoxLayout(details_group)

        self.session_details = QTextEdit()
        self.session_details.setReadOnly(True)
        self.session_details.setMaximumHeight(150)
        details_layout.addWidget(self.session_details)

        layout.addWidget(details_group)

        # Inicjalizuj listę sesji
        self.update_sessions_list()

    def create_session(
        self,
        connection_data: dict,
        request_password_callback: callable = None,
        fingerprint_callback: callable = None,
        timeout: int | None = None,
        ssh_options: dict | None = None,
        proxy_config: dict | None = None,
    ) -> str:
        """Tworzy nową sesję SSH z obsługą fingerprinta"""
        try:
            if self.logger:
                self.logger.info(
                    f"SessionManager - tworzenie sesji SSH: {connection_data['username']}@{connection_data['hostname']}"
                )

            # Stwórz sesję przez SSH service
            session = self.ssh_service.create_session(
                hostname=connection_data["hostname"],
                username=connection_data["username"],
                port=connection_data.get("port", 22),
                key_filename=connection_data.get("key_filename"),
                password=connection_data.get("password"),
                proxy_config=proxy_config or connection_data.get("proxy_config"),
                request_password_callback=request_password_callback,
                fingerprint_callback=fingerprint_callback,
                timeout=timeout,
                ssh_options=ssh_options or connection_data.get("ssh_options"),
            )

            if session:
                if self.logger:
                    self.logger.info(f"SessionManager - sesja utworzona: {session.id}")
                # Dodaj do listy
                self.update_sessions_list()
                return session.id
            else:
                if self.logger:
                    self.logger.error("SessionManager - nie udało się utworzyć sesji")
                return None

        except Exception as e:
            error_msg = f"Nie udało się utworzyć sesji: {str(e)}"
            if self.logger:
                self.logger.error(f"SessionManager - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)
            return None

    def create_button_panel(self):
        """Tworzy panel przycisków"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Nowa sesja
        self.new_session_btn = QPushButton("Nowa Sesja")
        self.new_session_btn.clicked.connect(self.new_session_requested.emit)
        layout.addWidget(self.new_session_btn)

        # Połącz
        self.connect_btn = QPushButton("Połącz")
        self.connect_btn.clicked.connect(self.connect_selected_session)
        self.connect_btn.setEnabled(False)
        layout.addWidget(self.connect_btn)

        # Rozłącz
        self.disconnect_btn = QPushButton("Rozłącz")
        self.disconnect_btn.clicked.connect(self.disconnect_selected_session)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)

        # Zamknij
        self.close_btn = QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.close_selected_session)
        self.close_btn.setEnabled(False)
        layout.addWidget(self.close_btn)

        layout.addStretch()

        # Odśwież
        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.update_sessions_list)
        layout.addWidget(self.refresh_btn)

        return panel

    def update_sessions_list(self):
        """Aktualizuje listę sesji"""
        try:
            # Pobierz sesje z service
            sessions = self.ssh_service.list_sessions()

            # Wyczyść drzewo
            self.sessions_tree.clear()

            # Dodaj sesje do drzewa
            for session in sessions:
                item = QTreeWidgetItem()
                item.setText(0, session.id[:8])  # Krótkie ID
                item.setText(1, session.status)
                item.setText(2, session.hostname)
                item.setText(3, session.username)

                # Ustaw kolory na podstawie statusu
                if session.status == "connected":
                    item.setForeground(1, Qt.GlobalColor.green)
                elif session.status == "connecting":
                    item.setForeground(1, Qt.GlobalColor.orange)
                elif session.status == "error":
                    item.setForeground(1, Qt.GlobalColor.red)

                # Przechowaj pełne ID w item
                item.setData(0, Qt.ItemDataRole.UserRole, session.id)

                self.sessions_tree.addTopLevelItem(item)

            # Aktualizuj licznik sesji
            self.update_session_count(len(sessions))

        except Exception as e:
            # W przypadku błędu, wyświetl informację
            self.sessions_tree.clear()
            error_item = QTreeWidgetItem()
            error_item.setText(0, f"Błąd: {str(e)}")
            error_item.setForeground(0, Qt.GlobalColor.red)
            self.sessions_tree.addTopLevelItem(error_item)

    def update_session_count(self, count: int):
        """Aktualizuje licznik sesji"""
        # Można dodać etykietę z licznikiem
        pass

    def on_session_selected(self, item: QTreeWidgetItem, column: int):
        """Obsługuje wybór sesji"""
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            session_id = item.data(0, Qt.ItemDataRole.UserRole)
            self.active_session = session_id

            # Włącz przyciski
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.close_btn.setEnabled(True)

            # Pokaż szczegóły sesji
            self.show_session_details(session_id)

            # Emituj sygnał wyboru sesji
            self.session_selected.emit(session_id)

    def on_session_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Obsługuje podwójne kliknięcie na sesję"""
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            session_id = item.data(0, Qt.ItemDataRole.UserRole)
            # Przełącz na terminal dla tej sesji
            self.session_selected.emit(session_id)

    def show_session_details(self, session_id: str):
        """Pokazuje szczegóły sesji"""
        try:
            session_info = self.ssh_service.get_session_info(session_id)
            if session_info:
                details_text = f"""
ID Sesji: {session_info["id"]}
Host: {session_info["hostname"]}
Użytkownik: {session_info["username"]}
Port: {session_info["port"]}
Status: {session_info["status"]}
Utworzona: {session_info["created_at"]}
Ostatnia aktywność: {session_info["last_activity"]}

Aktywne transfery: {len(session_info["active_transfers"])}
"""

                # Dodaj informacje o transferach
                if session_info["active_transfers"]:
                    details_text += "\nTransfery:\n"
                    for transfer in session_info["active_transfers"]:
                        details_text += f"- {transfer['direction']}: {transfer['source']} → {transfer['destination']} ({transfer['progress']:.1f}%)\n"

                self.session_details.setText(details_text)
            else:
                self.session_details.setText("Brak informacji o sesji")

        except Exception as e:
            self.session_details.setText(f"Błąd pobierania szczegółów: {str(e)}")

    def connect_selected_session(self):
        """Łączy wybraną sesję"""
        if not self.active_session:
            return

        try:
            success = self.ssh_service.connect_session(self.active_session)
            if success:
                # Odśwież listę
                self.update_sessions_list()
                # Pokaż szczegóły
                self.show_session_details(self.active_session)
            else:
                # Pokaż błąd
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(self, "Błąd", "Nie udało się połączyć z sesją")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Błąd", f"Błąd łączenia: {str(e)}")

    def disconnect_selected_session(self):
        """Rozłącza wybraną sesję"""
        if not self.active_session:
            return

        try:
            success = self.ssh_service.disconnect_session(self.active_session)
            if success:
                # Odśwież listę
                self.update_sessions_list()
                # Pokaż szczegóły
                self.show_session_details(self.active_session)
            else:
                # Pokaż błąd
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(self, "Błąd", "Nie udało się rozłączyć sesji")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Błąd", f"Błąd rozłączania: {str(e)}")

    def close_selected_session(self):
        """Zamyka wybraną sesję"""
        if not self.active_session:
            return

        try:
            success = self.ssh_service.close_session(self.active_session)
            if success:
                # Wyczyść aktywną sesję
                self.active_session = None

                # Wyłącz przyciski
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(False)
                self.close_btn.setEnabled(False)

                # Wyczyść szczegóły
                self.session_details.clear()

                # Odśwież listę
                self.update_sessions_list()
            else:
                # Pokaż błąd
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(self, "Błąd", "Nie udało się zamknąć sesji")

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Błąd", f"Błąd zamykania: {str(e)}")

    def connect_session(self, session_id: str):
        """Łączy sesję o podanym ID"""
        try:
            success = self.ssh_service.connect_session(session_id)
            if success:
                self.update_sessions_list()
            return success
        except Exception:
            return False

    def disconnect_session(self, session_id: str):
        """Rozłącza sesję o podanym ID"""
        try:
            success = self.ssh_service.disconnect_session(session_id)
            if success:
                self.update_sessions_list()
            return success
        except Exception:
            return False

    def close_session(self, session_id: str):
        """Zamyka sesję o podanym ID"""
        try:
            success = self.ssh_service.close_session(session_id)
            if success:
                self.update_sessions_list()
            return success
        except Exception:
            return False

    def get_sessions_count(self) -> int:
        """Zwraca liczbę sesji"""
        try:
            return len(self.ssh_service.list_sessions())
        except Exception:
            return 0

    def get_active_session(self) -> str:
        """Zwraca ID aktywnej sesji"""
        return self.active_session

    def close_all_sessions(self):
        """Zamyka wszystkie sesje"""
        try:
            sessions = self.ssh_service.list_sessions()
            for session in sessions:
                self.ssh_service.close_session(session.id)

            # Wyczyść aktywną sesję
            self.active_session = None

            # Wyłącz przyciski
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.close_btn.setEnabled(False)

            # Wyczyść szczegóły
            self.session_details.clear()

            # Odśwież listę
            self.update_sessions_list()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Ostrzeżenie", f"Błąd zamykania sesji: {str(e)}")

    # Note: Fingerprint handling methods removed - simplified approach
    # SSH will handle fingerprint prompts naturally during connection
