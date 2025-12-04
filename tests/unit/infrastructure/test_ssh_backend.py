"""Unit tests for SshBackend - SSH command execution."""

from __future__ import annotations

from mancer.infrastructure.backend.ssh_backend import SshBackend, SshBackendFactory


class TestSshBackend:
    """Tests for SshBackend initialization and configuration."""

    def test_initialization_with_defaults(self) -> None:
        """Backend initializes with default values."""
        backend = SshBackend(hostname="example.com")

        assert backend.hostname == "example.com"
        assert backend.port == 22
        assert backend.allow_agent is True
        assert backend.look_for_keys is True
        assert backend.gssapi_auth is False

    def test_initialization_with_all_params(self) -> None:
        """Backend stores all parameters correctly."""
        backend = SshBackend(
            hostname="secure.example.com",
            username="admin",
            port=2222,
            key_filename="/path/to/key",
            password="secret",
            passphrase="phrase",
            allow_agent=False,
            look_for_keys=False,
            compress=True,
            timeout=30,
            gssapi_auth=True,
            gssapi_kex=True,
            gssapi_delegate_creds=True,
            ssh_options={"StrictHostKeyChecking": "no"},
        )

        assert backend.hostname == "secure.example.com"
        assert backend.username == "admin"
        assert backend.port == 2222
        assert backend.key_filename == "/path/to/key"
        assert backend.password == "secret"
        assert backend.passphrase == "phrase"
        assert backend.allow_agent is False
        assert backend.look_for_keys is False
        assert backend.compress is True
        assert backend.timeout == 30
        assert backend.gssapi_auth is True
        assert backend.gssapi_kex is True
        assert backend.gssapi_delegate_creds is True
        assert backend.ssh_options == {"StrictHostKeyChecking": "no"}

    def test_sessions_dict_initialized(self) -> None:
        """Sessions dictionary is initialized empty."""
        backend = SshBackend(hostname="test.com")
        assert backend.sessions == {}

    def test_parse_output_success(self) -> None:
        """parse_output creates successful CommandResult."""
        backend = SshBackend(hostname="test.com")
        result = backend.parse_output("echo test", "output line\n", 0, "")

        assert result.success
        assert result.exit_code == 0
        assert result.raw_output == "output line\n"
        assert result.error_message is None

    def test_parse_output_failure(self) -> None:
        """parse_output creates failed CommandResult with error."""
        backend = SshBackend(hostname="test.com")
        result = backend.parse_output("bad_cmd", "", 1, "command not found")

        assert not result.success
        assert result.exit_code == 1
        assert result.error_message == "command not found"

    def test_build_command_string_basic(self) -> None:
        """build_command_string creates correct command."""
        backend = SshBackend(hostname="test.com")
        cmd = backend.build_command_string("ls", [], {}, [])

        assert cmd == "ls"

    def test_build_command_string_with_options(self) -> None:
        """build_command_string includes options."""
        backend = SshBackend(hostname="test.com")
        cmd = backend.build_command_string("ls", ["-l", "-a"], {}, [])

        assert "ls" in cmd
        assert "-l" in cmd
        assert "-a" in cmd

    def test_build_command_string_with_flags(self) -> None:
        """build_command_string includes flags."""
        backend = SshBackend(hostname="test.com")
        cmd = backend.build_command_string("find", [], {}, ["recursive"])

        assert "find" in cmd
        assert "recursive" in cmd  # Flags are appended as-is

    def test_build_command_string_with_params(self) -> None:
        """build_command_string includes parameters."""
        backend = SshBackend(hostname="test.com")
        cmd = backend.build_command_string("grep", [], {"pattern": "test"}, [])

        assert "grep" in cmd
        assert "test" in cmd


class TestSshBackendFactory:
    """Tests for SshBackendFactory."""

    def test_create_backend_returns_instance(self) -> None:
        """Factory returns SshBackend instance."""
        backend = SshBackendFactory.create_backend(hostname="example.com")

        assert isinstance(backend, SshBackend)
        assert backend.hostname == "example.com"

    def test_create_backend_with_defaults(self) -> None:
        """Factory creates backend with default values."""
        backend = SshBackendFactory.create_backend(hostname="example.com")

        assert backend.port == 22
        assert backend.allow_agent is True
        assert backend.look_for_keys is True

    def test_create_backend_passes_all_params(self) -> None:
        """Factory passes all parameters to backend."""
        backend = SshBackendFactory.create_backend(
            hostname="secure.example.com",
            username="admin",
            port=2222,
            key_filename="/keys/id_rsa",
            password="pass123",
            allow_agent=False,
            compress=True,
            timeout=30,
            gssapi_auth=True,
        )

        assert backend.hostname == "secure.example.com"
        assert backend.username == "admin"
        assert backend.port == 2222
        assert backend.key_filename == "/keys/id_rsa"
        assert backend.password == "pass123"
        assert backend.allow_agent is False
        assert backend.compress is True
        assert backend.timeout == 30
        assert backend.gssapi_auth is True


class TestSshBackendSession:
    """Tests for SSH session management."""

    def test_create_session(self) -> None:
        """create_session returns SSHSession object."""
        backend = SshBackend(hostname="testhost.com", username="user")
        session = backend.create_session("test-session-1")

        assert session is not None
        assert session.id == "test-session-1"
        assert session.hostname == "testhost.com"
        assert "test-session-1" in backend.sessions

    def test_create_session_stores_in_dict(self) -> None:
        """Created session is stored in sessions dict."""
        backend = SshBackend(hostname="test.com")
        backend.create_session("session-1")

        assert "session-1" in backend.sessions
        assert backend.sessions["session-1"].id == "session-1"

    def test_switch_session_success(self) -> None:
        """switch_session returns True for valid session."""
        backend = SshBackend(hostname="test.com")
        session = backend.create_session("session-1")
        session.status = "connected"

        result = backend.switch_session("session-1")

        assert result is True
        assert backend.active_session == "session-1"

    def test_switch_session_fails_for_nonexistent(self) -> None:
        """switch_session returns False for non-existent session."""
        backend = SshBackend(hostname="test.com")

        result = backend.switch_session("nonexistent")

        assert result is False


class TestSshBackendSecurity:
    """Tests for SSH backend security features."""

    def test_key_based_auth_stores_key_path(self) -> None:
        """Backend stores key file path."""
        backend = SshBackend(
            hostname="secure.com",
            key_filename="/path/to/private/key",
        )

        assert backend.key_filename == "/path/to/private/key"

    def test_ssh_agent_enabled_by_default(self) -> None:
        """SSH agent is enabled by default."""
        backend = SshBackend(hostname="test.com")

        assert backend.allow_agent is True

    def test_gssapi_auth_disabled_by_default(self) -> None:
        """GSSAPI authentication is disabled by default."""
        backend = SshBackend(hostname="test.com")

        assert backend.gssapi_auth is False
        assert backend.gssapi_kex is False
        assert backend.gssapi_delegate_creds is False

    def test_look_for_keys_enabled_by_default(self) -> None:
        """Looking for keys in ~/.ssh is enabled by default."""
        backend = SshBackend(hostname="test.com")

        assert backend.look_for_keys is True

    def test_compression_disabled_by_default(self) -> None:
        """Compression is disabled by default."""
        backend = SshBackend(hostname="test.com")

        assert backend.compress is False
