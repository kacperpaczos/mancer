# Configuration

Mancer can be configured using YAML or JSON files, as well as environment variables.

## Example YAML Configuration
```yaml
backend: ssh
host: your-host
user: your-user
log_level: INFO
```

## Example JSON Configuration
```json
{
  "backend": "ssh",
  "host": "your-host",
  "user": "your-user",
  "log_level": "INFO"
}
```

## Environment Variables
You can override configuration values using environment variables:
```bash
export MANCER_BACKEND=ssh
export MANCER_HOST=your-host
export MANCER_USER=your-user
```
