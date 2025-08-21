#!/usr/bin/env python3
"""
Mancer Flask Service

This module provides Flask integration for Mancer applications.
It allows easy creation of web APIs with minimal configuration.
"""

import logging
import sys
import threading
import time
from functools import wraps
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)

# Flask is imported conditionally to avoid hard dependency
_has_flask = False
try:
    from flask import Flask, jsonify, request

    _has_flask = True
except ImportError:
    logger.debug("Flask is not installed - MancerFlask service will be limited")


class MancerFlaskError(Exception):
    """Base exception for MancerFlask errors"""

    pass


class FlaskNotInstalledError(MancerFlaskError):
    """Exception raised when Flask is required but not installed"""

    def __init__(self, message="Flask is not installed. Install it using: pip install flask"):
        self.message = message
        super().__init__(self.message)


class MancerFlask:
    """
    Class for integrating Flask with Mancer applications

    This class provides a simple wrapper around Flask to make it easy to
    integrate HTTP capabilities into Mancer applications.
    """

    def __init__(
        self,
        app_name: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False,
    ):
        """
        Initialize Flask server for Mancer

        Args:
            app_name: Flask application name
            host: Host to listen on
            port: Port to listen on
            debug: Debug mode

        Raises:
            FlaskNotInstalledError: If Flask is not installed
        """
        if not _has_flask:
            raise FlaskNotInstalledError()

        self.app = Flask(app_name or __name__)
        self.host = host
        self.port = port
        self.debug = debug
        self.thread = None
        self.running = False

        # Add Mancer headers to all responses
        @self.app.after_request
        def add_mancer_headers(response):
            response.headers["X-Powered-By"] = "Mancer"
            return response

        # Default endpoint, shows API information
        @self.app.route("/", methods=["GET"])
        def home():
            rules = []
            for rule in self.app.url_map.iter_rules():
                if rule.endpoint != "static":
                    methods = [m for m in rule.methods if m != "HEAD" and m != "OPTIONS"]
                    rules.append(
                        {
                            "endpoint": rule.endpoint,
                            "methods": methods,
                            "path": str(rule),
                        }
                    )

            return jsonify({"status": "success", "message": "Mancer Flask API", "endpoints": rules})

    def add_route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        auth_required: bool = False,
    ):
        """
        Decorator for adding API routes

        Args:
            path: URL path
            methods: List of allowed HTTP methods
            auth_required: Whether authorization is required

        Returns:
            Decorator function
        """
        if methods is None:
            methods = ["GET"]

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Authorization validation
                if auth_required:
                    # You can add authorization logic for Mancer here
                    # For example, checking the Authorization header
                    auth_header = request.headers.get("Authorization")
                    if not auth_header:
                        return jsonify({"status": "error", "error": "Authorization required"}), 401

                # Call the actual function
                try:
                    result = f(*args, **kwargs)
                    if isinstance(result, tuple) and len(result) == 2:
                        return result
                    return jsonify(result)
                except Exception as e:
                    logger.exception(f"Error in route {path}: {str(e)}")
                    return jsonify({"status": "error", "error": str(e)}), 500

            # Register the route in the Flask application
            self.app.route(path, methods=methods)(wrapper)
            return wrapper

        return decorator

    def start(self, background: bool = True) -> None:
        """
        Starts the Flask server

        Args:
            background: Whether to run in the background as a thread
        """
        if background:
            if self.running:
                logger.info(f"Server is already running on http://{self.host}:{self.port}")
                return

            self.running = True
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()

            # Wait a moment to ensure the server has started
            time.sleep(1)
            logger.info(f"Flask server started in the background on http://{self.host}:{self.port}")
        else:
            self._run_server()

    def stop(self) -> None:
        """
        Stops the Flask server running in the background
        """
        if not self.running:
            logger.warning("Server is not running")
            return

        # Signal that the server should stop
        self.running = False
        logger.info("Stopping Flask server...")

        # Unfortunately, Flask doesn't have an elegant way to stop from another thread
        # You could use the shutdown function from werkzeug, but it requires a special endpoint
        # Here we simply assume the thread will run until the program terminates

    def _run_server(self) -> None:
        """Internal method to run the server"""
        try:
            self.app.run(host=self.host, port=self.port, debug=self.debug, use_reloader=False)
        except Exception as e:
            logger.error(f"Error running Flask server: {str(e)}")
        finally:
            self.running = False


def is_flask_available() -> bool:
    """
    Check if Flask is available

    Returns:
        True if Flask is installed, False otherwise
    """
    return _has_flask


def install_flask(prompt: bool = True) -> bool:
    """
    Attempt to install Flask

    Args:
        prompt: Whether to prompt the user before installation

    Returns:
        True if Flask was installed successfully, False otherwise
    """
    global Flask, request, jsonify, _has_flask

    if _has_flask:
        return True

    try:
        if prompt:
            user_input = input("Flask is not installed. Install it now? (y/n): ").lower()
            if user_input != "y":
                return False

        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])

        # Try to import Flask again
        from flask import Flask, jsonify, request

        _has_flask = True

        return True
    except Exception as e:
        logger.error(f"Error installing Flask: {str(e)}")
        return False


# Example usage
def example():
    """
    Example of using MancerFlask
    """
    if not is_flask_available():
        if not install_flask():
            print("Flask is required for this example")
            return

    # Create a MancerFlask instance
    mf = MancerFlask("example_application", port=5050)

    # Add example routes
    @mf.add_route("/api/hello", methods=["GET"])
    def hello():
        return {
            "status": "success",
            "message": "Hello from Mancer Flask!",
            "query_params": dict(request.args),
        }

    @mf.add_route("/api/echo", methods=["POST"])
    def echo():
        data = request.json or {}
        return {"status": "success", "message": "Echo", "data": data}

    @mf.add_route("/api/secure", methods=["GET"], auth_required=True)
    def secure():
        return {"status": "success", "message": "This route requires authorization"}

    # Start the server in the background
    mf.start(background=True)

    # Simulate other application activities
    try:
        print("Application is running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing application...")
        mf.stop()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    # Run the example
    example()
