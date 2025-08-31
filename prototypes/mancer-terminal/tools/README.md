# 🛠️ Narzędzia Mancer Terminal

Ten katalog zawiera skrypty pomocnicze do uruchamiania i zarządzania Mancer Terminal.

## 📁 Dostępne Narzędzia

### 1. `run_terminal.sh` - Skrypt Bash
**Skrypt bash do uruchomienia Mancer Terminal w środowisku wirtualnym.**

**Użycie:**
```bash
# Uruchom z katalogu głównego projektu Mancer
./prototypes/mancer-terminal/tools/run_terminal.sh

# Uruchom z testem GUI
./prototypes/mancer-terminal/tools/run_terminal.sh --test

# Pokaż pomoc
./prototypes/mancer-terminal/tools/run_terminal.sh --help
```

**Funkcje:**
- ✅ Sprawdza wersję Pythona (wymagany 3.8+)
- ✅ Tworzy/aktywuje środowisko wirtualne
- ✅ Aktualizuje pip
- ✅ Instaluje Mancer w trybie deweloperskim
- ✅ Instaluje zależności Mancer Terminal
- ✅ Sprawdza/instaluje PyQt6
- ✅ Sprawdza dostępność Mancer
- ✅ Opcjonalny test GUI
- ✅ Uruchamia Mancer Terminal

### 2. `run_terminal.py` - Skrypt Python
**Skrypt Python do uruchomienia Mancer Terminal w środowisku wirtualnym.**

**Użycie:**
```bash
# Uruchom z katalogu głównego projektu Mancer
python prototypes/mancer-terminal/tools/run_terminal.py

# Uruchom z testem GUI
python prototypes/mancer-terminal/tools/run_terminal.py --test

# Pokaż pomoc
python prototypes/mancer-terminal/tools/run_terminal.py --help
```

**Funkcje:**
- ✅ Wszystkie funkcje z wersji bash
- ✅ Lepsze zarządzanie błędami
- ✅ Automatyczna aktywacja venv
- ✅ Szczegółowe logowanie

## 🚀 Szybkie Uruchomienie

### Krok 1: Przejdź do katalogu głównego
```bash
cd /ścieżka/do/projektu/mancer
```

### Krok 2: Uruchom skrypt
```bash
# Używając bash (Linux/macOS)
chmod +x prototypes/mancer-terminal/tools/run_terminal.sh
./prototypes/mancer-terminal/tools/run_terminal.sh

# Lub używając Python
python prototypes/mancer-terminal/tools/run_terminal.py
```

### Krok 3: Czekaj na instalację
Skrypt automatycznie:
1. Sprawdzi wymagania
2. Utworzy/aktywuje venv
3. Zainstaluje Mancer w trybie deweloperskim
4. Zainstaluje zależności Mancer Terminal
5. Uruchomi aplikację

## 🔧 Wymagania Systemowe

### Linux/macOS
- Python 3.8+
- Bash shell
- Uprawnienia do tworzenia katalogów

### Windows
- Python 3.8+
- PowerShell lub Command Prompt
- Uprawnienia do tworzenia katalogów

## 📋 Co Instaluje Skrypt

### Mancer Framework
```bash
pip install -e src/  # Instalacja w trybie deweloperskim
```

### Zależności Mancer Terminal
```bash
pip install -r prototypes/mancer-terminal/requirements.txt
```

### Główne Pakiety
- **PyQt6** - Framework GUI
- **Paramiko** - Biblioteka SSH
- **AsyncSSH** - Asynchroniczna obsługa SSH
- **Cryptography** - Szyfrowanie
- **Pyte/Blessed** - Emulacja terminala

## 🧪 Testowanie

### Uruchom z testem GUI
```bash
# Bash
./prototypes/mancer-terminal/tools/run_terminal.sh --test

# Python
python prototypes/mancer-terminal/tools/run_terminal.py --test
```

### Test sprawdza:
- ✅ Import PyQt6
- ✅ Import komponentów GUI
- ✅ Integrację z Mancer
- ✅ Dostępność SSH backend

## 🐛 Rozwiązywanie Problemów

### Problem: "Permission denied"
```bash
chmod +x prototypes/mancer-terminal/tools/run_terminal.sh
```

### Problem: "Python3 not found"
```bash
# Sprawdź czy Python jest zainstalowany
python3 --version

# Lub użyj aliasu
alias python3=python
```

### Problem: "venv not found"
```bash
# Skrypt automatycznie utworzy venv
# Lub utwórz ręcznie
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# lub
venv\Scripts\activate     # Windows
```

### Problem: "PyQt6 installation failed"
```bash
# Sprawdź system dependencies
# Ubuntu/Debian
sudo apt-get install python3-pyqt6

# macOS
brew install pyqt@6

# Windows
# Użyj pip install PyQt6
```

## 📊 Status Instalacji

Skrypt wyświetla kolorowy status każdego kroku:

- 🔵 **[INFO]** - Informacja
- 🟢 **[SUCCESS]** - Operacja zakończona pomyślnie
- 🟡 **[WARNING]** - Ostrzeżenie (można kontynuować)
- 🔴 **[ERROR]** - Błąd krytyczny (zatrzymuje skrypt)

## 🔄 Aktualizacje

### Aktualizuj Mancer
```bash
cd src/mancer
git pull origin main
cd ../..
pip install -e src/ --upgrade
```

### Aktualizuj zależności
```bash
cd prototypes/mancer-terminal
pip install -r requirements.txt --upgrade
cd ../..
```

## 📝 Przykłady Użycia

### Uruchomienie podstawowe
```bash
./prototypes/mancer-terminal/tools/run_terminal.sh
```

### Uruchomienie z testem
```bash
./prototypes/mancer-terminal/tools/run_terminal.sh --test
```

### Uruchomienie w trybie debug
```bash
bash -x ./prototypes/mancer-terminal/tools/run_terminal.sh
```

### Uruchomienie Python
```bash
python prototypes/mancer-terminal/tools/run_terminal.py --test
```

## 🤝 Wsparcie

### Zgłaszanie problemów
Jeśli napotkasz problemy z uruchomieniem:

1. Sprawdź czy jesteś w katalogu głównym projektu
2. Uruchom z flagą `--test` aby zobaczyć szczegóły
3. Sprawdź logi błędów
4. Zgłoś problem w GitHub Issues

### Logi
Skrypt wyświetla szczegółowe informacje o każdym kroku. Jeśli coś nie działa, skopiuj pełny output i dołącz do zgłoszenia problemu.

---

**Narzędzia Mancer Terminal** - Ułatwiają uruchomienie i zarządzanie aplikacją 🚀
