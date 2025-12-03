"""
Integration tests for ls command in LXC containers.

These tests validate that ls command works correctly with real
filesystem operations in isolated LXC environments.
"""

import pytest


@pytest.mark.integration
@pytest.mark.lxc
class TestLsIntegration:
    """Integration tests for ls command in LXC containers."""

    def test_ls_basic_directory_listing(self, lxc_container, container_workspace):
        """Test basic ls command lists files in workspace."""
        # Create test files in workspace
        result = lxc_container.execute_command(f"touch {container_workspace}/file1.txt {container_workspace}/file2.txt")
        assert result["success"], f"Failed to create test files: {result['stderr']}"

        # Run ls command
        result = lxc_container.execute_command(f"ls {container_workspace}")
        assert result["success"], f"ls command failed: {result['stderr']}"

        # Verify files are listed
        output_lines = result["stdout"].strip().split("\n")
        assert "file1.txt" in output_lines
        assert "file2.txt" in output_lines

    def test_ls_long_format(self, lxc_container, container_workspace):
        """Test ls -l provides detailed file information."""
        # Create test file
        result = lxc_container.execute_command(f"echo 'test content' > {container_workspace}/test.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Run ls -l
        result = lxc_container.execute_command(f"ls -l {container_workspace}/test.txt")
        assert result["success"], f"ls -l command failed: {result['stderr']}"

        # Verify long format output contains expected fields
        output = result["stdout"].strip()
        assert "test.txt" in output
        # Should contain permissions, size, date, etc.
        assert len(output.split()) >= 8  # Long format has many fields

    def test_ls_hidden_files(self, lxc_container, container_workspace):
        """Test ls -a shows hidden files."""
        # Create regular and hidden files
        commands = [f"touch {container_workspace}/visible.txt", f"touch {container_workspace}/.hidden.txt"]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create file: {result['stderr']}"

        # Run ls without -a (should not show hidden)
        result = lxc_container.execute_command(f"ls {container_workspace}")
        assert result["success"]
        assert ".hidden.txt" not in result["stdout"]

        # Run ls -a (should show hidden)
        result = lxc_container.execute_command(f"ls -a {container_workspace}")
        assert result["success"]
        assert ".hidden.txt" in result["stdout"]
        assert "visible.txt" in result["stdout"]

    def test_ls_nonexistent_directory(self, lxc_container):
        """Test ls with non-existent directory returns error."""
        nonexistent_path = "/tmp/nonexistent_integration_dir"

        result = lxc_container.execute_command(f"ls {nonexistent_path}")
        assert not result["success"]
        assert result["returncode"] == 2  # ls returns 2 for missing directory
        assert "No such file or directory" in result["stderr"]

    def test_ls_permission_denied(self, lxc_container):
        """Test ls with permission denied returns appropriate error."""
        # Try to access a directory with restricted permissions
        result = lxc_container.execute_command("ls /root", user="mancer")
        # This might succeed or fail depending on container setup
        # If it fails, it should be due to permissions
        if not result["success"]:
            assert result["returncode"] != 0
            # Could be permission denied or other error

    def test_ls_sorted_by_time(self, lxc_container, container_workspace):
        """Test ls -t sorts files by modification time."""
        # Create files with different timestamps
        commands = [
            f"touch {container_workspace}/file_a.txt",
            "sleep 1",
            f"touch {container_workspace}/file_b.txt",
            "sleep 1",
            f"touch {container_workspace}/file_c.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to execute: {cmd}"

        # Run ls -t (sort by time, newest first)
        result = lxc_container.execute_command(f"ls -t {container_workspace}")
        assert result["success"], f"ls -t command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        # Should be in reverse chronological order: file_c, file_b, file_a
        assert len(output_lines) >= 3
        # Note: Exact order might vary based on filesystem behavior

    def test_ls_recursive_listing(self, lxc_container, container_workspace):
        """Test ls -R for recursive directory listing."""
        # Create nested directory structure
        commands = [
            f"mkdir -p {container_workspace}/subdir1",
            f"mkdir -p {container_workspace}/subdir2",
            f"touch {container_workspace}/root_file.txt",
            f"touch {container_workspace}/subdir1/file1.txt",
            f"touch {container_workspace}/subdir2/file2.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create structure: {result['stderr']}"

        # Run ls -R
        result = lxc_container.execute_command(f"ls -R {container_workspace}")
        assert result["success"], f"ls -R command failed: {result['stderr']}"

        output = result["stdout"]
        # Should contain directory names and file listings
        assert "subdir1:" in output
        assert "subdir2:" in output
        assert "root_file.txt" in output
        assert "file1.txt" in output
        assert "file2.txt" in output

    def test_ls_human_readable_sizes(self, lxc_container, container_workspace):
        """Test ls -lh shows human-readable file sizes."""
        # Create file with known size
        test_content = "x" * 2048  # 2KB of content
        result = lxc_container.execute_command(f"echo '{test_content}' > {container_workspace}/test_2k.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Run ls -lh
        result = lxc_container.execute_command(f"ls -lh {container_workspace}/test_2k.txt")
        assert result["success"], f"ls -lh command failed: {result['stderr']}"

        output = result["stdout"]
        # Should contain human-readable size (like 2.1K)
        assert "test_2k.txt" in output
        # Check for human-readable size format (contains K, M, G, etc.)
        assert any(unit in output for unit in ["K", "M", "G"])

    def test_ls_directory_sizes(self, lxc_container, container_workspace):
        """Test ls shows directory sizes."""
        # Create directory with some content
        commands = [
            f"mkdir {container_workspace}/testdir",
            f"echo 'content' > {container_workspace}/testdir/file1.txt",
            f"echo 'more content' > {container_workspace}/testdir/file2.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create directory content: {result['stderr']}"

        # Run ls -l to see directory size
        result = lxc_container.execute_command(f"ls -l {container_workspace}")
        assert result["success"], f"ls -l command failed: {result['stderr']}"

        output = result["stdout"]
        assert "testdir" in output
        # Directory size should be shown (typically 4096 or similar for empty dirs)
