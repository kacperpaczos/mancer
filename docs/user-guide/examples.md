# Examples

## Basic Command
```python
from mancer.application.command_manager import CommandManager
CommandManager.run('ls -l')
```

## Command Chain
```python
CommandManager.chain([
    'cd /tmp',
    'ls',
    'cat file.txt'
])
```

## Remote Execution
```python
CommandManager.run('ls', backend='ssh', host='your-host', user='your-user')
```

## Custom Command
```python
from mancer.application.commands.custom_commands import MyCustomCommand
MyCustomCommand().run()
```

See the `examples/` directory in the repository for more.
