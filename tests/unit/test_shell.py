import pytest
from mancer.shell import Shell, shell
from mancer.core import Command, CommandResult
import os
from datetime import datetime

@pytest.fixture
def shell():
    return Shell()

class TestShell:
    def test_ls_command_creation(self, shell):
        # Test podstawowego ls
        cmd = shell.ls()
        assert isinstance(cmd, Command)
        assert cmd.cmd == ["ls"]

        # Test ls z opcjami
        cmd = shell.ls(options="-la")
        assert cmd.cmd == ["ls", "-la"]

        # Test ls ze ścieżką
        cmd = shell.ls(path="/tmp")
        assert cmd.cmd == ["ls", "/tmp"]

        # Test ls z opcjami i ścieżką
        cmd = shell.ls(path="/tmp", options="-la")
        assert cmd.cmd == ["ls", "-la", "/tmp"]

    def test_cd_command(self, shell):
        # Test poprawnej zmiany katalogu
        initial_dir = os.getcwd()
        result = shell.cd("/tmp")
        assert isinstance(result, CommandResult)
        assert result.return_code == 0
        assert os.getcwd() == "/tmp"
        
        # Sprzątanie
        os.chdir(initial_dir)

        # Test błędnej ścieżki
        result = shell.cd("/nieistniejacy/katalog")
        assert result.return_code == 1
        assert result.stderr != ""

    def test_ls_with_parsing(self, shell):
        # Utworzenie testowego pliku
        with open("test_file.txt", "w") as f:
            f.write("test content")
        
        result = shell.ls(options="-la", parse_output=True).run()
        assert result.return_code == 0
        assert hasattr(result, 'parsed_files')
        assert len(result.parsed_files) > 0
        
        test_file = next(f for f in result.parsed_files if f.name == "test_file.txt")
        assert test_file.size > 0
        assert not test_file.is_directory
        assert isinstance(test_file.modified_time, datetime) 