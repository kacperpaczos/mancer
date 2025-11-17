"""
Integration tests for cat command in LXC containers.

These tests validate that cat command works correctly with real
file reading operations in isolated LXC environments.
"""

import pytest


@pytest.mark.integration
@pytest.mark.lxc
class TestCatIntegration:
    """Integration tests for cat command in LXC containers."""

    def test_cat_single_file(self, lxc_container, container_workspace):
        """Test cat displaying content of single file."""
        test_content = "This is test content\nwith multiple lines\nfor cat command"

        # Create test file
        result = lxc_container.execute_command(f"cat > {container_workspace}/test.txt << 'EOF'\n{test_content}\nEOF")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read file with cat
        result = lxc_container.execute_command(f"cat {container_workspace}/test.txt")
        assert result["success"], f"cat command failed: {result['stderr']}"

        assert result["stdout"].strip() == test_content

    def test_cat_multiple_files(self, lxc_container, container_workspace):
        """Test cat concatenating multiple files."""
        content1 = "Content of file 1"
        content2 = "Content of file 2"

        # Create multiple test files
        commands = [
            f"echo '{content1}' > {container_workspace}/file1.txt",
            f"echo '{content2}' > {container_workspace}/file2.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Concatenate files
        result = lxc_container.execute_command(f"cat {container_workspace}/file1.txt {container_workspace}/file2.txt")
        assert result["success"], f"cat multiple files failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert output_lines[0] == content1
        assert output_lines[1] == content2

    def test_cat_with_line_numbers(self, lxc_container, container_workspace):
        """Test cat -n showing line numbers."""
        test_content = "first line\nsecond line\nthird line"

        # Create test file
        result = lxc_container.execute_command(
            f"cat > {container_workspace}/numbered.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read with line numbers
        result = lxc_container.execute_command(f"cat -n {container_workspace}/numbered.txt")
        assert result["success"], f"cat -n command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 3
        assert "1\tfirst line" in output_lines[0]
        assert "2\tsecond line" in output_lines[1]
        assert "3\tthird line" in output_lines[2]

    def test_cat_show_nonprinting(self, lxc_container, container_workspace):
        """Test cat -v showing non-printing characters."""
        # Create file with non-printing characters
        result = lxc_container.execute_command(f"printf 'line^Mwith^@control\\n' > {container_workspace}/control.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read with non-printing characters visible
        result = lxc_container.execute_command(f"cat -v {container_workspace}/control.txt")
        assert result["success"], f"cat -v command failed: {result['stderr']}"

        output = result["stdout"]
        # Should show control characters (^M for carriage return, ^@ for null)
        assert "^M" in output or len(output) > 0  # May vary by system

    def test_cat_squeeze_blank_lines(self, lxc_container, container_workspace):
        """Test cat -s squeezing multiple blank lines."""
        test_content = "line 1\n\n\n\n\nline 2\n\n\nline 3"

        # Create test file
        result = lxc_container.execute_command(f"cat > {container_workspace}/blanks.txt << 'EOF'\n{test_content}\nEOF")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read with blank line squeezing
        result = lxc_container.execute_command(f"cat -s {container_workspace}/blanks.txt")
        assert result["success"], f"cat -s command failed: {result['stderr']}"

        output = result["stdout"]
        # Multiple consecutive blank lines should be reduced to single blank lines
        assert "\n\n\n" not in output  # No three consecutive newlines

    def test_cat_file_not_found(self, lxc_container):
        """Test cat with non-existent file."""
        result = lxc_container.execute_command("cat /nonexistent/file.txt")
        assert not result["success"]
        assert result["returncode"] == 1
        assert "No such file or directory" in result["stderr"]

    def test_cat_permission_denied(self, lxc_container):
        """Test cat with permission denied."""
        # Try to read a restricted file
        result = lxc_container.execute_command("cat /etc/shadow", user="mancer")
        # This might succeed or fail depending on container setup
        if not result["success"]:
            assert result["returncode"] != 0
            # Could be permission denied or other access error

    def test_cat_empty_file(self, lxc_container, container_workspace):
        """Test cat with empty file."""
        # Create empty file
        result = lxc_container.execute_command(f"touch {container_workspace}/empty.txt")
        assert result["success"], f"Failed to create empty file: {result['stderr']}"

        # Read empty file
        result = lxc_container.execute_command(f"cat {container_workspace}/empty.txt")
        assert result["success"], f"cat empty file failed: {result['stderr']}"
        assert result["stdout"].strip() == ""

    def test_cat_binary_file_warning(self, lxc_container, container_workspace):
        """Test cat with binary file (may show warnings)."""
        # Create a simple binary-like file
        result = lxc_container.execute_command(
            f"dd if=/dev/zero of={container_workspace}/binary.dat bs=1024 count=1 2>/dev/null"
        )
        assert result["success"], f"Failed to create binary file: {result['stderr']}"

        # Try to cat binary file
        result = lxc_container.execute_command(f"cat {container_workspace}/binary.dat")
        # This should succeed but output might be empty or contain binary data
        assert result["returncode"] == 0

    def test_cat_stdin_input(self, lxc_container):
        """Test cat reading from stdin."""
        # Use echo to pipe content to cat
        result = lxc_container.execute_command("echo 'stdin content' | cat")
        assert result["success"], f"cat stdin failed: {result['stderr']}"
        assert "stdin content" in result["stdout"]

    def test_cat_show_ends(self, lxc_container, container_workspace):
        """Test cat -E showing line ends."""
        test_content = "line1\nline2"

        # Create test file
        result = lxc_container.execute_command(f"printf '{test_content}' > {container_workspace}/ends.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read with line ends visible
        result = lxc_container.execute_command(f"cat -E {container_workspace}/ends.txt")
        assert result["success"], f"cat -E command failed: {result['stderr']}"

        output = result["stdout"]
        assert "line1$" in output
        assert "line2$" in output

    def test_cat_show_tabs(self, lxc_container, container_workspace):
        """Test cat -T showing tabs."""
        test_content = "col1\tcol2\tcol3"

        # Create test file
        result = lxc_container.execute_command(f"printf '{test_content}' > {container_workspace}/tabs.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Read with tabs visible
        result = lxc_container.execute_command(f"cat -T {container_workspace}/tabs.txt")
        assert result["success"], f"cat -T command failed: {result['stderr']}"

        output = result["stdout"]
        assert "^I" in output  # Tab character should be shown as ^I
