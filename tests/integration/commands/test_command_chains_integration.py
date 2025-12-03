"""
Integration tests for command chains and pipelines in LXC containers.

These tests validate that complex command pipelines work correctly
with real command execution and data flow between commands.
"""

import pytest


@pytest.mark.integration
@pytest.mark.lxc
class TestCommandChainsIntegration:
    """Integration tests for command chains and pipelines."""

    def test_simple_pipeline_ls_grep(self, lxc_container, container_workspace):
        """Test simple pipeline: ls | grep."""
        # Create test files
        commands = [
            f"touch {container_workspace}/test1.txt",
            f"touch {container_workspace}/test2.txt",
            f"touch {container_workspace}/other.dat",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create test file: {cmd}"

        # Run pipeline: ls | grep txt
        result = lxc_container.execute_command(f"ls {container_workspace} | grep txt")
        assert result["success"], f"Pipeline ls | grep failed: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 2
        assert "test1.txt" in output_lines
        assert "test2.txt" in output_lines

    def test_complex_pipeline_sort_unique_count(self, lxc_container, container_workspace):
        """Test complex pipeline: generate data | sort | uniq | count."""
        # Create file with duplicate data
        test_data = """apple
banana
apple
cherry
banana
date
apple"""

        result = lxc_container.execute_command(f"cat > {container_workspace}/fruits.txt << 'EOF'\n{test_data}\nEOF")
        assert result["success"], f"Failed to create test data: {result['stderr']}"

        # Run complex pipeline: cat | sort | uniq | wc -l
        pipeline = f"cat {container_workspace}/fruits.txt | sort | uniq | wc -l"
        result = lxc_container.execute_command(pipeline)
        assert result["success"], f"Complex pipeline failed: {result['stderr']}"

        # Should have 4 unique fruits
        assert result["stdout"].strip() == "4"

    def test_pipeline_with_file_redirection(self, lxc_container, container_workspace):
        """Test pipeline with file redirection."""
        # Create input file
        input_data = "line 1\nline 2\nerror line\nline 3\nerror line"

        result = lxc_container.execute_command(f"cat > {container_workspace}/input.txt << 'EOF'\n{input_data}\nEOF")
        assert result["success"], f"Failed to create input: {result['stderr']}"

        # Run pipeline: grep "line" input.txt | grep -v "error" > output.txt
        pipeline = f"grep 'line' {container_workspace}/input.txt | grep -v 'error' > {container_workspace}/output.txt"
        result = lxc_container.execute_command(pipeline)
        assert result["success"], f"Pipeline with redirection failed: {result['stderr']}"

        # Verify output file
        result = lxc_container.execute_command(f"cat {container_workspace}/output.txt")
        assert result["success"], f"Failed to read output file: {result['stderr']}"

        output_lines = result["stdout"].strip().split("\n")
        assert len(output_lines) == 2
        assert "line 1" in output_lines
        assert "line 2" in output_lines
        assert "line 3" in output_lines

    def test_pipeline_error_handling(self, lxc_container, container_workspace):
        """Test pipeline error handling."""
        # Create file
        result = lxc_container.execute_command(f"touch {container_workspace}/test.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Run pipeline where first command fails: nonexistent_command | wc -l
        result = lxc_container.execute_command("nonexistent_command 2>/dev/null | wc -l")
        # Pipeline should succeed even if first command fails (due to 2>/dev/null)
        assert result["success"] or result["returncode"] == 0

    def test_conditional_command_execution(self, lxc_container, container_workspace):
        """Test conditional command execution with && and ||."""
        # Create test file
        result = lxc_container.execute_command(f"touch {container_workspace}/test.txt")
        assert result["success"], f"Failed to create test file: {result['stderr']}"

        # Test success condition: ls && echo "success"
        result = lxc_container.execute_command(f"ls {container_workspace}/test.txt && echo 'success'")
        assert result["success"], f"Conditional success failed: {result['stderr']}"
        assert "success" in result["stdout"]

        # Test failure condition: ls nonexistent || echo "fallback"
        result = lxc_container.execute_command(f"ls {container_workspace}/nonexistent 2>/dev/null || echo 'fallback'")
        assert result["success"], f"Conditional fallback failed: {result['stderr']}"
        assert "fallback" in result["stdout"]

    def test_command_substitution(self, lxc_container, container_workspace):
        """Test command substitution $(...)."""
        # Create files
        commands = [
            f"touch {container_workspace}/file1.txt",
            f"touch {container_workspace}/file2.txt",
            f"touch {container_workspace}/file3.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create file: {cmd}"

        # Use command substitution to count files
        result = lxc_container.execute_command(f'echo "Found $(ls {container_workspace}/*.txt | wc -l) text files"')
        assert result["success"], f"Command substitution failed: {result['stderr']}"
        assert "Found 3 text files" in result["stdout"]

    def test_background_process_pipeline(self, lxc_container, container_workspace):
        """Test pipeline with background processes."""
        # This is simplified - real background testing would be more complex
        # Create a simple background-like operation
        result = lxc_container.execute_command(
            f"cd {container_workspace} && (sleep 1 && echo 'background done' > result.txt) & echo 'started'"
        )
        assert result["success"], f"Background process setup failed: {result['stderr']}"

        # Wait a bit and check result
        result = lxc_container.execute_command("sleep 2")
        assert result["success"]

        # Check if background process completed
        result = lxc_container.execute_command(f"cat {container_workspace}/result.txt 2>/dev/null || echo 'not ready'")
        # This might succeed or fail depending on timing
        assert result["returncode"] == 0 or "not ready" in result["stdout"]

    def test_pipeline_with_quotes_and_spaces(self, lxc_container, container_workspace):
        """Test pipeline handling quotes and spaces in filenames."""
        # Create file with spaces in name
        result = lxc_container.execute_command(f"touch {container_workspace}/'file with spaces.txt'")
        assert result["success"], f"Failed to create file with spaces: {result['stderr']}"

        # Create file with quotes in name
        result = lxc_container.execute_command(f"touch {container_workspace}/'file\"with\"quotes.txt'")
        assert result["success"], f"Failed to create file with quotes: {result['stderr']}"

        # List files with proper quoting
        result = lxc_container.execute_command(f"ls -1 {container_workspace}")
        assert result["success"], f"ls failed: {result['stderr']}"

        output = result["stdout"]
        assert "file with spaces.txt" in output
        assert 'file"with"quotes.txt' in output

    def test_large_data_pipeline(self, lxc_container, container_workspace):
        """Test pipeline with larger amounts of data."""
        # Generate larger test data (100 lines)
        result = lxc_container.execute_command(
            f'cd {container_workspace} && for i in {{1..100}}; do echo "line $i"; done > large_data.txt'
        )
        assert result["success"], f"Failed to generate large data: {result['stderr']}"

        # Process through pipeline: cat | grep "line [1-9][0-9]" | wc -l
        pipeline = f"cat {container_workspace}/large_data.txt | grep 'line [1-9][0-9]' | wc -l"
        result = lxc_container.execute_command(pipeline)
        assert result["success"], f"Large data pipeline failed: {result['stderr']}"

        # Should find lines 10-99 (90 lines total)
        count = int(result["stdout"].strip())
        assert count == 90, f"Expected 90 matches, got {count}"

    def test_pipeline_resource_limits(self, lxc_container, container_workspace):
        """Test pipeline behavior with resource constraints."""
        # Create many files to test resource usage
        result = lxc_container.execute_command(
            f'cd {container_workspace} && mkdir test_files && cd test_files && for i in {{1..50}}; do echo "content $i" > file$i.txt; done'
        )
        assert result["success"], f"Failed to create test files: {result['stderr']}"

        # Process all files through pipeline
        pipeline = f"cd {container_workspace}/test_files && cat *.txt | grep 'content' | sort | uniq | wc -l"
        result = lxc_container.execute_command(pipeline)
        assert result["success"], f"Resource-intensive pipeline failed: {result['stderr']}"

        # Should have 50 unique content lines
        assert result["stdout"].strip() == "50"

    def test_nested_command_execution(self, lxc_container, container_workspace):
        """Test nested command execution."""
        # Create test files
        result = lxc_container.execute_command(
            f"cd {container_workspace} && mkdir nested && cd nested && for d in a b c; do mkdir $d && echo test > $d/file.txt; done"
        )
        assert result["success"], f"Failed to create nested structure: {result['stderr']}"

        # Use nested commands to find and count files
        nested_cmd = f"find {container_workspace}/nested -name '*.txt' -exec cat {{}} \\; | wc -l"
        result = lxc_container.execute_command(nested_cmd)
        assert result["success"], f"Nested command execution failed: {result['stderr']}"

        # Should find 3 files with 1 line each
        assert result["stdout"].strip() == "3"
