"""
Integration tests for file operations in LXC containers.

These tests validate multi-command file operations and workflows
that combine different coreutils commands.
"""

import pytest


@pytest.mark.integration
@pytest.mark.lxc
class TestFileOperationsIntegration:
    """Integration tests for file operations combining multiple commands."""

    def test_create_and_list_files(self, lxc_container, container_workspace):
        """Test creating files and listing them."""
        # Create multiple files
        commands = [
            f"touch {container_workspace}/file1.txt",
            f"touch {container_workspace}/file2.txt",
            f"echo 'content' > {container_workspace}/file3.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to execute: {cmd}"

        # List files
        result = lxc_container.execute_command(f"ls {container_workspace}")
        assert result["success"], f"ls command failed: {result['stderr']}"

        files = result["stdout"].strip().split("\n")
        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "file3.txt" in files

    def test_copy_and_verify_files(self, lxc_container, container_workspace):
        """Test copying files and verifying content."""
        # Create source file
        source_content = "This is the source content"
        result = lxc_container.execute_command(f"echo '{source_content}' > {container_workspace}/source.txt")
        assert result["success"], f"Failed to create source file: {result['stderr']}"

        # Copy file
        result = lxc_container.execute_command(f"cp {container_workspace}/source.txt {container_workspace}/copy.txt")
        assert result["success"], f"cp command failed: {result['stderr']}"

        # Verify copy exists
        result = lxc_container.execute_command(f"ls {container_workspace}/copy.txt")
        assert result["success"], f"Copy file not found: {result['stderr']}"

        # Verify content is identical
        result = lxc_container.execute_command(f"diff {container_workspace}/source.txt {container_workspace}/copy.txt")
        assert result["success"], f"Files differ: {result['stderr']}"

    def test_move_and_rename_files(self, lxc_container, container_workspace):
        """Test moving and renaming files."""
        # Create file
        result = lxc_container.execute_command(f"touch {container_workspace}/original.txt")
        assert result["success"], f"Failed to create file: {result['stderr']}"

        # Rename file
        result = lxc_container.execute_command(
            f"mv {container_workspace}/original.txt {container_workspace}/renamed.txt"
        )
        assert result["success"], f"mv command failed: {result['stderr']}"

        # Verify old name gone
        result = lxc_container.execute_command(f"ls {container_workspace}/original.txt 2>/dev/null || echo 'not found'")
        assert "not found" in result["stdout"] or result["returncode"] != 0

        # Verify new name exists
        result = lxc_container.execute_command(f"ls {container_workspace}/renamed.txt")
        assert result["success"], f"Renamed file not found: {result['stderr']}"

    def test_file_permissions_workflow(self, lxc_container, container_workspace):
        """Test file permissions creation and verification."""
        # Create file
        result = lxc_container.execute_command(f"touch {container_workspace}/perm_test.txt")
        assert result["success"], f"Failed to create file: {result['stderr']}"

        # Change permissions
        result = lxc_container.execute_command(f"chmod 755 {container_workspace}/perm_test.txt")
        assert result["success"], f"chmod command failed: {result['stderr']}"

        # Verify permissions
        result = lxc_container.execute_command(f"ls -l {container_workspace}/perm_test.txt")
        assert result["success"], f"ls -l command failed: {result['stderr']}"

        # Check for expected permission string (should start with -rwxr-xr-x)
        output = result["stdout"].strip()
        assert "-rwxr-xr-x" in output or "-rwxr-xr-x" in output.replace(" ", "")

    def test_directory_operations(self, lxc_container, container_workspace):
        """Test directory creation, navigation, and cleanup."""
        # Create directory structure
        result = lxc_container.execute_command(f"mkdir -p {container_workspace}/testdir/subdir")
        assert result["success"], f"mkdir command failed: {result['stderr']}"

        # Create files in directories
        commands = [
            f"touch {container_workspace}/testdir/file1.txt",
            f"touch {container_workspace}/testdir/subdir/file2.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create file: {cmd}"

        # Count files recursively
        result = lxc_container.execute_command(f"find {container_workspace}/testdir -type f | wc -l")
        assert result["success"], f"find command failed: {result['stderr']}"
        assert result["stdout"].strip() == "2"

        # Remove directory recursively
        result = lxc_container.execute_command(f"rm -rf {container_workspace}/testdir")
        assert result["success"], f"rm command failed: {result['stderr']}"

        # Verify cleanup
        result = lxc_container.execute_command(f"ls {container_workspace}/testdir 2>/dev/null || echo 'cleaned'")
        assert "cleaned" in result["stdout"] or result["returncode"] != 0

    def test_text_processing_pipeline(self, lxc_container, container_workspace):
        """Test text processing pipeline with multiple commands."""
        # Create input file
        input_content = """line with pattern1
another line
line with pattern2
final line"""

        result = lxc_container.execute_command(f"cat > {container_workspace}/input.txt << 'EOF'\n{input_content}\nEOF")
        assert result["success"], f"Failed to create input file: {result['stderr']}"

        # Process through pipeline: grep -> sort -> uniq -> wc
        pipeline_cmd = f"grep 'pattern' {container_workspace}/input.txt | sort | uniq | wc -l"
        result = lxc_container.execute_command(pipeline_cmd)
        assert result["success"], f"Pipeline command failed: {result['stderr']}"

        # Should find 2 unique lines with "pattern"
        assert result["stdout"].strip() == "2"

    def test_file_archiving_workflow(self, lxc_container, container_workspace):
        """Test file archiving and extraction workflow."""
        # Create files to archive
        commands = [
            f"echo 'file1 content' > {container_workspace}/file1.txt",
            f"echo 'file2 content' > {container_workspace}/file2.txt",
        ]

        for cmd in commands:
            result = lxc_container.execute_command(cmd)
            assert result["success"], f"Failed to create file: {cmd}"

        # Create tar archive
        result = lxc_container.execute_command(
            f"cd {container_workspace} && tar -czf archive.tar.gz file1.txt file2.txt"
        )
        assert result["success"], f"tar command failed: {result['stderr']}"

        # Verify archive exists
        result = lxc_container.execute_command(f"ls {container_workspace}/archive.tar.gz")
        assert result["success"], f"Archive not created: {result['stderr']}"

        # Extract archive to new location
        result = lxc_container.execute_command(
            f"cd {container_workspace} && mkdir extract && cd extract && tar -xzf ../archive.tar.gz"
        )
        assert result["success"], f"tar extraction failed: {result['stderr']}"

        # Verify extracted files
        result = lxc_container.execute_command(f"ls {container_workspace}/extract/")
        assert result["success"], f"Extracted files not found: {result['stderr']}"
        files = result["stdout"].strip().split("\n")
        assert "file1.txt" in files
        assert "file2.txt" in files

    def test_large_file_handling(self, lxc_container, container_workspace):
        """Test handling of larger files."""
        # Create larger file (1MB)
        result = lxc_container.execute_command(
            f"dd if=/dev/zero of={container_workspace}/large_file.dat bs=1024 count=1024 2>/dev/null"
        )
        assert result["success"], f"Failed to create large file: {result['stderr']}"

        # Verify file size
        result = lxc_container.execute_command(f"du -h {container_workspace}/large_file.dat")
        assert result["success"], f"du command failed: {result['stderr']}"
        assert "1.0M" in result["stdout"] or "1024" in result["stdout"]

        # Test file operations on large file
        result = lxc_container.execute_command(
            f"cp {container_workspace}/large_file.dat {container_workspace}/large_copy.dat"
        )
        assert result["success"], f"Copy large file failed: {result['stderr']}"

        # Verify copy
        result = lxc_container.execute_command(
            f"diff {container_workspace}/large_file.dat {container_workspace}/large_copy.dat"
        )
        assert result["success"], f"Large file copy differs: {result['stderr']}"

    def test_concurrent_file_operations(self, lxc_container, container_workspace):
        """Test multiple file operations running concurrently."""
        # This is a simplified test - in real scenarios would use background processes
        # Create multiple files quickly
        result = lxc_container.execute_command(f"cd {container_workspace} && touch file{{1..10}}.txt")
        assert result["success"], f"Failed to create multiple files: {result['stderr']}"

        # Count files
        result = lxc_container.execute_command(f"ls {container_workspace}/*.txt | wc -l")
        assert result["success"], f"File count failed: {result['stderr']}"
        assert result["stdout"].strip() == "10"

        # Process all files
        result = lxc_container.execute_command(
            f'cd {container_workspace} && for f in *.txt; do echo processed >> "$f"; done'
        )
        assert result["success"], f"Batch processing failed: {result['stderr']}"

        # Verify processing
        result = lxc_container.execute_command(f"grep -l 'processed' {container_workspace}/*.txt | wc -l")
        assert result["success"], f"Processing verification failed: {result['stderr']}"
        assert result["stdout"].strip() == "10"
