import pytest
import os
import sys
import tempfile

# Dodanie ścieżki do src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture(autouse=True)
def setup_test_env():
    """Przygotowanie środowiska testowego"""
    # Zapisanie oryginalnego katalogu
    original_dir = os.getcwd()
    
    # Utworzenie tymczasowego katalogu testowego
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.chdir(tmp_dir)
        yield
    
    # Przywrócenie oryginalnego katalogu
    os.chdir(original_dir)

def pytest_configure(config):
    """Konfiguracja znaczników"""
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "privileged: tests requiring root privileges")
    config.addinivalue_line("markers", "mock: tests using mocking") 