"""
Widget transferu plików przez SCP
"""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
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
from mancer.infrastructure.backend.ssh_backend import SCPTransfer


class TransferMonitorThread(QThread):
    """Wątek monitorujący transfery"""

    transfer_updated = pyqtSignal(str, dict)  # transfer_id, transfer_info
    transfer_completed = pyqtSignal(str, bool)  # transfer_id, success

    def __init__(self, ssh_service: SSHSessionService):
        super().__init__()
        self.ssh_service = ssh_service
        self.running = True

    def run(self):
        """Główna pętla monitorowania"""
        while self.running:
            try:
                # Pobierz wszystkie transfery
                transfers = self.ssh_service.list_transfers()

                for transfer in transfers:
                    # Emituj aktualizację
                    transfer_info = {
                        "id": transfer.id,
                        "source": transfer.source,
                        "destination": transfer.destination,
                        "direction": transfer.direction,
                        "status": transfer.status,
                        "progress": transfer.progress,
                        "bytes_transferred": transfer.bytes_transferred,
                        "total_bytes": transfer.total_bytes,
                        "start_time": transfer.start_time.isoformat(),
                        "end_time": transfer.end_time.isoformat() if transfer.end_time else None,
                    }

                    self.transfer_updated.emit(transfer.id, transfer_info)

                    # Sprawdź czy transfer się zakończył
                    if transfer.status in ["completed", "failed", "cancelled"]:
                        self.transfer_completed.emit(transfer.id, transfer.status == "completed")

            except Exception as e:
                # Log błędu
                pass

            # Czekaj przed następnym sprawdzeniem
            self.msleep(1000)  # 1 sekunda

    def stop(self):
        """Zatrzymuje wątek"""
        self.running = False


class FileTransferWidget(QWidget):
    """Widget transferu plików przez SCP"""

    def __init__(self):
        super().__init__()

        # Inicjalizacja SSH service
        self.ssh_service = SSHSessionService()

        # Wątek monitorowania transferów
        self.monitor_thread = TransferMonitorThread(self.ssh_service)
        self.monitor_thread.transfer_updated.connect(self.on_transfer_updated)
        self.monitor_thread.transfer_completed.connect(self.on_transfer_completed)
        self.monitor_thread.start()

        # Inicjalizacja UI
        self.init_ui()

        # Timer do aktualizacji listy transferów
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_transfers_list)
        self.update_timer.start(2000)  # Aktualizuj co 2 sekundy

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Nagłówek
        header = QLabel("Transfer Plików (SCP)")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        # Panel przycisków
        button_panel = self.create_button_panel()
        layout.addWidget(button_panel)

        # Lista transferów
        transfers_group = QGroupBox("Aktywne Transfery")
        transfers_layout = QVBoxLayout(transfers_group)

        self.transfers_tree = QTreeWidget()
        self.transfers_tree.setHeaderLabels(["ID", "Kierunek", "Status", "Postęp", "Źródło", "Cel"])
        self.transfers_tree.setColumnWidth(0, 80)
        self.transfers_tree.setColumnWidth(1, 80)
        self.transfers_tree.setColumnWidth(2, 80)
        self.transfers_tree.setColumnWidth(3, 100)
        self.transfers_tree.setColumnWidth(4, 150)
        self.transfers_tree.setColumnWidth(5, 150)

        # Połącz sygnały
        self.transfers_tree.itemClicked.connect(self.on_transfer_selected)

        transfers_layout.addWidget(self.transfers_tree)
        layout.addWidget(transfers_group)

        # Panel szczegółów transferu
        details_group = QGroupBox("Szczegóły Transferu")
        details_layout = QVBoxLayout(details_group)

        self.transfer_details = QTextEdit()
        self.transfer_details.setReadOnly(True)
        self.transfer_details.setMaximumHeight(120)
        details_layout.addWidget(self.transfer_details)

        layout.addWidget(details_group)

        # Inicjalizuj listę transferów
        self.update_transfers_list()

    def create_button_panel(self):
        """Tworzy panel przycisków"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Upload
        self.upload_btn = QPushButton("Upload")
        self.upload_btn.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_btn)

        # Download
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download_file)
        layout.addWidget(self.download_btn)

        layout.addStretch()

        # Anuluj
        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.cancel_selected_transfer)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        # Odśwież
        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.update_transfers_list)
        layout.addWidget(self.refresh_btn)

        return panel

    def update_transfers_list(self):
        """Aktualizuje listę transferów"""
        try:
            # Pobierz transfery z service
            transfers = self.ssh_service.list_transfers()

            # Wyczyść drzewo
            self.transfers_tree.clear()

            # Dodaj transfery do drzewa
            for transfer in transfers:
                item = QTreeWidgetItem()
                item.setText(0, transfer.id[:8])  # Krótkie ID
                item.setText(1, transfer.direction)
                item.setText(2, transfer.status)
                item.setText(3, f"{transfer.progress:.1f}%")
                item.setText(4, transfer.source)
                item.setText(5, transfer.destination)

                # Ustaw kolory na podstawie statusu
                if transfer.status == "completed":
                    item.setForeground(2, Qt.GlobalColor.green)
                elif transfer.status == "transferring":
                    item.setForeground(2, Qt.GlobalColor.blue)
                elif transfer.status == "failed":
                    item.setForeground(2, Qt.GlobalColor.red)
                elif transfer.status == "cancelled":
                    item.setForeground(2, Qt.GlobalColor.gray)

                # Przechowaj pełne ID w item
                item.setData(0, Qt.ItemDataRole.UserRole, transfer.id)

                self.transfers_tree.addTopLevelItem(item)

        except Exception as e:
            # W przypadku błędu, wyświetl informację
            self.transfers_tree.clear()
            error_item = QTreeWidgetItem()
            error_item.setText(0, f"Błąd: {str(e)}")
            error_item.setForeground(0, Qt.GlobalColor.red)
            self.transfers_tree.addTopLevelItem(error_item)

    def on_transfer_selected(self, item: QTreeWidgetItem, column: int):
        """Obsługuje wybór transferu"""
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            transfer_id = item.data(0, Qt.ItemDataRole.UserRole)

            # Włącz przycisk anulowania
            self.cancel_btn.setEnabled(True)

            # Pokaż szczegóły transferu
            self.show_transfer_details(transfer_id)

    def show_transfer_details(self, transfer_id: str):
        """Pokazuje szczegóły transferu"""
        try:
            transfer = self.ssh_service.get_transfer_status(transfer_id)
            if transfer:
                details_text = f"""
ID Transferu: {transfer.id}
Kierunek: {transfer.direction}
Status: {transfer.status}
Postęp: {transfer.progress:.1f}%
Źródło: {transfer.source}
Cel: {transfer.destination}
Rozpoczęty: {transfer.start_time.isoformat()}
"""

                if transfer.end_time:
                    details_text += f"Zakończony: {transfer.end_time.isoformat()}\n"

                if transfer.bytes_transferred > 0:
                    details_text += f"Przesłane: {transfer.bytes_transferred} bajtów\n"

                if transfer.total_bytes > 0:
                    details_text += f"Całkowity rozmiar: {transfer.total_bytes} bajtów\n"

                self.transfer_details.setText(details_text)
            else:
                self.transfer_details.setText("Brak informacji o transferze")

        except Exception as e:
            self.transfer_details.setText(f"Błąd pobierania szczegółów: {str(e)}")

    def upload_file(self):
        """Upload pliku"""
        # Pobierz aktywną sesję (można dodać parametr)
        # active_session = self.get_active_session()
        # if not active_session:
        #     QMessageBox.warning(self, "Ostrzeżenie", "Brak aktywnej sesji")
        #     return

        # Wybierz plik lokalny
        local_file, _ = QFileDialog.getOpenFileName(self, "Wybierz plik do upload")
        if not local_file:
            return

        # Pobierz ścieżkę zdalną
        remote_path, ok = QInputDialog.getText(self, "Ścieżka zdalna", "Podaj ścieżkę zdalną:")
        if not ok or not remote_path:
            return

        # Pobierz ID sesji (można dodać dialog wyboru sesji)
        session_id, ok = QInputDialog.getText(self, "ID Sesji", "Podaj ID sesji SSH:")
        if not ok or not session_id:
            return

        # Rozpocznij upload
        try:
            transfer = self.ssh_service.scp_upload(local_file, remote_path, session_id)
            if transfer:
                QMessageBox.information(self, "Sukces", f"Rozpoczęto upload: {transfer.id}")
                self.update_transfers_list()
            else:
                QMessageBox.critical(self, "Błąd", "Nie udało się rozpocząć upload")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd upload: {str(e)}")

    def download_file(self):
        """Download pliku"""
        # Pobierz ID sesji
        session_id, ok = QInputDialog.getText(self, "ID Sesji", "Podaj ID sesji SSH:")
        if not ok or not session_id:
            return

        # Pobierz ścieżkę zdalną
        remote_path, ok = QInputDialog.getText(self, "Ścieżka zdalna", "Podaj ścieżkę zdalną:")
        if not ok or not remote_path:
            return

        # Wybierz lokalizację
        local_file, _ = QFileDialog.getSaveFileName(self, "Zapisz plik jako")
        if not local_file:
            return

        # Rozpocznij download
        try:
            transfer = self.ssh_service.scp_download(remote_path, local_file, session_id)
            if transfer:
                QMessageBox.information(self, "Sukces", f"Rozpoczęto download: {transfer.id}")
                self.update_transfers_list()
            else:
                QMessageBox.critical(self, "Błąd", "Nie udało się rozpocząć download")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd download: {str(e)}")

    def cancel_selected_transfer(self):
        """Anuluje wybrany transfer"""
        current_item = self.transfers_tree.currentItem()
        if not current_item or not current_item.data(0, Qt.ItemDataRole.UserRole):
            return

        transfer_id = current_item.data(0, Qt.ItemDataRole.UserRole)

        try:
            success = self.ssh_service.cancel_transfer(transfer_id)
            if success:
                QMessageBox.information(self, "Sukces", "Transfer anulowany")
                self.update_transfers_list()
            else:
                QMessageBox.warning(self, "Ostrzeżenie", "Nie udało się anulować transferu")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd anulowania: {str(e)}")

    def on_transfer_updated(self, transfer_id: str, transfer_info: dict):
        """Obsługuje aktualizację transferu"""
        # Znajdź item w drzewie i zaktualizuj
        for i in range(self.transfers_tree.topLevelItemCount()):
            item = self.transfers_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == transfer_id:
                item.setText(2, transfer_info["status"])
                item.setText(3, f"{transfer_info['progress']:.1f}%")

                # Aktualizuj kolory
                if transfer_info["status"] == "completed":
                    item.setForeground(2, Qt.GlobalColor.green)
                elif transfer_info["status"] == "transferring":
                    item.setForeground(2, Qt.GlobalColor.blue)
                elif transfer_info["status"] == "failed":
                    item.setForeground(2, Qt.GlobalColor.red)
                elif transfer_info["status"] == "cancelled":
                    item.setForeground(2, Qt.GlobalColor.gray)
                break

    def on_transfer_completed(self, transfer_id: str, success: bool):
        """Obsługuje zakończenie transferu"""
        if success:
            # Transfer zakończony pomyślnie
            pass
        else:
            # Transfer zakończony z błędem
            pass

        # Odśwież listę
        self.update_transfers_list()

    def start_upload(self, session_id: str, local_path: str, remote_path: str):
        """Rozpoczyna upload pliku"""
        try:
            transfer = self.ssh_service.scp_upload(local_path, remote_path, session_id)
            if transfer:
                QMessageBox.information(self, "Sukces", f"Rozpoczęto upload: {transfer.id}")
                self.update_transfers_list()
            else:
                QMessageBox.critical(self, "Błąd", "Nie udało się rozpocząć upload")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd upload: {str(e)}")

    def start_download(self, session_id: str, remote_path: str, local_path: str):
        """Rozpoczyna download pliku"""
        try:
            transfer = self.ssh_service.scp_download(remote_path, local_path, session_id)
            if transfer:
                QMessageBox.information(self, "Sukces", f"Rozpoczęto download: {transfer.id}")
                self.update_transfers_list()
            else:
                QMessageBox.critical(self, "Błąd", "Nie udało się rozpocząć download")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd download: {str(e)}")

    def get_transfers_count(self) -> int:
        """Zwraca liczbę transferów"""
        try:
            return len(self.ssh_service.list_transfers())
        except Exception:
            return 0

    def closeEvent(self, event):
        """Obsługuje zamknięcie widgetu"""
        # Zatrzymaj wątek monitorowania
        if self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()

        event.accept()
