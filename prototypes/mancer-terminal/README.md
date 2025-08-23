# Mancer Terminal

**Mancer Terminal** to zaawansowany emulator terminala SSH zintegrowany z frameworkiem Mancer, oferujący pełne zarządzanie sesjami SSH, transfer plików przez SCP i obsługę proxy SSH.

## 🎯 Cel Projektu

**Mancer Terminal** ma być **wyświetlaczem i backendem** pomagającym realizować funkcje przez SSH i SCP. Aplikacja wykorzystuje PyQt6 jako interfejs graficzny i integruje się z rozszerzonymi funkcjonalnościami Mancer:

- **SSH Session Management** - zarządzanie wieloma sesjami SSH
- **SCP File Transfer** - przesyłanie plików przez SCP (Linux → Linux)
- **SSH Proxy Support** - obsługa proxy SSH (HTTP, SOCKS, ProxyCommand)
- **Chain Connections** - łączenie łańcuchowe (Linux → Linux → Linux)
- **Real-time Terminal** - emulacja terminala w czasie rzeczywistym
- **Multi-session Interface** - interfejs z zakładkami dla wielu sesji

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    Mancer Terminal GUI                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Session Manager │  │ Terminal Widget │  │ File Transfer│ │
│  │   (PyQt6)      │  │    (PyQt6)      │  │   (PyQt6)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mancer Framework                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ SSH Session     │  │ SSH Backend     │  │ SCP Backend │ │
│  │   Service       │  │ (Enhanced)      │  │ (New)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SSH Infrastructure                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ Session Pool    │  │ Proxy Manager   │  │ File Transfer│ │
│  │ Management      │  │ (HTTP/SOCKS)    │  │ (SCP/SFTP)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Kluczowe Funkcje

### 🔐 SSH Session Management
- **Multi-session Support** - zarządzanie wieloma sesjami SSH jednocześnie
- **Session Pooling** - pulowanie połączeń SSH dla lepszej wydajności
- **Connection Monitoring** - monitorowanie statusu połączeń w czasie rzeczywistym
- **Session Switching** - łatwe przełączanie między sesjami

### 📁 SCP File Transfer
- **Upload/Download** - przesyłanie plików w obu kierunkach (Linux → Linux)
- **Progress Tracking** - śledzenie postępu transferów w czasie rzeczywistym
- **Resume Support** - wznawianie przerwanych transferów
- **Batch Operations** - operacje na wielu plikach jednocześnie

### 🌐 SSH Proxy Support
- **HTTP Proxy** - obsługa proxy HTTP
- **SOCKS Proxy** - obsługa proxy SOCKS4/SOCKS5
- **ProxyCommand** - obsługa niestandardowych komend proxy
- **Chain Connections** - łączenie łańcuchowe przez wiele proxy

### 🖥️ Terminal Emulation
- **Real-time Output** - wyświetlanie outputu w czasie rzeczywistym
- **Multi-tab Interface** - interfejs z zakładkami dla różnych sesji
- **Command History** - historia komend z możliwością nawigacji
- **Color Support** - obsługa kolorów terminala

### 🔧 Advanced Features
- **Connection Testing** - testowanie połączeń przed utworzeniem sesji
- **Configuration Profiles** - profile konfiguracji połączeń
- **Logging & Monitoring** - zaawansowane logowanie i monitorowanie
- **Error Handling** - inteligentne zarządzanie błędami

## 🛠️ Technologie

### Frontend (PyQt6)
- **PyQt6** - główny framework GUI
- **QThread** - wielowątkowość dla operacji SSH
- **QTimer** - aktualizacje w czasie rzeczywistym
- **QTreeWidget** - zarządzanie sesjami i transferami

### Backend (Mancer Integration)
- **SSH Backend** - rozszerzony o session management
- **SCP Backend** - nowy backend dla transferu plików
- **SSH Session Service** - serwis zarządzania sesjami
- **Proxy Manager** - zarządzanie połączeniami proxy

### SSH & Networking
- **Paramiko** - biblioteka SSH dla Pythona
- **AsyncSSH** - asynchroniczna obsługa SSH
- **SCP Protocol** - protokół transferu plików
- **Proxy Support** - obsługa różnych typów proxy

## 📁 Struktura Prototypu

```
mancer-terminal/
├── main.py                 # Główny plik uruchamiający
├── requirements.txt        # Zależności Python
├── pyproject.toml         # Konfiguracja projektu
├── test_gui.py            # Test GUI
├── gui/                    # Pakiet interfejsu graficznego
│   ├── __init__.py
│   ├── main_window.py     # Główne okno aplikacji
│   ├── terminal_widget.py # Widget terminala SSH
│   ├── session_manager_widget.py  # Zarządzanie sesjami
│   ├── file_transfer_widget.py    # Transfer plików
│   └── connection_dialog.py       # Dialog połączenia
├── config/                 # Konfiguracja
│   └── terminal.yaml      # Ustawienia terminala
└── README.md              # Dokumentacja
```

## 🚀 Uruchomienie

### Wymagania
```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Upewnij się, że Mancer jest dostępny w src/
```

### Uruchomienie aplikacji
```bash
# Uruchom główną aplikację
python main.py

# Lub bezpośrednio
python -m gui.main_window
```

### Testowanie
```bash
# Test GUI i integracji z Mancer
python test_gui.py

# Test z pytest (jeśli zainstalowane)
pytest test_gui.py -v
```

## 🔌 Integracja z Mancer

### Rozszerzenia Mancer
Mancer Terminal wykorzystuje rozszerzone funkcjonalności Mancer:

1. **Enhanced SSH Backend** (`src/mancer/infrastructure/backend/ssh_backend.py`)
   - Session management
   - SCP support
   - Proxy configuration

2. **SSH Session Service** (`src/mancer/domain/service/ssh_session_service.py`)
   - Centralne zarządzanie sesjami
   - Integration z SSH backend

### Przykład użycia
```python
from mancer.domain.service.ssh_session_service import SSHSessionService

# Stwórz serwis SSH
ssh_service = SSHSessionService()

# Stwórz nową sesję
session = ssh_service.create_session(
    hostname="192.168.1.100",
    username="admin",
    port=22,
    key_filename="~/.ssh/id_rsa"
)

# Połącz sesję
ssh_service.connect_session(session.id)

# Wykonaj komendę
result = ssh_service.execute_command("ls -la", session.id)

# Upload pliku
transfer = ssh_service.scp_upload(
    "/local/file.txt", 
    "/remote/file.txt", 
    session.id
)
```

## 📊 Funkcje Enterprise

### Multi-server Management
- **Group Management** - zarządzanie grupami serwerów
- **Bulk Operations** - operacje na wielu serwerach
- **Load Balancing** - balansowanie obciążenia
- **Failover Support** - obsługa awarii

### Security & Compliance
- **Role-based Access Control (RBAC)** - kontrola dostępu
- **Audit Logging** - logowanie audytowe
- **Encryption** - szyfrowanie danych
- **Compliance Monitoring** - monitorowanie zgodności

### Monitoring & Alerting
- **Real-time Monitoring** - monitorowanie w czasie rzeczywistym
- **Performance Metrics** - metryki wydajności
- **Alert Management** - zarządzanie alertami
- **Health Checks** - sprawdzanie stanu zdrowia

## 🗺️ Roadmap

### Faza 1: Core SSH Backend (Miesiące 1-2) ✅
- [x] Rozszerzenie SSH Backend o session management
- [x] Implementacja SCP support
- [x] Podstawowa obsługa proxy SSH

### Faza 2: PyQt6 Interface (Miesiące 2-3) ✅
- [x] Główne okno aplikacji
- [x] Widget terminala SSH
- [x] Manager sesji
- [x] Widget transferu plików

### Faza 3: Advanced Features (Miesiące 3-4) 🔄
- [ ] Chain connections (Linux → Linux → Linux)
- [ ] Advanced proxy support
- [ ] Session pooling
- [ ] Performance optimization

### Faza 4: Enterprise Features (Miesiące 4-5)
- [ ] Multi-server groups
- [ ] RBAC implementation
- [ ] Advanced monitoring
- [ ] Compliance features

### Faza 5: Production Ready (Miesiące 5-6)
- [ ] Performance testing
- [ ] Security audit
- [ ] Documentation
- [ ] Deployment scripts

## 🔧 Konfiguracja

### Terminal Configuration
```yaml
# config/terminal.yaml
terminal:
  theme: "dark"
  font_family: "Monospace"
  font_size: 10
  
sessions:
  default_timeout: 30
  max_sessions: 10
  auto_reconnect: true
  
file_transfer:
  chunk_size: 8192
  progress_update_interval: 1000
  resume_support: true
  
proxy:
  default_type: "http"
  timeout: 10
  retry_attempts: 3
```

## 📈 Przykład Użycia

### 1. Utworzenie nowej sesji SSH
```
1. Kliknij "Nowa Sesja" w głównym oknie
2. Wypełnij dane połączenia:
   - Hostname: 192.168.1.100
   - Port: 22
   - Username: admin
   - Użyj klucza prywatnego: ~/.ssh/id_rsa
3. Kliknij "Połącz"
```

### 2. Wykonanie komendy
```
1. Wybierz sesję z listy po lewej stronie
2. W terminalu wpisz komendę: ls -la
3. Naciśnij Enter lub kliknij "Wykonaj"
4. Zobacz wynik w terminalu
```

### 3. Transfer pliku
```
1. W panelu "Transfer Plików" kliknij "Upload"
2. Wybierz plik lokalny
3. Podaj ścieżkę zdalną: /home/admin/file.txt
4. Podaj ID sesji SSH
5. Kliknij "OK" - transfer rozpocznie się automatycznie
```

### 4. Zarządzanie sesjami
```
1. Zobacz wszystkie sesje w panelu "Zarządzanie Sesjami SSH"
2. Kliknij na sesję, aby zobaczyć szczegóły
3. Użyj przycisków: Połącz/Rozłącz/Zamknij
4. Przełącz między sesjami klikając na nie
```

## 🧪 Testowanie

### Test GUI
```bash
# Uruchom test GUI
python test_gui.py

# Oczekiwany wynik:
# 🧪 Testing Mancer Terminal GUI...
# ==================================================
# 
# 📱 Testing GUI imports:
# ✅ PyQt6 import successful
# ✅ MancerTerminalWindow import successful
# ✅ TerminalWidget import successful
# ✅ SessionManagerWidget import successful
# ✅ FileTransferWidget import successful
# ✅ ConnectionDialog import successful
# 
# 🔌 Testing Mancer integration:
# ✅ Mancer SSH Backend import successful
# ✅ Mancer SSH Session Service import successful
# 
# ==================================================
# 🎉 All tests passed! Mancer Terminal is ready to use.
```

### Test z pytest
```bash
# Zainstaluj pytest-qt
pip install pytest-qt

# Uruchom testy
pytest test_gui.py -v
```

## 🤝 Współpraca

### Zgłaszanie problemów
- Użyj GitHub Issues do zgłaszania błędów
- Opisz dokładnie problem i kroki reprodukcji
- Dołącz logi i zrzuty ekranu

### Propozycje funkcji
- Otwórz Feature Request w GitHub Issues
- Opisz funkcję i jej użyteczność
- Przedstaw przykłady użycia

### Pull Requests
- Fork projektu
- Stwórz branch dla funkcji
- Zaimplementuj zmiany
- Prześlij Pull Request

## 📄 Licencja

Projekt jest dostępny na licencji MIT. Zobacz plik `LICENSE` dla szczegółów.

## 🔗 Linki

- **Mancer Framework**: [GitHub Repository](https://github.com/your-org/mancer)
- **PyQt6 Documentation**: [https://doc.qt.io/qtforpython-6/](https://doc.qt.io/qtforpython-6/)
- **SSH Protocol**: [RFC 4251-4254](https://tools.ietf.org/html/rfc4251)
- **SCP Protocol**: [OpenSSH Documentation](https://www.openssh.com/manual.html)

---

**Mancer Terminal** - Zaawansowany emulator terminala SSH zintegrowany z frameworkiem Mancer 🚀
