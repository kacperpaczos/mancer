# Adding Backends

Mancer supports multiple backends (bash, ssh, powershell). You can add your own backend by implementing the required interface.

## Example: Creating a Backend
1. Create a new file in `src/mancer/infrastructure/backend/`.
2. Implement the backend class, inheriting from the appropriate base class.
3. Register your backend in the backend factory.

See existing backends in `src/mancer/infrastructure/backend/` for reference.
