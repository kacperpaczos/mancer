# 🌿 Strategia Gałęzi Prototypów Frameworka Mancer

## Przegląd

Strategia gałęzi prototypów pozwala na izolowane rozwijanie prototypów na osobnych gałęziach Git, co zapewnia:
- **Czystą separację** między kodem frameworka a prototypami
- **Bezpieczne eksperymentowanie** bez wpływu na główną gałąź
- **Łatwe zarządzanie** różnymi wersjami prototypów
- **Kontrolowaną integrację** udanych funkcjonalności do main

## 🎯 Główne Zasady

### 1. Struktura Gałęzi
```
main                    # Główna gałąź - stabilny kod frameworka
├── prototypes         # Gałąź prototypów - główna gałąź rozwojowa
├── feature-name      # Gałęzie funkcjonalności - konkretne prototypy
├── experiment-name   # Gałęzie eksperymentalne - testowanie pomysłów
└── cleanup-name      # Gałęzie porządkowe - refaktoring i optymalizacja
```

### 2. Cykl Życia Gałęzi
1. **Tworzenie** - nowa gałąź z main
2. **Rozwój** - implementacja prototypów
3. **Testowanie** - weryfikacja funkcjonalności
4. **Integracja** - merge udanych funkcjonalności do main
5. **Czyszczenie** - usunięcie zużytych gałęzi

### 3. Zasady Naming
- **prototypes** - główna gałąź prototypów
- **feature-*** - nowe funkcjonalności
- **experiment-*** - eksperymentalne podejścia
- **cleanup-*** - porządkowanie kodu
- **hotfix-*** - szybkie poprawki

## 🛠️ Narzędzia Zarządzania

### Menedżer Gałęzi Prototypów
```bash
# Status gałęzi
./tools/prototype_branch_manager.sh -s

# Lista wszystkich gałęzi
./tools/prototype_branch_manager.sh -l

# Utwórz nową gałąź
./tools/prototype_branch_manager.sh -c "feature-name"

# Wypchnij zmiany na remote
./tools/prototype_branch_manager.sh -p

# Zaktualizuj z remote
./tools/prototype_branch_manager.sh -u

# Merguj do main
./tools/prototype_branch_manager.sh -m

# Usuń gałąź
./tools/prototype_branch_manager.sh -d "feature-name"

# Backup gałęzi
./tools/prototype_branch_manager.sh -b
```

## 📋 Workflow Rozwoju

### 1. Rozpoczęcie Pracy nad Prototypem

```bash
# Sprawdź status
./tools/prototype_branch_manager.sh -s

# Przejdź na main i pobierz najnowsze zmiany
git checkout main
git pull origin main

# Utwórz nową gałąź dla prototypu
./tools/prototype_branch_manager.sh -c "feature-remote-config"

# Automatycznie przełączysz się na nową gałąź
```

### 2. Rozwój Prototypu

```bash
# Jesteś na gałęzi feature-remote-config
# Rozwijaj prototyp używając frameworka

# Sprawdź status
git status

# Dodaj zmiany
git add .

# Commit zmiany
git commit -m "feat: implementacja RemoteConfigManager"

# Wypchnij na remote
./tools/prototype_branch_manager.sh -p
```

### 3. Testowanie i Iteracja

```bash
# Testuj prototyp
./tools/quick_prototype.sh -r "configMaster"

# Jeśli są problemy - popraw i commit
git add .
git commit -m "fix: poprawka błędu połączenia SSH"

# Wypchnij poprawki
git push origin feature-remote-config
```

### 4. Integracja z Frameworkiem

```bash
# Gdy prototyp działa - merguj do main
./tools/prototype_branch_manager.sh -m

# Automatycznie:
# - Przełącz na main
# - Merguj funkcjonalności
# - Wypchnij zmiany
# - Usuń gałąź prototypów
```

## 🔄 Synchronizacja z Remote

### Wypychanie Zmian
```bash
# Sprawdź status
./tools/prototype_branch_manager.sh -s

# Wypchnij zmiany
./tools/prototype_branch_manager.sh -p

# Jeśli są niezacommitowane zmiany - zostaniesz poproszony o commit
```

### Aktualizacja z Remote
```bash
# Pobierz najnowsze zmiany
./tools/prototype_branch_manager.sh -u

# Jeśli masz lokalne zmiany - zostaniesz poproszony o stash
```

### Rozwiązywanie Konfliktów
```bash
# W przypadku konfliktów podczas merge
git status                    # Sprawdź pliki z konfliktami
# Edytuj pliki i rozwiąż konflikty
git add .                     # Dodaj rozwiązane pliki
git commit                    # Dokończ merge
```

## 🎯 Strategie Gałęzi

### 1. Gałąź Główna (prototypes)
- **Cel**: Główna gałąź rozwojowa prototypów
- **Źródło**: main
- **Przeznaczenie**: Integracja różnych prototypów
- **Życie**: Długoterminowa

### 2. Gałęzie Funkcjonalności (feature-*)
- **Cel**: Konkretne funkcjonalności
- **Źródło**: main lub prototypes
- **Przeznaczenie**: Rozwój pojedynczych funkcji
- **Życie**: Średnioterminowe

### 3. Gałęzie Eksperymentalne (experiment-*)
- **Cel**: Testowanie nowych pomysłów
- **Źródło**: main
- **Przeznaczenie**: Eksperymenty bez gwarancji sukcesu
- **Życie**: Krótkoterminowe

### 4. Gałęzie Porządkowe (cleanup-*)
- **Cel**: Refaktoring i optymalizacja
- **Źródło**: main
- **Przeznaczenie**: Poprawa jakości kodu
- **Życie**: Średnioterminowe

## 🚀 Przykłady Użycia

### Scenariusz 1: Nowa Funkcjonalność
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

### Scenariusz 2: Eksperyment Architektoniczny
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

### Scenariusz 3: Refaktoring
```bash
# 1. Utwórz gałąź porządkową
./tools/prototype_branch_manager.sh -c "cleanup-command-structure"

# 2. Refaktoruj kod
# - Popraw strukturę komend
# - Zoptymalizuj wydajność
# - Zaktualizuj dokumentację

# 3. Testuj zmiany
./tools/quick_prototype.sh -t

# 4. Merguj do main
./tools/prototype_branch_manager.sh -m
```

## 🔍 Monitoring i Backup

### Status Gałęzi
```bash
# Sprawdź status wszystkich gałęzi
./tools/prototype_branch_manager.sh -s

# Lista wszystkich gałęzi
./tools/prototype_branch_manager.sh -l

# Szczegółowy status
git branch -vv
git status
```

### Backup Gałęzi
```bash
# Utwórz backup wszystkich gałęzi prototypów
./tools/prototype_branch_manager.sh -b

# Backup zawiera:
# - Informacje o gałęziach
# - Historię commitów
# - Diff względem main
# - Instrukcje przywracania
```

### Historia Zmian
```bash
# Historia gałęzi
git log --oneline --graph --all

# Historia konkretnej gałęzi
git log --oneline feature-name

# Porównanie z main
git diff main..feature-name
```

## ⚠️ Najlepsze Praktyki

### 1. Tworzenie Gałęzi
- **Zawsze z main** - zapewnia czystą bazę
- **Opisowe nazwy** - jasno określ cel
- **Krótkie życie** - nie trzymaj gałęzi zbyt długo

### 2. Praca na Gałęziach
- **Regularne commity** - małe, logiczne zmiany
- **Opisowe wiadomości** - jasno określ co zmieniono
- **Testowanie** - weryfikuj przed commit

### 3. Integracja z Main
- **Tylko udane funkcjonalności** - nie merguj eksperymentów
- **Rozwiązywanie konfliktów** - nie ignoruj problemów
- **Testowanie po merge** - upewnij się że wszystko działa

### 4. Czyszczenie
- **Usuwanie zużytych gałęzi** - utrzymuj porządek
- **Backup ważnych zmian** - przed usunięciem
- **Dokumentacja** - zapisz wnioski i doświadczenia

## 🎉 Podsumowanie

Strategia gałęzi prototypów zapewnia:

- **Izolację rozwoju** - prototypy nie wpływają na główny kod
- **Bezpieczne eksperymentowanie** - możliwość testowania pomysłów
- **Kontrolowaną integrację** - tylko udane funkcjonalności trafiają do main
- **Łatwe zarządzanie** - automatyzacja procesów Git
- **Historię zmian** - śledzenie ewolucji prototypów

Dzięki tej strategii możesz swobodnie rozwijać prototypy, testować nowe pomysły i integrować udane funkcjonalności z frameworkiem, jednocześnie utrzymując stabilność głównej gałęzi.

---

**🚀 Rozpocznij pracę z gałęziami prototypów!**

```bash
# Sprawdź status
./tools/prototype_branch_manager.sh -s

# Utwórz pierwszą gałąź
./tools/prototype_branch_manager.sh -c "feature-my-prototype"

# Rozwijaj prototyp i merguj do main gdy gotowy!
```
