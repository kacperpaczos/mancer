"""
Widget zarządzania profilami SSH
"""

import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from mancer.domain.model.ssh_profile import SSHProfile
from mancer.domain.service.ssh_profile_service import SSHProfileService


class ProfileEditDialog(QDialog):
    """Dialog edycji profilu SSH"""

    def __init__(self, profile: Optional[SSHProfile] = None, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Edycja profilu SSH" if profile else "Nowy profil SSH")
        self.setModal(True)
        self.setFixedSize(500, 600)

        self.init_ui()
        if profile:
            self.load_profile(profile)

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Formularz
        form_layout = QFormLayout()

        # Nazwa profilu
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nazwa profilu")
        form_layout.addRow("Nazwa:", self.name_edit)

        # Opis
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Opis profilu")
        form_layout.addRow("Opis:", self.description_edit)

        # Hostname
        self.hostname_edit = QLineEdit()
        self.hostname_edit.setPlaceholderText("127.0.0.1")
        form_layout.addRow("Hostname:", self.hostname_edit)

        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("pyroxar")
        form_layout.addRow("Username:", self.username_edit)

        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)
        form_layout.addRow("Port:", self.port_spin)

        # Kategoria
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("default")
        form_layout.addRow("Kategoria:", self.category_edit)

        # Tagi
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1,tag2,tag3")
        form_layout.addRow("Tagi:", self.tags_edit)

        # Klucz prywatny
        self.key_filename_edit = QLineEdit()
        self.key_filename_edit.setPlaceholderText("~/.ssh/id_rsa")
        form_layout.addRow("Klucz prywatny:", self.key_filename_edit)

        # Zapisz hasło
        self.save_password_check = QCheckBox("Zapisz hasło")
        form_layout.addRow("", self.save_password_check)

        layout.addLayout(form_layout)

        # Przyciski
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.save_btn = QPushButton("Zapisz")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def load_profile(self, profile: SSHProfile):
        """Ładuje dane profilu do formularza"""
        try:
            # Bezpieczne pobieranie danych profilu
            name = getattr(profile, "name", "")
            description = getattr(profile, "description", "")
            hostname = getattr(profile, "hostname", "")
            username = getattr(profile, "username", "")
            port = getattr(profile, "port", 22)
            category = getattr(profile, "category", "")
            tags = getattr(profile, "tags", [])
            key_filename = getattr(profile, "key_filename", "")
            save_password = getattr(profile, "save_password", False)

            self.name_edit.setText(str(name))
            self.description_edit.setPlainText(str(description))
            self.hostname_edit.setText(str(hostname))
            self.username_edit.setText(str(username))
            self.port_spin.setValue(int(port))
            self.category_edit.setText(str(category))
            self.tags_edit.setText(",".join(str(tag) for tag in tags))
            self.key_filename_edit.setText(str(key_filename) if key_filename else "")
            self.save_password_check.setChecked(bool(save_password))

        except Exception as e:
            print(f"Błąd ładowania profilu do formularza: {e}")
            # Ustaw domyślne wartości w przypadku błędu
            self.name_edit.setText("")
            self.description_edit.setPlainText("")
            self.hostname_edit.setText("")
            self.username_edit.setText("")
            self.port_spin.setValue(22)
            self.category_edit.setText("")
            self.tags_edit.setText("")
            self.key_filename_edit.setText("")
            self.save_password_check.setChecked(False)

    def get_profile_data(self) -> dict:
        """Zwraca dane z formularza"""
        tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]

        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "hostname": self.hostname_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "port": self.port_spin.value(),
            "category": self.category_edit.text().strip() or "default",
            "tags": tags,
            "key_filename": self.key_filename_edit.text().strip() or None,
            "save_password": self.save_password_check.isChecked(),
        }


class ProfileManagerWidget(QWidget):
    """Widget zarządzania profilami SSH"""

    profile_selected = pyqtSignal(SSHProfile)  # Sygnał wyboru profilu

    def __init__(self):
        super().__init__()

        # Inicjalizacja serwisu profili - opóźniona
        self.profile_service = None

        # Inicjalizacja loggera
        self.setup_logger()

        self.init_ui()

        # Opóźniona inicjalizacja serwisu i ładowanie profili
        self.init_profile_service()

    def setup_logger(self):
        """Konfiguruje logger dla widgetu"""
        try:
            from mancer.infrastructure.logging.mancer_logger import MancerLogger

            self.logger = MancerLogger.get_instance()
            self.logger.info("ProfileManagerWidget - inicjalizacja")
        except Exception as e:
            print(f"Błąd konfiguracji loggera ProfileManagerWidget: {e}")
            self.logger = None

    def init_profile_service(self):
        """Inicjalizuje serwis profili w tle"""
        try:
            if self.logger:
                self.logger.info("ProfileManagerWidget - inicjalizacja serwisu profili")

            # Inicjalizuj serwis profili bez ładowania profili
            self.profile_service = SSHProfileService(load_profiles=False)

            # Załaduj profile w tle
            self.load_profiles()

            # Połącz sygnał filtrowania po załadowaniu profili
            self.category_combo.currentTextChanged.connect(self.filter_by_category)

        except Exception as e:
            error_msg = f"Błąd inicjalizacji serwisu profili: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            print(f"ProfileManagerWidget - {error_msg}")

            # Pokaż błąd w interfejsie
            self.profile_details.setPlainText(f"Błąd inicjalizacji: {e}")

            # Spróbuj ponownie za chwilę
            from PyQt6.QtCore import QTimer

            timer = QTimer()
            timer.singleShot(1000, self.init_profile_service)

    def init_ui(self):
        """Inicjalizuje interfejs użytkownika"""
        layout = QVBoxLayout(self)

        # Nagłówek
        header = QLabel("Zarządzanie profilami SSH")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Panel wyszukiwania
        search_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Wyszukaj profile...")
        self.search_edit.textChanged.connect(self.search_profiles)
        search_layout.addWidget(self.search_edit)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Wszystkie kategorie")
        # Połącz sygnał dopiero po załadowaniu profili
        # self.category_combo.currentTextChanged.connect(self.filter_by_category)
        search_layout.addWidget(self.category_combo)

        layout.addLayout(search_layout)

        # Splitter dla listy i szczegółów
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Lista profili
        profiles_group = QGroupBox("Profile SSH")
        profiles_layout = QVBoxLayout(profiles_group)

        self.profiles_tree = QTreeWidget()
        self.profiles_tree.setHeaderLabels(["Nazwa", "Host", "Kategoria", "Ostatnie użycie"])
        self.profiles_tree.itemSelectionChanged.connect(self.on_profile_selected)
        self.profiles_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.profiles_tree.customContextMenuRequested.connect(self.show_context_menu)
        profiles_layout.addWidget(self.profiles_tree)

        # Przyciski dla profili
        profiles_buttons = QHBoxLayout()

        self.new_profile_btn = QPushButton("Nowy profil")
        self.new_profile_btn.clicked.connect(self.create_profile)
        profiles_buttons.addWidget(self.new_profile_btn)

        self.edit_profile_btn = QPushButton("Edytuj")
        self.edit_profile_btn.clicked.connect(self.edit_profile)
        self.edit_profile_btn.setEnabled(False)
        profiles_buttons.addWidget(self.edit_profile_btn)

        self.delete_profile_btn = QPushButton("Usuń")
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.delete_profile_btn.setEnabled(False)
        profiles_buttons.addWidget(self.delete_profile_btn)

        profiles_layout.addLayout(profiles_buttons)
        splitter.addWidget(profiles_group)

        # Szczegóły profilu
        details_group = QGroupBox("Szczegóły profilu")
        details_layout = QVBoxLayout(details_group)

        self.profile_details = QTextEdit()
        self.profile_details.setReadOnly(True)
        self.profile_details.setPlaceholderText("Wybierz profil aby zobaczyć szczegóły")
        details_layout.addWidget(self.profile_details)

        # Przyciski dla szczegółów
        details_buttons = QHBoxLayout()

        self.connect_profile_btn = QPushButton("Połącz")
        self.connect_profile_btn.clicked.connect(self.connect_profile)
        self.connect_profile_btn.setEnabled(False)
        details_buttons.addWidget(self.connect_profile_btn)

        self.export_profile_btn = QPushButton("Eksportuj")
        self.export_profile_btn.clicked.connect(self.export_profile)
        self.export_profile_btn.setEnabled(False)
        details_buttons.addWidget(self.export_profile_btn)

        details_layout.addLayout(details_buttons)
        splitter.addWidget(details_group)

        # Ustaw proporcje splittera
        splitter.setSizes([300, 400])

    def load_profiles(self):
        """Ładuje profile do listy"""
        try:
            # Sprawdź czy serwis jest zainicjalizowany
            if not self.profile_service:
                self.profile_details.setPlainText(
                    "Serwis profili nie jest jeszcze zainicjalizowany..."
                )
                return

            # Wyczyść listę
            self.profiles_tree.clear()

            # Pobierz profile z zabezpieczeniem
            try:
                profiles = self.profile_service.list_profiles()
            except RecursionError:
                # Jeśli wystąpi błąd rekurencji, spróbuj pobrać profile pojedynczo
                profiles = []
                profile_ids = list(self.profile_service.profiles.keys())
                for profile_id in profile_ids:
                    try:
                        profile = self.profile_service.get_profile(profile_id)
                        if profile:
                            profiles.append(profile)
                    except Exception:
                        continue

            # Załaduj kategorie
            try:
                categories = self.profile_service.get_categories()
                self.category_combo.clear()
                self.category_combo.addItem("Wszystkie kategorie")
                self.category_combo.addItems(categories)
            except Exception:
                self.category_combo.clear()
                self.category_combo.addItem("Wszystkie kategorie")

            # Dodaj profile do listy z zabezpieczeniem
            for profile in profiles:
                try:
                    # Bezpieczne pobieranie danych profilu
                    name = getattr(profile, "name", "Nieznany")
                    hostname = getattr(profile, "hostname", "localhost")
                    port = getattr(profile, "port", 22)
                    category = getattr(profile, "category", "default")
                    last_used = getattr(profile, "last_used", None)

                    # Formatowanie daty
                    last_used_str = "Nigdy"
                    if last_used:
                        try:
                            last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            last_used_str = "Błąd daty"

                    item = QTreeWidgetItem(
                        [
                            str(name),
                            f"{str(hostname)}:{str(port)}",
                            str(category),
                            str(last_used_str),
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, profile)
                    self.profiles_tree.addTopLevelItem(item)

                except Exception as e:
                    # Pomiń problematyczny profil
                    if self.logger:
                        self.logger.warning(f"Pominięto problematyczny profil: {e}")
                    continue

            if self.logger:
                self.logger.info(f"Załadowano {len(profiles)} profili SSH")

        except Exception as e:
            error_msg = f"Błąd ładowania profili: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def search_profiles(self):
        """Wyszukuje profile"""
        if not self.profile_service:
            return

        query = self.search_edit.text().strip()
        if not query:
            self.load_profiles()
            return

        try:
            # Wyszukaj profile
            profiles = self.profile_service.search_profiles(query)

            # Wyczyść listę
            self.profiles_tree.clear()

            # Dodaj wyniki z zabezpieczeniem
            for profile in profiles:
                try:
                    # Bezpieczne pobieranie danych profilu
                    name = getattr(profile, "name", "Nieznany")
                    hostname = getattr(profile, "hostname", "localhost")
                    port = getattr(profile, "port", 22)
                    category = getattr(profile, "category", "default")
                    last_used = getattr(profile, "last_used", None)

                    # Formatowanie daty
                    last_used_str = "Nigdy"
                    if last_used:
                        try:
                            last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            last_used_str = "Błąd daty"

                    item = QTreeWidgetItem(
                        [
                            str(name),
                            f"{str(hostname)}:{str(port)}",
                            str(category),
                            str(last_used_str),
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, profile)
                    self.profiles_tree.addTopLevelItem(item)

                except Exception as e:
                    # Pomiń problematyczny profil
                    if self.logger:
                        self.logger.warning(
                            f"Pominięto problematyczny profil podczas wyszukiwania: {e}"
                        )
                    continue

        except Exception as e:
            error_msg = f"Błąd wyszukiwania: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def filter_by_category(self, category: str):
        """Filtruje profile po kategorii"""
        if not self.profile_service:
            return

        if category == "Wszystkie kategorie":
            self.load_profiles()
            return

        try:
            # Filtruj profile
            profiles = self.profile_service.list_profiles(category=category)

            # Wyczyść listę
            self.profiles_tree.clear()

            # Dodaj wyniki z zabezpieczeniem
            for profile in profiles:
                try:
                    # Bezpieczne pobieranie danych profilu
                    name = getattr(profile, "name", "Nieznany")
                    hostname = getattr(profile, "hostname", "localhost")
                    port = getattr(profile, "port", 22)
                    category = getattr(profile, "category", "default")
                    last_used = getattr(profile, "last_used", None)

                    # Formatowanie daty
                    last_used_str = "Nigdy"
                    if last_used:
                        try:
                            last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            last_used_str = "Błąd daty"

                    item = QTreeWidgetItem(
                        [
                            str(name),
                            f"{str(hostname)}:{str(port)}",
                            str(category),
                            str(last_used_str),
                        ]
                    )
                    item.setData(0, Qt.ItemDataRole.UserRole, profile)
                    self.profiles_tree.addTopLevelItem(item)

                except Exception as e:
                    # Pomiń problematyczny profil
                    if self.logger:
                        self.logger.warning(
                            f"Pominięto problematyczny profil podczas filtrowania: {e}"
                        )
                    continue

        except Exception as e:
            error_msg = f"Błąd filtrowania: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def on_profile_selected(self):
        """Obsługuje wybór profilu"""
        current_item = self.profiles_tree.currentItem()
        if not current_item:
            self.clear_profile_details()
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if profile:
            self.show_profile_details(profile)
            self.edit_profile_btn.setEnabled(True)
            self.delete_profile_btn.setEnabled(True)
            self.connect_profile_btn.setEnabled(True)
            self.export_profile_btn.setEnabled(True)

    def show_profile_details(self, profile: SSHProfile):
        """Wyświetla szczegóły profilu"""
        try:
            # Bezpieczne pobieranie danych profilu
            name = getattr(profile, "name", "Nieznany")
            description = getattr(profile, "description", "Brak opisu")
            hostname = getattr(profile, "hostname", "localhost")
            username = getattr(profile, "username", "unknown")
            port = getattr(profile, "port", 22)
            category = getattr(profile, "category", "default")
            tags = getattr(profile, "tags", [])
            key_filename = getattr(profile, "key_filename", None)
            proxy_config = getattr(profile, "proxy_config", None)
            save_password = getattr(profile, "save_password", False)
            created_at = getattr(profile, "created_at", None)
            updated_at = getattr(profile, "updated_at", None)
            last_used = getattr(profile, "last_used", None)
            use_count = getattr(profile, "use_count", 0)

            # Formatowanie tagów
            tags_str = ", ".join(tags) if tags else "Brak"

            # Formatowanie dat
            created_str = "Nieznana"
            if created_at:
                try:
                    created_str = created_at.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    created_str = "Błąd daty"

            updated_str = "Nieznana"
            if updated_at:
                try:
                    updated_str = updated_at.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    updated_str = "Błąd daty"

            last_used_str = "Nigdy"
            if last_used:
                try:
                    last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    last_used_str = "Błąd daty"

            details = f"""Nazwa: {name}
Opis: {description}
Hostname: {hostname}
Username: {username}
Port: {port}
Kategoria: {category}
Tagi: {tags_str}
Klucz prywatny: {key_filename or 'Brak'}
Proxy: {'Tak' if proxy_config else 'Nie'}
Zapisz hasło: {'Tak' if save_password else 'Nie'}
Utworzono: {created_str}
Ostatnia aktualizacja: {updated_str}
Ostatnie użycie: {last_used_str}
Liczba użyć: {use_count}"""

            self.profile_details.setPlainText(details)

        except Exception as e:
            error_msg = f"Błąd wyświetlania szczegółów profilu: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            self.profile_details.setPlainText(f"Błąd ładowania szczegółów profilu: {e}")

    def clear_profile_details(self):
        """Czyści szczegóły profilu"""
        self.profile_details.clear()
        self.edit_profile_btn.setEnabled(False)
        self.delete_profile_btn.setEnabled(False)
        self.connect_profile_btn.setEnabled(False)
        self.export_profile_btn.setEnabled(False)

    def create_profile(self):
        """Tworzy nowy profil"""
        if not self.profile_service:
            QMessageBox.warning(self, "Błąd", "Serwis profili nie jest jeszcze zainicjalizowany")
            return

        try:
            dialog = ProfileEditDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                profile_data = dialog.get_profile_data()

                # Stwórz profil
                profile = self.profile_service.create_profile(**profile_data)

                # Odśwież listę
                self.load_profiles()

                # Wybierz nowy profil
                profile_id = getattr(profile, "id", None)
                if profile_id:
                    self.select_profile_by_id(profile_id)

                if self.logger:
                    profile_name = getattr(profile, "name", "Nieznany")
                    self.logger.info(f"ProfileManagerWidget - utworzono profil: {profile_name}")

        except Exception as e:
            error_msg = f"Błąd tworzenia profilu: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def edit_profile(self):
        """Edytuje wybrany profil"""
        if not self.profile_service:
            QMessageBox.warning(self, "Błąd", "Serwis profili nie jest jeszcze zainicjalizowany")
            return

        current_item = self.profiles_tree.currentItem()
        if not current_item:
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not profile:
            return

        try:
            dialog = ProfileEditDialog(profile, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                profile_data = dialog.get_profile_data()

                # Aktualizuj profil
                profile_id = getattr(profile, "id", None)
                if not profile_id:
                    raise ValueError("Profil nie ma ID")
                self.profile_service.update_profile(profile_id, **profile_data)

                # Odśwież listę
                self.load_profiles()

                # Wybierz zaktualizowany profil
                self.select_profile_by_id(profile_id)

                if self.logger:
                    profile_name = getattr(profile, "name", "Nieznany")
                    self.logger.info(
                        f"ProfileManagerWidget - zaktualizowano profil: {profile_name}"
                    )

        except Exception as e:
            error_msg = f"Błąd aktualizacji profilu: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def delete_profile(self):
        """Usuwa wybrany profil"""
        if not self.profile_service:
            QMessageBox.warning(self, "Błąd", "Serwis profili nie jest jeszcze zainicjalizowany")
            return

        current_item = self.profiles_tree.currentItem()
        if not current_item:
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not profile:
            return

        # Potwierdź usunięcie
        profile_name = getattr(profile, "name", "Nieznany")
        reply = QMessageBox.question(
            self,
            "Potwierdź usunięcie",
            f"Czy na pewno chcesz usunąć profil '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Usuń profil
                profile_id = getattr(profile, "id", None)
                if not profile_id:
                    raise ValueError("Profil nie ma ID")
                self.profile_service.delete_profile(profile_id)

                # Odśwież listę
                self.load_profiles()

                # Wyczyść szczegóły
                self.clear_profile_details()

                if self.logger:
                    profile_name = getattr(profile, "name", "Nieznany")
                    self.logger.info(f"ProfileManagerWidget - usunięto profil: {profile_name}")

            except Exception as e:
                error_msg = f"Błąd usuwania profilu: {e}"
                if self.logger:
                    self.logger.error(f"ProfileManagerWidget - {error_msg}")
                QMessageBox.critical(self, "Błąd", error_msg)

    def connect_profile(self):
        """Łączy się z serwerem używając profilu"""
        if not self.profile_service:
            QMessageBox.warning(self, "Błąd", "Serwis profili nie jest jeszcze zainicjalizowany")
            return

        current_item = self.profiles_tree.currentItem()
        if not current_item:
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not profile:
            return

        # Emituj sygnał wyboru profilu
        self.profile_selected.emit(profile)

        if self.logger:
            profile_name = getattr(profile, "name", "Nieznany")
            self.logger.info(f"ProfileManagerWidget - wybrano profil do połączenia: {profile_name}")

    def export_profile(self):
        """Eksportuje profil"""
        if not self.profile_service:
            QMessageBox.warning(self, "Błąd", "Serwis profili nie jest jeszcze zainicjalizowany")
            return

        current_item = self.profiles_tree.currentItem()
        if not current_item:
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not profile:
            return

        try:
            # Eksportuj profil
            profile_id = getattr(profile, "id", None)
            if not profile_id:
                raise ValueError("Profil nie ma ID")
            profile_data = self.profile_service.export_profile(
                profile_id, include_credentials=False
            )

            # Pokaż dane
            import json

            export_text = json.dumps(profile_data, indent=2, ensure_ascii=False)

            # TODO: Zapisz do pliku lub skopiuj do schowka
            QMessageBox.information(
                self, "Eksport profilu", f"Profil wyeksportowany:\n\n{export_text}"
            )

        except Exception as e:
            error_msg = f"Błąd eksportu profilu: {e}"
            if self.logger:
                self.logger.error(f"ProfileManagerWidget - {error_msg}")
            QMessageBox.critical(self, "Błąd", error_msg)

    def select_profile_by_id(self, profile_id: str):
        """Wybiera profil po ID"""
        for i in range(self.profiles_tree.topLevelItemCount()):
            item = self.profiles_tree.topLevelItem(i)
            profile = item.data(0, Qt.ItemDataRole.UserRole)
            if profile:
                profile_id_attr = getattr(profile, "id", None)
                if profile_id_attr == profile_id:
                    self.profiles_tree.setCurrentItem(item)
                    break

    def show_context_menu(self, position):
        """Pokazuje menu kontekstowe"""
        current_item = self.profiles_tree.currentItem()
        if not current_item:
            return

        profile = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not profile:
            return

        menu = QMenu()

        # Akcje
        connect_action = QAction("Połącz", self)
        connect_action.triggered.connect(self.connect_profile)
        menu.addAction(connect_action)

        edit_action = QAction("Edytuj", self)
        edit_action.triggered.connect(self.edit_profile)
        menu.addAction(edit_action)

        delete_action = QAction("Usuń", self)
        delete_action.triggered.connect(self.delete_profile)
        menu.addAction(delete_action)

        menu.addSeparator()

        export_action = QAction("Eksportuj", self)
        export_action.triggered.connect(self.export_profile)
        menu.addAction(export_action)

        # Pokaż menu
        menu.exec(self.profiles_tree.mapToGlobal(position))
