# Custom Commands

You can extend Mancer by creating your own custom commands.

## Example: Creating a Custom Command
```python
from mancer.infrastructure.command.custom.custom_command_base import CustomCommandBase

class MyCustomCommand(CustomCommandBase):
    def run(self):
        # Your custom logic here
        print("Hello from custom command!")

# Register and use your command
MyCustomCommand().run()
```

See the `src/mancer/infrastructure/command/custom/` directory for more examples.
