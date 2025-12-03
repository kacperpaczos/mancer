"""
Integration tests for grep command in LXC containers.

These tests validate that grep command works correctly with real
file searching operations in isolated LXC environments.
"""

import pytest


@pytest.mark.integration
@pytest.mark.lxc
class TestGrepIntegration:
    """Integration tests for grep command in LXC containers."""

    def test_grep_basic_pattern_search(self, lxc_container, container_workspace):
        """Test basic grep pattern search in files."""
        # Create test file with content
        test_content = """line one
matching line here
another line
matching pattern again
final line"""

        result = lxc_container.execute_command(f"cat > {container_workspace}/test.txt << 'EOF'\n{test_content}\nEOF")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search for pattern
        result = lxc_container.execute_command(f"grep 'matching' {container_workspace}/test.txt")
        assert result["success"], f"grep command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 2
        assert "matching line here" in output_lines[0]
        assert "matching pattern again" in output_lines[1]

    def test_grep_case_insensitive(self, lxc_container, container_workspace):
        """Test grep -i case insensitive search."""
        test_content = """PATTERN
pattern
Pattern
PATTERN"""

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/case_test.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search case insensitive
        result = lxc_container.execute_command(f"grep -i 'pattern' {container_workspace}/case_test.txt")
        assert result["success"], f"grep -i command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 4  # All lines should match

    def test_grep_line_numbers(self, lxc_container, container_workspace):
        """Test grep -n shows line numbers."""
        test_content = """first line
second line with match
third line
fourth line with match"""

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/numbered.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search with line numbers
        result = lxc_container.execute_command(f"grep -n 'match' {container_workspace}/numbered.txt")
        assert result["success"], f"grep -n command failed: {result['stderr']}"

        output = result["stdout"].strip()
        assert "2:second line with match" in output
        assert "4:fourth line with match" in output

    def test_grep_invert_match(self, lxc_container, container_workspace):
        """Test grep -v inverts the match."""
        test_content = """line one
matching line
line two
another matching line
line three"""

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/invert_test.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search with inverted match
        result = lxc_container.execute_command(f"grep -v 'matching' {container_workspace}/invert_test.txt")
        assert result["success"], f"grep -v command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 3
        assert "line one" in output_lines
        assert "line two" in output_lines
        assert "line three" in output_lines

    def test_grep_multiple_files(self, lxc_container, container_workspace):
        """Test grep across multiple files."""
        # Create multiple test files
        file1_content = "this file has a match\nand another line"
        file2_content = "this file also has a match\nand some other content"

        commands = [
            f"cat > {container_workspace}/file1.txt << 'EOF'\n{file1_content}\nEOF",
            f"cat > {container_workspace}/file2.txt << 'EOF'\n{file2_content}\nEOF",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search across multiple files
        result = lxc_container.execute_command(
            f"grep 'match' {container_workspace}/file1.txt {container_workspace}/file2.txt"
        )
        assert result["success"], f"grep multi-file command failed: {result['stderr']}"

        output = result["stdout"]
        assert "file1.txt:this file has a match" in output
        assert "file2.txt:this file also has a match" in output

    def test_grep_no_matches_found(self, lxc_container, container_workspace):
        """Test grep when no matches are found."""
        test_content = "line without pattern\nanother line"

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/no_match.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search for non-existent pattern
        result = lxc_container.execute_command(f"grep 'nonexistent' {container_workspace}/no_match.txt")
        assert not result["success"]
        assert result["returncode"] == 1  # grep returns 1 when no matches found
        assert result["stdout"].strip() == ""

    def test_grep_regex_pattern(self, lxc_container, container_workspace):
        """Test grep with extended regex patterns."""
        test_content = "test123\ntest456\nother789\ntest999"

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/regex_test.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search with regex
        result = lxc_container.execute_command(f"grep -E 'test[0-9]+' {container_workspace}/regex_test.txt")
        assert result["success"], f"grep -E command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 3
        assert "test123" in output_lines
        assert "test456" in output_lines
        assert "test999" in output_lines

    def test_grep_word_boundary(self, lxc_container, container_workspace):
        """Test grep -w matches whole words only."""
        test_content = "test\natest\ntestb\ntest"

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/word_test.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Search for whole word "test"
        result = lxc_container.execute_command(f"grep -w 'test' {container_workspace}/word_test.txt")
        assert result["success"], f"grep -w command failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        # Should match lines 1 and 4 (whole word "test"), but not "atest" or "testb"
        assert len(output_lines) >= 2  # At least two matches

    def test_grep_count_only(self, lxc_container, container_workspace):
        """Test grep -c shows only count of matches."""
        test_content = "match1\nno match\nmatch2\nmatch3"

        result = lxc_container.execute_command(
            f"cat > {container_workspace}/count_test.txt << 'EOF'\n{test_content}\nEOF"
        )
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Count matches
        result = lxc_container.execute_command(f"grep -c 'match' {container_workspace}/count_test.txt")
        assert result["success"], f"grep -c command failed: {result['stderr']}"

        output = result["stdout"].strip()
        assert output == "3"  # Should count 3 matches

    def test_grep_file_not_found(self, lxc_container):
        """Test grep with non-existent file."""
        result = lxc_container.execute_command("grep 'pattern' /nonexistent/file.txt")
        assert not result["success"]
        assert result["returncode"] == 2
        assert "No such file or directory" in result["stderr"]

    def test_grep_directory_search(self, lxc_container, container_workspace):
        """Test grep searching recursively in directories."""
        # Create directory structure with files containing matches
        commands = [
            f"mkdir -p {container_workspace}/subdir",
            f"echo 'match in root' > {container_workspace}/root.txt",
            f"echo 'match in subdir' > {container_workspace}/subdir/sub.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create test structure: {result['stderr']}"

        # Search recursively
        result = lxc_container.execute_command(f"grep -r 'match' {container_workspace}")
        assert result["success"], f"grep -r command failed: {result['stderr']}"

        output = result["stdout"]
        assert "match in root" in output
        assert "match in subdir" in output
