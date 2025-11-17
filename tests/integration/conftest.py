"""
Pytest configuration for integration tests.

This module provides shared fixtures and configuration for all
integration tests that run against LXC containers.
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def integration_setup():
    """Global setup for integration test session."""
    # Skip integration tests if not explicitly requested
    if not pytest.config.getoption("--run-integration"):
        pytest.skip("Integration tests not requested. Use --run-integration to run them.")

    # Check if running as root (dangerous for integration tests)
    if os.geteuid() == 0:
        pytest.skip("Integration tests should not run as root")

    yield


@pytest.fixture(scope="session")
def integration_temp_dir():
    """Provide a temporary directory for integration test artifacts."""
    with tempfile.TemporaryDirectory(prefix="mancer_integration_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def integration_test_cleanup():
    """Clean up after each integration test."""
    yield
    # Cleanup logic can be added here if needed


# Add command-line options
def pytest_addoption(parser):
    """Add command-line options for integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require LXC containers",
    )

    parser.addoption(
        "--integration-container",
        action="store",
        default="mancer-integration-test",
        help="Name of the LXC container to use for integration tests",
    )

    parser.addoption(
        "--keep-containers",
        action="store_true",
        default=False,
        help="Keep LXC containers running after tests (for debugging)",
    )


@pytest.fixture(scope="session")
def integration_config(request):
    """Provide integration test configuration."""
    return {
        "container_name": request.config.getoption("--integration-container"),
        "keep_containers": request.config.getoption("--keep-containers"),
        "run_integration": request.config.getoption("--run-integration"),
    }
