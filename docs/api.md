# API Reference

This section provides an overview of the main classes and methods in Mancer. For full details, see the source code and docstrings.

## Main Classes

### CommandManager
- `run(cmd, backend='bash', **kwargs)`: Execute a command
- `chain(cmd_list)`: Execute a chain of commands

### CommandCache
- `get(cmd)`: Retrieve result from cache
- `set(cmd, result)`: Store result in cache

## Example Usage
```python
from mancer.application.command_manager import CommandManager
result = CommandManager.run('ls -l')
print(result.output)
```

---

For auto-generated API documentation, use tools like `pdoc` or `sphinx`.
