import pytest
import os
from mancer import shell

@pytest.mark.integration
class TestShellIntegration:
    def test_ls_integration(self):
        # Utworzenie testowego pliku
        with open("test_file.txt", "w") as f:
            f.write("test")
            
        # Test ls w bieżącym katalogu
        result = shell.ls().run()
        assert result.return_code == 0
        assert isinstance(result.stdout, str)
        assert len(result.stdout) > 0

        # Test ls z opcjami
        result = shell.ls(options="-la").run()
        assert result.return_code == 0
        assert any(x in result.stdout for x in ["total", "razem"])  # obsługa różnych języków

    def test_cd_ls_combination(self):
        initial_dir = os.getcwd()
        
        # Zmiana katalogu i listing
        shell.cd("/tmp")
        result = shell.ls().run()
        assert result.return_code == 0
        
        # Sprzątanie
        os.chdir(initial_dir) 