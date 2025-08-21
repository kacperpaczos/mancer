# 🚀 Strategia Prototypów Frameworka Mancer

## Przegląd

Strategia "Prototypy jako Laboratorium Frameworka" pozwala na rozwój frameworka Mancer przez budowanie rzeczywistych aplikacji, jednocześnie utrzymując czystą separację między kodem frameworka a prototypami.

## 🎯 Główne Zasady

1. **Prototypy NIE są częścią frameworka** - mają własne zależności i konfigurację
2. **Framework jest zależnością zewnętrzną** - prototypy importują go jako bibliotekę
3. **Każdy prototyp ma własny katalog** z kompletną strukturą projektu
4. **Prototypy testują i rozwijają framework** przez praktyczne zastosowania
5. **Rozwój na osobnych gałęziach Git** - izolacja od głównego kodu

## 🌿 Strategia Gałęzi

### Struktura Gałęzi
```
main                    # Główna gałąź - stabilny kod frameworka
├── prototypes         # Gałąź prototypów - główna gałąź rozwojowa
├── feature-name      # Gałęzie funkcjonalności - konkretne prototypy
├── experiment-name   # Gałęzie eksperymentalne - testowanie pomysłów
└── cleanup-name      # Gałęzie porządkowe - refaktoring i optymalizacja
```

### Workflow Rozwoju
1. **Tworzenie** - nowa gałąź z main
2. **Rozwój** - implementacja prototypów
3. **Testowanie** - weryfikacja funkcjonalności
4. **Integracja** - merge udanych funkcjonalności do main
5. **Czyszczenie** - usunięcie zużytych gałęzi

## 🛠️ Szybki Start

### 1. Sprawdź status
```bash
./tools/quick_prototype.sh -s
```

### 2. Lista prototypów
```bash
./tools/quick_prototype.sh -l
```

### 3. Utwórz nowy prototyp
```bash
./tools/quick_prototype.sh -c "my-app" "Opis mojej aplikacji"
```

### 4. Uruchom prototyp
```bash
./tools/quick_prototype.sh -r "my-app"
```

### 5. Testy strategii
```bash
./tools/quick_prototype.sh -t
```

## 🌿 Zarządzanie Gałęziami

### Status gałęzi
```bash
./tools/prototype_branch_manager.sh -s
```

### Utwórz nową gałąź
```bash
./tools/prototype_branch_manager.sh -c "feature-name"
```

### Wypchnij zmiany
```bash
./tools/prototype_branch_manager.sh -p
```

### Merguj do main
```bash
./tools/prototype_branch_manager.sh -m
```

## 📁 Struktura Projektu

```
mancer/
├── src/mancer/          # Rdzeń frameworka (niezmienny)
├── prototypes/          # Prototypy aplikacji
│   ├── template/        # Szablon nowego prototypu
│   ├── configMaster/    # Aplikacja zarządzania konfiguracją
│   ├── NetPinger/       # Aplikacja monitoringu sieci
│   └── ...
├── examples/            # Przykłady użycia frameworka
└── tools/               # Narzędzia developerskie
    ├── prototype_manager.py          # Python menedżer prototypów
    ├── quick_prototype.sh            # Szybki start (bash)
    ├── test_prototype_strategy.py    # Testy strategii
    └── prototype_branch_manager.sh   # Menedżer gałęzi prototypów
```

## 🔧 Narzędzia

### Menedżer Prototypów (Python)
```bash
# Lista prototypów
python tools/prototype_manager.py list

# Tworzenie nowego
python tools/prototype_manager.py create --name "app" --description "Opis"

# Uruchomienie
python tools/prototype_manager.py run --name "app"

# Raport użycia frameworka
python tools/prototype_manager.py report
```

### Szybki Start (Bash)
```bash
# Pomoc
./tools/quick_prototype.sh -h

# Status
./tools/quick_prototype.sh -s

# Lista
./tools/quick_prototype.sh -l

# Tworzenie
./tools/quick_prototype.sh -c "nazwa" "opis"

# Uruchomienie
./tools/quick_prototype.sh -r "nazwa"

# Testy
./tools/quick_prototype.sh -t
```

### Menedżer Gałęzi (Bash)
```bash
# Status gałęzi
./tools/prototype_branch_manager.sh -s

# Utwórz gałąź
./tools/prototype_branch_manager.sh -c "feature-name"

# Wypchnij zmiany
./tools/prototype_branch_manager.sh -p

# Merguj do main
./tools/prototype_branch_manager.sh -m
```

## 📋 Cykl Życia Prototypu

### 1. **Tworzenie**
- Użyj szablonu: `./tools/quick_prototype.sh -c "nazwa" "opis"`
- Edytuj `main.py` w katalogu prototypu
- Dodaj własne zależności do `requirements.txt`

### 2. **Rozwój**
- Implementuj logikę aplikacji
- Używaj frameworka jako zależności
- Testuj nowe funkcjonalności
- Dokumentuj problemy i sugestie

### 3. **Testowanie**
- Uruchom: `./tools/quick_prototype.sh -r "nazwa"`
- Sprawdź integrację z frameworkiem
- Weryfikuj działanie funkcjonalności

### 4. **Ewolucja**
- Przenieś udane funkcjonalności do frameworka
- Zaktualizuj prototyp do nowej wersji frameworka
- Usu przestarzałe prototypy

## 🌿 Workflow Gałęzi

### Rozpoczęcie Pracy
```bash
# Sprawdź status
./tools/prototype_branch_manager.sh -s

# Utwórz nową gałąź
./tools/prototype_branch_manager.sh -c "feature-remote-config"

# Automatycznie przełączysz się na nową gałąź
```

### Rozwój i Commit
```bash
# Rozwijaj prototyp
# Commit zmiany
git add .
git commit -m "feat: implementacja RemoteConfigManager"

# Wypchnij na remote
./tools/prototype_branch_manager.sh -p
```

### Integracja z Frameworkiem
```bash
# Gdy prototyp działa - merguj do main
./tools/prototype_branch_manager.sh -m

# Automatycznie:
# - Przełącz na main
# - Merguj funkcjonalności
# - Wypchnij zmiany
# - Usuń gałąź prototypów
```

## 💡 Wzorce Implementacji

### Import Frameworka
```python
import sys
from pathlib import Path

# Dodaj ścieżkę do frameworka (tryb develop)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mancer.application.command_manager import CommandManager
from mancer.infrastructure.backend.bash_backend import BashBackend
```

### Struktura Plików
```
prototype-name/
├── README.md           # Opis i instrukcje
├── main.py            # Główna logika aplikacji
├── requirements.txt   # Zależności Python
├── pyproject.toml    # Konfiguracja projektu
├── config/           # Konfiguracja aplikacji
├── tests/            # Testy specyficzne dla prototypu
└── docs/             # Dokumentacja prototypu
```

## 🎯 Korzyści Strategii

### Dla Frameworka
- **Testowanie w rzeczywistych scenariuszach** - prototypy używają frameworka jak prawdziwe aplikacje
- **Identyfikacja luk funkcjonalnych** - brakujące API stają się oczywiste
- **Walidacja architektury** - problemy z designem ujawniają się podczas implementacji
- **Dokumentacja przez przykład** - prototypy pokazują jak używać frameworka

### Dla Deweloperów
- **Szybkie prototypowanie** - gotowy szablon i narzędzia
- **Izolacja środowiska** - każdy prototyp ma własne zależności
- **Łatwe testowanie** - integracja z frameworkiem jest automatyczna
- **Możliwość eksperymentowania** - testowanie nowych pomysłów bez wpływu na framework
- **Bezpieczne eksperymentowanie** - na osobnych gałęziach Git

### Dla Projektu
- **Czysta architektura** - framework i aplikacje są rozdzielone
- **Łatwe zarządzanie** - menedżer prototypów automatyzuje procesy
- **Skalowalność** - nowe prototypy nie komplikują głównego kodu
- **Współpraca** - różni deweloperzy mogą pracować nad różnymi prototypami
- **Kontrolowana integracja** - tylko udane funkcjonalności trafiają do main

## 🚀 Przykłady Użycia

### Testowanie Nowej Funkcjonalności
```bash
# Stwórz prototyp testujący nowe API
./tools/quick_prototype.sh -c "test-new-api" "Test nowego API"

# Zaimplementuj test w prototypie
# Uruchom i zweryfikuj działanie
./tools/quick_prototype.sh -r "test-new-api"

# Jeśli działa - przenieś do frameworka
# Jeśli nie - popraw framework i powtórz test
```

### Demonstracja Funkcjonalności
```bash
# Stwórz prototyp pokazujący użycie frameworka
./tools/quick_prototype.sh -c "demo-app" "Demonstracja frameworka"

# Zaimplementuj przykładową aplikację
# Uruchom i pokaż działanie
./tools/quick_prototype.sh -r "demo-app"
```

### Eksperymentowanie z Architekturą
```bash
# Stwórz prototyp testujący nową architekturę
./tools/quick_prototype.sh -c "arch-test" "Test nowej architektury"

# Zaimplementuj alternatywne podejście
# Porównaj z obecną implementacją
# Zdecyduj czy przenieść do frameworka
```

## 🌿 Przykłady Gałęzi

### Nowa Funkcjonalność
```bash
# 1. Utwórz gałąź
./tools/prototype_branch_manager.sh -c "feature-web-api"

# 2. Rozwijaj prototyp
# - Implementuj Web API
# - Testuj z frameworkiem
# - Commit zmiany

# 3. Wypchnij na remote
./tools/prototype_branch_manager.sh -p

# 4. Gdy gotowe - merguj do main
./tools/prototype_branch_manager.sh -m
```

### Eksperyment Architektoniczny
```bash
# 1. Utwórz gałąź eksperymentalną
./tools/prototype_branch_manager.sh -c "experiment-new-architecture"

# 2. Testuj nowe podejście
# - Implementuj alternatywną architekturę
# - Porównaj z obecną
# - Oceń wyniki

# 3. Jeśli udane - merguj do main
./tools/prototype_branch_manager.sh -m

# 4. Jeśli nie - usuń gałąź
./tools/prototype_branch_manager.sh -d "experiment-new-architecture"
```

## 📚 Dokumentacja

- **Strategia**: `docs/development/prototype-strategy.md`
- **Strategia Gałęzi**: `docs/development/prototype-branching-strategy.md`
- **Przykłady**: `examples/`
- **Szablon**: `prototypes/template/`
- **Narzędzia**: `tools/`

## 🔍 Status i Monitoring

### Sprawdź status całego systemu
```bash
./tools/quick_prototype.sh -s
```

### Status gałęzi prototypów
```bash
./tools/prototype_branch_manager.sh -s
```

### Generuj raport użycia frameworka
```bash
python tools/prototype_manager.py report
```

### Testuj strategię
```bash
./tools/quick_prototype.sh -t
```

## 🎉 Podsumowanie

Strategia prototypów pozwala na:
- **Rozwój frameworka przez praktykę** - realne aplikacje testują funkcjonalności
- **Czystą separację kodu** - framework i aplikacje pozostają niezależne
- **Szybkie iteracje** - prototypy można szybko tworzyć i testować
- **Walidację architektury** - problemy ujawniają się w rzeczywistych scenariuszach
- **Bezpieczne eksperymentowanie** - na osobnych gałęziach Git
- **Kontrolowaną integrację** - tylko udane funkcjonalności trafiają do main

Dzięki tej strategii framework Mancer może ewoluować w oparciu o rzeczywiste potrzeby aplikacji, a nie tylko teoretyczne założenia.

---

**🚀 Rozpocznij pracę z prototypami już teraz!**

```bash
# Sprawdź status
./tools/quick_prototype.sh -s

# Sprawdź status gałęzi
./tools/prototype_branch_manager.sh -s

# Zobacz dostępne prototypy
./tools/quick_prototype.sh -l

# Utwórz pierwszy prototyp
./tools/quick_prototype.sh -c "my-first-app" "Moja pierwsza aplikacja z frameworkiem Mancer"

# Utwórz gałąź dla nowej funkcjonalności
./tools/prototype_branch_manager.sh -c "feature-my-feature"
```
