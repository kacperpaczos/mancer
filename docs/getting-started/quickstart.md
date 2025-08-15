# Quickstart

After installation, you can run your first command with Mancer:

```python
from mancer.application.command_manager import CommandManager

result = CommandManager.run('ls -l')
print(result.output)
```

You can also chain commands:

```python
CommandManager.chain([
    'cd /tmp',
    'ls',
    'cat file.txt'
])
```

For more advanced usage, see the [User Guide](../user-guide/commands.md).
