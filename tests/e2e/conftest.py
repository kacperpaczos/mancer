"""
Pytest configuration for End-to-End tests.

This module provides fixtures and configuration for E2E tests that
run complete workflows across multiple containers and systems.
"""

import pytest
import logging
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List


# Configure logging for E2E tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("e2e_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def e2e_setup():
    """Global setup for E2E test session."""
    # Skip E2E tests if not explicitly requested
    if not pytest.config.getoption("--run-e2e"):
        pytest.skip("E2E tests not requested. Use --run-e2e to run them.")

    # Check if running as root (dangerous for E2E tests)
    import os
    if os.geteuid() == 0:
        pytest.skip("E2E tests should not run as root")

    # Log E2E test start
    logger.info("Starting E2E test session")

    yield

    # Global cleanup
    logger.info("Completed E2E test session")


@pytest.fixture(scope="session")
def e2e_temp_dir():
    """Provide a temporary directory for E2E test artifacts."""
    with tempfile.TemporaryDirectory(prefix="mancer_e2e_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def performance_monitor():
    """Fixture for performance monitoring during E2E tests."""
    start_time = time.time()
    metrics = {
        "start_time": start_time,
        "operations": [],
        "resource_usage": {}
    }

    class PerformanceMonitor:
        def record_operation(self, name: str, duration: float, success: bool = True):
            """Record an operation's performance."""
            metrics["operations"].append({
                "name": name,
                "duration": duration,
                "success": success,
                "timestamp": time.time()
            })

        def get_total_duration(self) -> float:
            """Get total test duration."""
            return time.time() - start_time

        def get_metrics(self) -> Dict[str, Any]:
            """Get all collected metrics."""
            return metrics.copy()

    yield PerformanceMonitor()


# Add command-line options for E2E tests
def pytest_addoption(parser):
    """Add command-line options for E2E tests."""
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run E2E tests that require multi-container setups"
    )

    parser.addoption(
        "--e2e-containers",
        action="store",
        default="mancer-e2e-app,mancer-e2e-db",
        help="Comma-separated list of E2E container names"
    )

    parser.addoption(
        "--performance-monitoring",
        action="store_true",
        default=False,
        help="Enable detailed performance monitoring during E2E tests"
    )

    parser.addoption(
        "--baseline-compare",
        action="store_true",
        default=False,
        help="Compare performance against baseline metrics"
    )

    parser.addoption(
        "--chaos-mode",
        action="store_true",
        default=False,
        help="Enable fault injection during E2E tests"
    )


@pytest.fixture(scope="session")
def e2e_config(request):
    """Provide E2E test configuration."""
    containers = request.config.getoption("--e2e-containers").split(",")

    return {
        "containers": [c.strip() for c in containers],
        "performance_monitoring": request.config.getoption("--performance-monitoring"),
        "baseline_compare": request.config.getoption("--baseline-compare"),
        "chaos_mode": request.config.getoption("--chaos-mode")
    }


# E2E test markers
def pytest_configure(config):
    """Configure pytest with E2E test markers."""
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests (require --run-e2e)"
    )
    config.addinivalue_line(
        "markers",
        "data_pipeline: marks tests as data pipeline E2E scenarios"
    )
    config.addinivalue_line(
        "markers",
        "automation: marks tests as automation workflow E2E scenarios"
    )
    config.addinivalue_line(
        "markers",
        "error_handling: marks tests as error handling E2E scenarios"
    )
    config.addinivalue_line(
        "markers",
        "performance: marks tests that include performance monitoring"
    )
    config.addinivalue_line(
        "markers",
        "multi_container: marks tests requiring multiple containers"
    )