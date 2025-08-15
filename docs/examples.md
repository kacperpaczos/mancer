# Przykłady użycia

## Podstawowe komendy
```python
from mancer.application.command_manager import CommandManager
CommandManager.run('ls -l')
```

## Łańcuchy komend
```python
CommandManager.chain([
    'cd /tmp',
    'ls',
    'cat plik.txt'
])
```

## Zdalne wykonywanie
```python
CommandManager.run('ls', backend='ssh', host='adres', user='user')
```

## Własne komendy
```python
from mancer.application.commands.custom_commands import MyCustomCommand
MyCustomCommand().run()
```

Więcej przykładów znajdziesz w katalogu `examples/` w repozytorium.
