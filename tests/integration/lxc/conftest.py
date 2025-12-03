"""
Pytest configuration for LXC-based integration tests.

This module configures pytest for integration tests that run
against real LXC containers with actual system commands.
"""

import logging
import os

import pytest

# Configure logging for integration tests
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Integration test markers
def pytest_configure(config):
    """Configure pytest with integration test markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line("markers", "lxc: marks tests that require LXC containers")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


@pytest.fixture(scope="session", autouse=True)
def integration_test_setup():
    """Global setup for integration tests."""
    # Check if running in CI environment
    is_ci = os.getenv("CI", "false").lower() == "true"

    if is_ci:
        # In CI, we might want different behavior
        logging.getLogger().setLevel(logging.WARNING)

    # Ensure we're not running as root for safety
    if os.geteuid() == 0:
        pytest.skip("Integration tests should not run as root")

    yield

    # Global cleanup if needed
    pass


@pytest.fixture(autouse=True)
def test_isolation():
    """Ensure test isolation by checking we're not in a dirty state."""
    # This could check for leftover files, running processes, etc.
    yield


# Command-line options for integration tests
def pytest_addoption(parser):
    """Add command-line options for integration tests."""
    parser.addoption(
        "--lxc-container-name",
        action="store",
        default="mancer-integration-test",
        help="Name of the LXC container to use for tests",
    )

    parser.addoption(
        "--lxc-template", action="store", default="debian", help="LXC template to use for container creation"
    )

    parser.addoption("--lxc-release", action="store", default="bullseye", help="Debian release to use for container")

    parser.addoption(
        "--integration-timeout", action="store", type=int, default=300, help="Timeout for integration tests in seconds"
    )


@pytest.fixture(scope="session")
def lxc_config(request):
    """Provide LXC configuration from command line options."""
    return {
        "container_name": request.config.getoption("--lxc-container-name"),
        "template": request.config.getoption("--lxc-template"),
        "release": request.config.getoption("--lxc-release"),
        "timeout": request.config.getoption("--integration-timeout"),
    }
