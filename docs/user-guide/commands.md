# Commands

## Running a Single Command
```python
from mancer.application.command_manager import CommandManager
result = CommandManager.run('ls -l')
print(result.output)
```

## Chaining Commands
```python
CommandManager.chain([
    'cd /tmp',
    'ls',
    'cat file.txt'
])
```

## Remote Command Execution
```python
CommandManager.run('ls', backend='ssh', host='your-host', user='your-user')
```

See [Examples](examples.md) for more advanced scenarios.
