# Strategia Prototypów Frameworka Mancer

## Przegląd

Strategia "Prototypy jako Laboratorium Frameworka" pozwala na rozwój frameworka Mancer przez budowanie rzeczywistych aplikacji, jednocześnie utrzymując czystą separację między kodem frameworka a prototypami.

## Zasady Organizacyjne

### 1. Separacja Kodu
- **Prototypy NIE są częścią frameworka** - mają własne zależności i konfigurację
- **Framework jest zależnością zewnętrzną** - prototypy importują go jako bibliotekę
- **Każdy prototyp ma własny katalog** z kompletną strukturą projektu

### 2. Rozwój Frameworka
- **Prototypy testują nowe funkcjonalności** frameworka
- **Identyfikują brakujące API** i luki w funkcjonalności
- **Demonstrują praktyczne zastosowania** różnych modułów
- **Generują feedback** o użyteczności i wydajności

### 3. Struktura Katalogów
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
```

## Cykl Życia Prototypu

### 1. Tworzenie
```bash
# Użyj menedżera prototypów
python tools/prototype_manager.py create --name "my-app" --description "Moja aplikacja"

# Lub skopiuj ręcznie z szablonu
cp -r prototypes/template prototypes/my-app
```

### 2. Rozwój
- Edytuj kod w katalogu prototypu
- Używaj frameworka jako zależności
- Testuj nowe funkcjonalności
- Dokumentuj problemy i sugestie

### 3. Testowanie
```bash
# Uruchom prototyp
python tools/prototype_manager.py run --name "my-app"

# Sprawdź integrację z frameworkiem
python tools/prototype_manager.py report
```

### 4. Ewolucja
- Przenieś udane funkcjonalności do frameworka
- Zaktualizuj prototyp do nowej wersji frameworka
- Usu przestarzałe prototypy

## Wzorce Implementacji

### 1. Import Frameworka
```python
# W prototypie
import sys
from pathlib import Path

# Dodaj ścieżkę do frameworka (tryb develop)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mancer.application.command_manager import CommandManager
from mancer.infrastructure.backend.bash_backend import BashBackend
```

### 2. Konfiguracja Zależności
```toml
# pyproject.toml prototypu
[project]
name = "prototype-my-app"
dependencies = [
    # Framework Mancer (tryb develop)
    "mancer @ file://../../src",
    # Inne zależności
    "paramiko>=3.0.0",
    "rich>=13.0.0"
]
```

### 3. Struktura Plików
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

## Korzyści Strategii

### 1. Dla Frameworka
- **Testowanie w rzeczywistych scenariuszach** - prototypy używają frameworka jak prawdziwe aplikacje
- **Identyfikacja luk funkcjonalnych** - brakujące API stają się oczywiste
- **Walidacja architektury** - problemy z designem ujawniają się podczas implementacji
- **Dokumentacja przez przykład** - prototypy pokazują jak używać frameworka

### 2. Dla Deweloperów
- **Szybkie prototypowanie** - gotowy szablon i narzędzia
- **Izolacja środowiska** - każdy prototyp ma własne zależności
- **Łatwe testowanie** - integracja z frameworkiem jest automatyczna
- **Możliwość eksperymentowania** - testowanie nowych pomysłów bez wpływu na framework

### 3. Dla Projektu
- **Czysta architektura** - framework i aplikacje są rozdzielone
- **Łatwe zarządzanie** - menedżer prototypów automatyzuje procesy
- **Skalowalność** - nowe prototypy nie komplikują głównego kodu
- **Współpraca** - różni deweloperzy mogą pracować nad różnymi prototypami

## Narzędzia Wspierające

### 1. Menedżer Prototypów
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

### 2. Szablon Prototypu
- Gotowa struktura katalogów
- Przykłady użycia frameworka
- Konfiguracja narzędzi developerskich
- Dokumentacja integracji

### 3. Automatyzacja
- Skrypty uruchamiania
- Integracja z CI/CD
- Automatyczne testy integracyjne
- Generowanie raportów

## Najlepsze Praktyki

### 1. Tworzenie Prototypów
- **Używaj szablonu** - zapewnia spójność i kompletność
- **Dokumentuj cel** - jasny opis co prototyp ma osiągnąć
- **Minimalizuj zależności** - używaj tylko niezbędnych pakietów
- **Testuj integrację** - upewnij się że framework działa poprawnie

### 2. Rozwój Frameworka
- **Implementuj brakujące funkcjonalności** - gdy prototyp ich potrzebuje
- **Refaktoruj API** - na podstawie feedbacku z prototypów
- **Dodawaj testy** - dla nowych funkcjonalności
- **Aktualizuj dokumentację** - po zmianach w API

### 3. Utrzymanie
- **Regularnie testuj prototypy** - po zmianach w frameworku
- **Aktualizuj zależności** - utrzymuj kompatybilność
- **Usuwaj przestarzałe prototypy** - utrzymuj czystość
- **Dokumentuj zmiany** - śledź ewolucję frameworka

## Przykłady Użycia

### 1. Testowanie Nowej Funkcjonalności
```bash
# Stwórz prototyp testujący nowe API
python tools/prototype_manager.py create --name "test-new-api" --description "Test nowego API"

# Zaimplementuj test w prototypie
# Uruchom i zweryfikuj działanie
python tools/prototype_manager.py run --name "test-new-api"

# Jeśli działa - przenieś do frameworka
# Jeśli nie - popraw framework i powtórz test
```

### 2. Demonstracja Funkcjonalności
```bash
# Stwórz prototyp pokazujący użycie frameworka
python tools/prototype_manager.py create --name "demo-app" --description "Demonstracja frameworka"

# Zaimplementuj przykładową aplikację
# Uruchom i pokaż działanie
python tools/prototype_manager.py run --name "demo-app"
```

### 3. Eksperymentowanie z Architekturą
```bash
# Stwórz prototyp testujący nową architekturę
python tools/prototype_manager.py create --name "arch-test" --description "Test nowej architektury"

# Zaimplementuj alternatywne podejście
# Porównaj z obecną implementacją
# Zdecyduj czy przenieść do frameworka
```

## Podsumowanie

Strategia prototypów pozwala na:
- **Rozwój frameworka przez praktykę** - realne aplikacje testują funkcjonalności
- **Czystą separację kodu** - framework i aplikacje pozostają niezależne
- **Szybkie iteracje** - prototypy można szybko tworzyć i testować
- **Walidację architektury** - problemy ujawniają się w rzeczywistych scenariuszach

Dzięki tej strategii framework Mancer może ewoluować w oparciu o rzeczywiste potrzeby aplikacji, a nie tylko teoretyczne założenia.
