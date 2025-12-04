"""Unit tests for grep command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from mancer.infrastructure.command.file.grep_command import GrepCommand


class TestGrepCommand:
    """Unit tests for GrepCommand - pattern searching."""

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_basic_pattern_search(self, mock_get_backend, context):
        """Test basic grep pattern search."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "file1.txt:matching line\nfile2.txt:another match\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("test").file("*.txt")
        result = cmd.execute(context)

        assert result.success
        assert "matching line" in result.raw_output
        assert result.exit_code == 0
        mock_backend.execute.assert_called_once()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_case_insensitive(self, mock_get_backend, context):
        """Test grep -i case insensitive search."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:Pattern\nfile.txt:PATTERN\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("pattern").ignore_case()
        result = cmd.execute(context)

        assert result.success
        assert "Pattern" in result.raw_output
        assert "PATTERN" in result.raw_output
        assert "-i" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_line_numbers(self, mock_get_backend, context):
        """Test grep -n with line numbers."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:1:line one\nfile.txt:5:line five\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("line").line_number()
        result = cmd.execute(context)

        assert result.success
        assert "1:line one" in result.raw_output
        assert "-n" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_invert_match(self, mock_get_backend, context):
        """Test grep -v invert match."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "file.txt:line without pattern\nfile.txt:another line\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("pattern").invert_match()
        result = cmd.execute(context)

        assert result.success
        assert "-v" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_recursive(self, mock_get_backend, context):
        """Test grep -r recursive search."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "dir/file.txt:match\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("match").recursive()
        result = cmd.execute(context)

        assert result.success
        assert "-r" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_extended_regex(self, mock_get_backend, context):
        """Test grep -E extended regex."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "file.txt:test123\ntest456\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("test[0-9]+").extended_regexp()
        result = cmd.execute(context)

        assert result.success
        assert "-E" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_count_only(self, mock_get_backend, context):
        """Test grep -c count only mode."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "2\n", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("pattern").count()
        result = cmd.execute(context)

        assert result.success
        assert "-c" in cmd.build_command()

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_no_matches_found(self, mock_get_backend, context):
        """Test grep when no matches are found (exit code 1)."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (1, "", "")
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("nonexistent")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 1

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_file_not_found(self, mock_get_backend, context):
        """Test grep with non-existent file."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            2,
            "",
            "grep: nonexistent.txt: No such file or directory",
        )
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("pattern").file("nonexistent.txt")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "No such file or directory" in result.error_message

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_structured_output_parsing(self, mock_get_backend, context):
        """Test that grep parses output into structured format."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (
            0,
            "file1.txt:10:matching content\nfile2.txt:20:another match\n",
            "",
        )
        mock_get_backend.return_value = mock_backend

        cmd = GrepCommand().pattern("match").line_number()
        result = cmd.execute(context)

        assert result.success
        # Check structured output contains parsed matches
        structured = result.structured_output
        # Handle both list and DataFrame cases
        if hasattr(structured, "to_dicts"):
            data = structured.to_dicts()
        else:
            data = list(structured)
        assert len(data) == 2
        # First match
        first_match = data[0]
        assert first_match["file"] == "file1.txt"
        assert first_match["line_number"] == "10"
        assert "matching content" in first_match["content"]

    @patch("mancer.infrastructure.command.base_command.BaseCommand._get_backend")
    def test_grep_with_stdin_input(self, mock_get_backend, context, result_factory):
        """Test grep reading from stdin (piped input)."""
        mock_backend = MagicMock()
        mock_backend.execute.return_value = (0, "matching line\n", "")
        mock_get_backend.return_value = mock_backend

        input_result = result_factory(output="line1\nmatching line\nline3\n")
        cmd = GrepCommand().pattern("matching")
        result = cmd.execute(context, input_result=input_result)

        assert result.success
        # Verify stdin was passed to backend
        call_args = mock_backend.execute.call_args
        assert call_args.kwargs.get("input_data") == "line1\nmatching line\nline3\n"
