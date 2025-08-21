"""
Simple test to debug import issues
"""


def test_python_works():
    """Basic test that Python works"""
    assert 1 + 1 == 2


def test_mancer_import():
    """Test mancer import"""
    try:
        import mancer

        print(f"Mancer version: {mancer.__version__}")
        assert True
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, f"Cannot import mancer: {e}"


def test_mancer_application_import():
    """Test mancer.application import"""
    try:
        import mancer.application

        assert True
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, f"Cannot import mancer.application: {e}"


def test_shell_runner_import():
    """Test ShellRunner import"""
    try:
        from mancer.application.shell_runner import ShellRunner

        assert True
    except ImportError as e:
        print(f"Import error: {e}")
        assert False, f"Cannot import ShellRunner: {e}"
