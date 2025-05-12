# Mancer Web Infrastructure

This module provides web service capabilities for Mancer applications.

## Overview

The Mancer Web Infrastructure offers components for integrating HTTP services with Mancer applications. Currently, it includes:

- **MancerFlask**: A lightweight wrapper around Flask providing easy HTTP API capabilities

## MancerFlask

MancerFlask is a simple integration layer for Flask that makes it easy to add HTTP API capabilities to any Mancer application.

### Key Features

- Easy Flask server startup in the background or foreground
- Convenient API for defining endpoints with automatic error handling
- Automatic JSON response formatting
- Authorization handling capability
- Optional dependency - Flask is only required when actually using HTTP features

### Basic Usage

```python
from mancer.infrastructure.web.flask_service import MancerFlask, is_flask_available, install_flask

# Check if Flask is available and install if needed
if not is_flask_available():
    install_flask()

# Create a MancerFlask instance
app = MancerFlask("my_application", port=5000)

# Add an endpoint
@app.add_route('/hello', methods=['GET'])
def hello():
    return {
        "message": "Hello, World!"
    }

# Start the server in the background
app.start(background=True)

# Continue with other application tasks...
# When done:
app.stop()
```

### Handling GET Requests

```python
@app.add_route('/api/users', methods=['GET'])
def get_users():
    from flask import request
    
    # Get query parameters
    limit = request.args.get('limit', '10')
    offset = request.args.get('offset', '0')
    
    # Process and return data
    return {
        "limit": int(limit),
        "offset": int(offset),
        "users": ["user1", "user2"]
    }
```

### Handling POST Requests

```python
@app.add_route('/api/users', methods=['POST'])
def create_user():
    from flask import request
    
    # Get JSON data from the request
    data = request.json
    
    if not data or 'name' not in data:
        return {
            "status": "error",
            "message": "Missing required field 'name'"
        }, 400  # HTTP 400 Bad Request
    
    # Process and return data
    return {
        "status": "success",
        "message": f"Created user {data['name']}"
    }
```

### Adding Authorization

```python
@app.add_route('/api/secure', methods=['GET'], auth_required=True)
def secure_endpoint():
    # This function requires authorization (Authorization header)
    return {
        "status": "success",
        "message": "Authorized access"
    }
```

### Fallback for Local Development

If you're developing without the full Mancer infrastructure, you can use the local MancerFlask module:

```python
try:
    # Try to import from Mancer infrastructure
    from mancer.infrastructure.web.flask_service import MancerFlask
except ImportError:
    # Fallback to local version
    from mancer_flask import MancerFlask
```

## Customizing and Extending

### Custom Authorization

The default implementation checks for the presence of an Authorization header, but you can customize this by extending the `MancerFlask` class:

```python
from mancer.infrastructure.web.flask_service import MancerFlask

class CustomMancerFlask(MancerFlask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_keys = kwargs.get('api_keys', [])
    
    def add_route(self, path, methods=None, auth_required=False):
        if methods is None:
            methods = ['GET']
            
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Custom authorization logic
                if auth_required:
                    from flask import request
                    api_key = request.headers.get('X-API-Key')
                    if not api_key or api_key not in self.api_keys:
                        return jsonify({
                            'status': 'error',
                            'error': 'Invalid API key'
                        }), 401
                
                # Call the actual function
                try:
                    result = f(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) == 2:
                        return result
                    return jsonify(result)
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'error': str(e)
                    }), 500
            
            # Register the route in the Flask application
            self.app.route(path, methods=methods)(wrapper)
            return wrapper
        
        return decorator
```

## Utility Functions

The module provides several utility functions:

- `is_flask_available()`: Check if Flask is installed
- `install_flask(prompt=True)`: Install Flask, optionally prompting for confirmation
- `example()`: Run a basic example of MancerFlask

## Running Stand-alone

You can run the module directly to see a demo:

```bash
python -m mancer.infrastructure.web.flask_service
``` 