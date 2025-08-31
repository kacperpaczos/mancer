"""
Widget terminala SSH
"""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from mancer.domain.service.ssh_session_service import SSHSessionService
from mancer.infrastructure.backend.ssh_backend import SshBackend


class SSHCommandThread(QThread):
    """Wątek do wykonywania komend SSH"""

    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    command_finished = pyqtSignal(int)

    def __init__(self, ssh_service: SSHSessionService, session_id: str, command: str):
        super().__init__()
        self.ssh_service = ssh_service
        self.session_id = session_id
        self.command = command

        # Inicjalizacja loggera
        self.setup_logger()

    def setup_logger(self):
        """Konfiguruje logger dla wątku komend"""
        try:
            from mancer.infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
        except Exception:
            self.logger = None

    def run(self):
        """Wykonuje komendę SSH"""
        try:
            if self.logger:
                self.logger.info(
                    f"SSHCommandThread - wykonywanie komendy: {self.command} na sesji: {self.session_id}"
                )

            result = self.ssh_service.execute_command(
                command=self.command, session_id=self.session_id
            )

            if result:
                if result.raw_output:
                    if self.logger:
                        self.logger.info(
                            f"SSHCommandThread - komenda zakończona pomyślnie, output: {len(result.raw_output)} znaków"
                        )
                    self.output_received.emit(result.raw_output)
                if result.error_message:
                    if self.logger:
                        self.logger.error(
                            f"SSHCommandThread - komenda zakończona z błędem: {result.error_message}"
                        )
                    self.error_received.emit(result.error_message)
                self.command_finished.emit(result.exit_code)
            else:
                error_msg = "Błąd wykonania komendy - brak wyniku"
                if self.logger:
                    self.logger.error(f"SSHCommandThread - {error_msg}")
                self.error_received.emit(error_msg)
                self.command_finished.emit(1)

        except Exception as e:
            error_msg = f"Błąd wykonania komendy SSH: {str(e)}"
            if self.logger:
                self.logger.error(f"SSHCommandThread - {error_msg}")
            self.error_received.emit(error_msg)
            self.command_finished.emit(1)


class TerminalWidget(QWidget):
    """Widget terminala SSH"""

    session_closed = pyqtSignal()

    def __init__(self, session_id: str, ssh_service: SSHSessionService = None):
        super().__init__()
        self.session_id = session_id

        # Inicjalizacja loggera
        self.setup_logger()

        # Inicjalizacja SSH service
        self.ssh_service = ssh_service or SSHSessionService()

        # Historia komend
        self.command_history = []
        self.history_index = 0

        # Inicjalizacja UI
        self.init_ui()

        # Timer do aktualizacji statusu
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Aktualizuj co 2 sekundy

    def setup_logger(self):
        """Konfiguruje logger dla terminala"""
        try:
            from mancer.infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
            self.logger.info(f"TerminalWidget - inicjalizacja dla sesji: {self.session_id}")
        except Exception as e:
            print(f"Błąd konfiguracji loggera TerminalWidget: {e}")
            self.logger = None

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Górny panel - informacje o sesji
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)

        # Splitter dla terminala i logów
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # Terminal
        terminal_panel = self.create_terminal_panel()
        splitter.addWidget(terminal_panel)

        # Logi
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)

        # Ustaw proporcje splittera
        splitter.setSizes([600, 200])

        # Dolny panel - status
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Tworzy górny panel z informacjami o sesji"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # ID sesji
        self.session_id_label = QLabel(f"Sesja: {self.session_id[:8]}")
        layout.addWidget(self.session_id_label)

        layout.addStretch()

        # Status połączenia
        self.connection_status = QLabel("Status: Sprawdzanie...")
        layout.addWidget(self.connection_status)

        # Przycisk rozłączenia
        self.disconnect_btn = QPushButton("Rozłącz")
        self.disconnect_btn.clicked.connect(self.disconnect_session)
        layout.addWidget(self.disconnect_btn)

        return panel

    def create_terminal_panel(self):
        """Tworzy panel terminala"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Monospace", 10))

        # Ustaw kolory terminala
        palette = self.terminal_output.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
        self.terminal_output.setPalette(palette)

        layout.addWidget(self.terminal_output)

        # Panel komend
        command_panel = QWidget()
        command_layout = QHBoxLayout(command_panel)

        # Prompt
        self.prompt_label = QLabel("$ ")
        command_layout.addWidget(self.prompt_label)

        # Pole komendy
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.setFont(QFont("Monospace", 10))
        command_layout.addWidget(self.command_input)

        # Przycisk wykonania
        self.execute_btn = QPushButton("Wykonaj")
        self.execute_btn.clicked.connect(self.execute_command)
        command_layout.addWidget(self.execute_btn)

        # Przycisk wyczyszczenia
        self.clear_btn = QPushButton("Wyczyść")
        self.clear_btn.clicked.connect(self.clear_terminal)
        command_layout.addWidget(self.clear_btn)

        layout.addWidget(command_panel)

        return panel

    def create_log_panel(self):
        """Tworzy panel logów"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Nagłówek
        header = QLabel("Logi sesji:")
        layout.addWidget(header)

        # Logi
        self.log_output = QTextBrowser()
        self.log_output.setFont(QFont("Monospace", 9))
        layout.addWidget(self.log_output)

        return panel

    def create_bottom_panel(self):
        """Tworzy dolny panel statusu"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Status komendy
        self.command_status = QLabel("Gotowy")
        layout.addWidget(self.command_status)

        layout.addStretch()

        # Liczba komend
        self.commands_count = QLabel("Komendy: 0")
        layout.addWidget(self.commands_count)

        # Czas sesji
        self.session_time = QLabel("Czas: 00:00:00")
        layout.addWidget(self.session_time)

        return panel

    def execute_command(self):
        """Wykonuje komendę SSH"""
        try:
            command = self.command_input.text().strip()
            if not command:
                return

            if self.logger:
                self.logger.info(f"Terminal {self.session_id} - wykonywanie komendy: {command}")

            # Dodaj do historii
            self.add_to_history(command)

            # Wyczyść pole komendy
            self.command_input.clear()

            # Wyświetl komendę w terminalu
            self.terminal_output.append(f"$ {command}")

            # Ustaw status
            self.command_status.setText("Wykonywanie...")

            # Uruchom komendę w osobnym wątku
            self.command_thread = SSHCommandThread(self.ssh_service, self.session_id, command)

            # Połącz sygnały
            self.command_thread.output_received.connect(self.on_output_received)
            self.command_thread.error_received.connect(self.on_error_received)
            self.command_thread.command_finished.connect(self.on_command_finished)

            # Uruchom wątek
            self.command_thread.start()

            # Dodaj do logów
            self.log_output.append(f"[INFO] Wykonano komendę: {command}")

        except Exception as e:
            error_msg = f"Błąd podczas wykonywania komendy: {e}"
            if self.logger:
                self.logger.error(f"Terminal {self.session_id} - {error_msg}")
            self.log_output.append(f"[ERROR] {error_msg}")
            self.command_status.setText("Błąd")

    def on_output_received(self, output: str):
        """Obsługuje otrzymanie outputu"""
        self.terminal_output.append(output)

    def on_error_received(self, error: str):
        """Obsługuje otrzymanie błędu"""
        if self.logger:
            self.logger.error(f"Terminal {self.session_id} - błąd komendy: {error}")

        self.terminal_output.append(f"ERROR: {error}")
        self.log_output.append(f"[ERROR] {error}")

    def on_command_finished(self, exit_code: int):
        """Obsługuje zakończenie komendy"""
        if exit_code == 0:
            self.command_status.setText("Gotowy")
            self.log_output.append(f"[INFO] Komenda zakończona pomyślnie (kod: {exit_code})")
        else:
            self.command_status.setText(f"Błąd (kod: {exit_code})")
            self.log_output.append(f"[WARNING] Komenda zakończona z błędem (kod: {exit_code})")

        # Aktualizuj licznik komend
        self.commands_count.setText(f"Komendy: {len(self.command_history)}")

    def add_to_history(self, command: str):
        """Dodaje komendę do historii"""
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)

    def clear_terminal(self):
        """Czyści terminal"""
        self.terminal_output.clear()
        self.command_status.setText("Gotowy")

    def clear_logs(self):
        """Czyści logi"""
        self.log_output.clear()

    def disconnect_session(self):
        """Rozłącza sesję"""
        try:
            self.ssh_service.disconnect_session(self.session_id)
            self.connection_status.setText("Status: Rozłączony")
            self.disconnect_btn.setEnabled(False)
            self.command_input.setEnabled(False)
            self.execute_btn.setEnabled(False)

            self.log_output.append("[INFO] Sesja rozłączona")

        except Exception as e:
            self.log_output.append(f"[ERROR] Błąd rozłączania: {str(e)}")

    def close_session(self):
        """Zamyka sesję"""
        try:
            self.ssh_service.close_session(self.session_id)
            self.session_closed.emit()
        except Exception as e:
            self.log_output.append(f"[ERROR] Błąd zamykania sesji: {str(e)}")

    def update_status(self):
        """Aktualizuje status sesji"""
        try:
            status = self.ssh_service.get_session_status(self.session_id)
            if status:
                self.connection_status.setText(f"Status: {status}")

                # Aktualizuj kolory na podstawie statusu
                if status == "connected":
                    self.connection_status.setStyleSheet("color: green;")
                elif status == "connecting":
                    self.connection_status.setStyleSheet("color: orange;")
                elif status == "error":
                    self.connection_status.setStyleSheet("color: red;")
                else:
                    self.connection_status.setStyleSheet("")

        except Exception as e:
            self.log_output.append(f"[ERROR] Błąd aktualizacji statusu: {str(e)}")

    def keyPressEvent(self, event):
        """Obsługuje naciśnięcie klawiszy"""
        if event.key() == Qt.Key.Key_Up:
            # Historia w górę
            if self.history_index > 0:
                self.history_index -= 1
                if self.history_index < len(self.command_history):
                    self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            # Historia w dół
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)

    def clear(self):
        """Czyści terminal i logi"""
        self.clear_terminal()
        self.clear_logs()
