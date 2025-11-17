"""
Pytest fixtures for LXC container management in integration tests.

This module provides fixtures for creating, managing, and cleaning up
LXC containers during integration test execution.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

logger = logging.getLogger(__name__)


class LXCContainerManager:
    """Manages LXC container lifecycle for integration tests."""

    def __init__(self, container_name: str = "mancer-integration-test"):
        self.container_name = container_name
        self.workspace_dir = "/tmp/integration_workspace"
        self.test_user = "mancer"
        self.is_running = False

    def container_exists(self) -> bool:
        """Check if container exists."""
        try:
            result = subprocess.run(["lxc-ls", "-1"], capture_output=True, text=True, check=True)
            return self.container_name in result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return False

    def container_running(self) -> bool:
        """Check if container is running."""
        try:
            result = subprocess.run(
                ["lxc-info", "-n", self.container_name, "-s"], capture_output=True, text=True, check=True
            )
            return "RUNNING" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def start_container(self) -> None:
        """Start the LXC container."""
        if not self.container_exists():
            raise RuntimeError(f"Container {self.container_name} does not exist")

        if self.container_running():
            logger.info(f"Container {self.container_name} is already running")
            return

        logger.info(f"Starting container {self.container_name}")
        subprocess.run(["sudo", "lxc-start", "-n", self.container_name], check=True)

        # Wait for container to fully start
        for i in range(30):
            if self.container_running():
                logger.info(f"Container {self.container_name} started successfully")
                self.is_running = True
                time.sleep(2)  # Additional wait for services
                return
            time.sleep(1)

        raise RuntimeError(f"Container {self.container_name} failed to start")

    def stop_container(self) -> None:
        """Stop the LXC container."""
        if not self.container_running():
            logger.info(f"Container {self.container_name} is already stopped")
            return

        logger.info(f"Stopping container {self.container_name}")
        subprocess.run(["sudo", "lxc-stop", "-n", self.container_name], check=True)
        self.is_running = False

    def destroy_container(self) -> None:
        """Destroy the LXC container."""
        if self.container_running():
            self.stop_container()

        if not self.container_exists():
            logger.info(f"Container {self.container_name} does not exist")
            return

        logger.info(f"Destroying container {self.container_name}")
        subprocess.run(["sudo", "lxc-destroy", "-n", self.container_name], check=True)

    def execute_command(self, command: str, user: Optional[str] = None) -> Dict[str, Any]:
        """Execute command inside container."""
        if not self.container_running():
            raise RuntimeError(f"Container {self.container_name} is not running")

        lxc_cmd = ["sudo", "lxc-attach", "-n", self.container_name]

        if user:
            lxc_cmd.extend(["--", "su", "-", user, "-c", command])
        else:
            lxc_cmd.extend(["--"] + command.split())

        logger.debug(f"Executing in container: {' '.join(lxc_cmd)}")

        try:
            result = subprocess.run(lxc_cmd, capture_output=True, text=True, timeout=30)

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out", "success": False}

    def copy_to_container(self, local_path: str, container_path: str) -> None:
        """Copy file from host to container."""
        if not self.container_running():
            raise RuntimeError(f"Container {self.container_name} is not running")

        logger.info(f"Copying {local_path} to container:{container_path}")
        subprocess.run(
            ["sudo", "cp", local_path, f"/var/lib/lxc/{self.container_name}/rootfs{container_path}"], check=True
        )

    def copy_from_container(self, container_path: str, local_path: str) -> None:
        """Copy file from container to host."""
        if not self.container_running():
            raise RuntimeError(f"Container {self.container_name} is not running")

        logger.info(f"Copying container:{container_path} to {local_path}")
        subprocess.run(
            ["sudo", "cp", f"/var/lib/lxc/{self.container_name}/rootfs{container_path}", local_path], check=True
        )

    def create_test_workspace(self) -> str:
        """Create and return test workspace path inside container."""
        if not self.container_running():
            raise RuntimeError(f"Container {self.container_name} is not running")

        # Create workspace directory
        result = self.execute_command(f"mkdir -p {self.workspace_dir}")
        if not result["success"]:
            raise RuntimeError(f"Failed to create workspace: {result['stderr']}")

        # Set ownership to test user
        result = self.execute_command(f"chown {self.test_user}:{self.test_user} {self.workspace_dir}")
        if not result["success"]:
            raise RuntimeError(f"Failed to set workspace ownership: {result['stderr']}")

        return self.workspace_dir

    def cleanup_workspace(self, workspace_path: str) -> None:
        """Clean up test workspace."""
        if self.container_running():
            self.execute_command(f"rm -rf {workspace_path}")

    def get_container_ip(self) -> Optional[str]:
        """Get container IP address."""
        if not self.container_running():
            return None

        result = self.execute_command("hostname -I")
        if result["success"]:
            ips = result["stdout"].strip().split()
            return ips[0] if ips else None

        return None


@pytest.fixture(scope="session")
def lxc_container():
    """Session-scoped fixture providing LXC container management."""
    manager = LXCContainerManager()

    # Setup: start container if not already running
    try:
        manager.start_container()
        yield manager
    finally:
        # Cleanup: stop container (don't destroy in case of debugging)
        try:
            manager.stop_container()
        except Exception as e:
            logger.warning(f"Failed to stop container during cleanup: {e}")


@pytest.fixture
def container_workspace(lxc_container):
    """Per-test fixture providing isolated workspace inside container."""
    workspace = lxc_container.create_test_workspace()

    # Copy test fixtures to workspace
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    if fixtures_dir.exists():
        for fixture_file in fixtures_dir.glob("*.json"):
            container_dest = f"{workspace}/{fixture_file.name}"
            lxc_container.copy_to_container(str(fixture_file), container_dest)

        # Copy test scripts
        scripts_dir = fixtures_dir / "test_scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.glob("*.py"):
                container_dest = f"{workspace}/{script_file.name}"
                lxc_container.copy_to_container(str(script_file), container_dest)
                # Make executable
                lxc_container.execute_command(f"chmod +x {container_dest}")

    yield workspace

    # Cleanup workspace after test
    lxc_container.cleanup_workspace(workspace)


@pytest.fixture
def container_ip(lxc_container):
    """Fixture providing container IP address."""
    return lxc_container.get_container_ip()
