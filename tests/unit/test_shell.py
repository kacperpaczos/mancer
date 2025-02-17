import pytest
from mancer.shell import Shell, shell
from mancer.core import Command, CommandResult
import os

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