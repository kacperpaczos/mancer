from __future__ import annotations

from unittest.mock import MagicMock

from mancer.infrastructure.factory.command_factory import CommandFactory


class TestCommandFactory:
    def test_create_known_command_returns_instance(self):
        factory = CommandFactory()
        command = factory.create_command("ls")

        assert command is not None
        assert hasattr(command, "build_command")
        assert hasattr(command, "execute")

    def test_create_unknown_command_returns_none(self):
        factory = CommandFactory()
        assert factory.create_command("nonexistent-command") is None

    def test_register_and_get_command_returns_clone(self):
        factory = CommandFactory()
        stored_command = MagicMock()
        cloned_command = MagicMock()
        stored_command.clone.return_value = cloned_command

        factory.register_command("list-home", stored_command)
        result = factory.get_command("list-home")

        stored_command.clone.assert_called_once()
        assert result is cloned_command

    def test_get_command_unknown_alias_returns_none(self):
        factory = CommandFactory()
        assert factory.get_command("missing-alias") is None

