# Przewodnik użytkownika

## Podstawowe funkcje

- Uruchamianie komend systemowych
- Tworzenie własnych łańcuchów poleceń
- Obsługa backendów (bash, ssh, powershell)
- Zarządzanie konfiguracją

## Struktura komend

Komendy w Mancer mają postać:
```python
from mancer.application.command_manager import CommandManager

CommandManager.run('ls -la')
```

Możesz łączyć komendy w łańcuchy:
```python
CommandManager.chain([
    'cd /tmp',
    'ls',
    'cat plik.txt'
])
```

## Przykłady użycia

- Wylistowanie plików:
  ```python
  CommandManager.run('ls -l')
  ```
- Wykonanie komendy na zdalnej maszynie:
  ```python
  CommandManager.run('ls', backend='ssh', host='adres', user='user')
  ```

## Rozszerzanie frameworka

Możesz tworzyć własne komendy i backendy. Zajrzyj do katalogu `src/mancer/application/commands/` oraz `src/mancer/infrastructure/backend/`.

Więcej przykładów znajdziesz w katalogu `examples/`.
