from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.columns import Columns
from icecream import ic
from pathlib import Path
import subprocess
from typing import List, Dict, Any, Optional
from rich.box import SIMPLE

console = Console()

class CLI:
    def __init__(self, debug: bool = False):
        self.console = Console()
        self.debug = debug
        
    def log(self, message: str, data: Any = None, status: str = None):
        """
        Wyświetla komunikat w konsoli
        
        Args:
            message: Główny komunikat
            data: Dodatkowe dane do wyświetlenia
            status: Status komunikatu (error/success/warning)
        """
        if self.debug:
            ic(message, data)
            return
            
        # Określenie stylu na podstawie statusu
        style = {
            "error": "bold red",
            "success": "bold green",
            "warning": "bold yellow"
        }.get(status, "")
        
        # Przygotowanie tekstu
        text = message
        if data:
            if isinstance(data, dict):
                text += "\n" + "\n".join(f"  {k}: {v}" for k, v in data.items())
            else:
                text += f": {data}"
                
        # Wyświetlenie z odpowiednim formatowaniem
        if status:
            self.console.print(Panel(text, style=style))
        else:
            self.console.print(text)
            
    def show_header(self, text: str):
        self.console.print(Panel(text, style="bold blue"))
        
    def show_menu(self, ssh_connected: bool = False) -> str:
        choices = [
            ("1", "Pobierz pliki z serwera", True),
            ("2", "Wyślij pliki na serwer", True),
            ("3", "Sprawdź różnice", False),
            ("4", "Usuń pliki z cache", False),
            ("5", "Usuń pliki lokalne", False),
            ("6", "Zarządzaj aktualnym połączeniem", False),
            ("7", "Zarządzaj profilami", False),
            ("0", "Zakończ", False)
        ]
        
        self.console.print("\nMenu główne:")
        for num, text, requires_ssh in choices:
            if requires_ssh and not ssh_connected and not self.debug:
                self.console.print(f"[dim]{num}. {text} (wymaga połączenia)[/dim]")
            else:
                self.console.print(f"{num}. {text}")
        
        return Prompt.ask("\nWybierz opcję", choices=[c[0] for c in choices])
        
    def show_file_list(self, files: List[str], title: str):
        table = Table(title=title)
        table.add_column("Ścieżka pliku")
        for file in files:
            table.add_row(file)
        self.console.print(table)
        
    def show_diff_info(self, file: str, status: str, details: Optional[Dict] = None):
        icons = {
            "server": "🔄",
            "local": "📝",
            "error": "❌",
            "success": "✅"
        }
        
        text = f"{icons.get(status, '❓')} {file}"
        if details:
            for key, value in details.items():
                text += f"\n  └─ {key}: {value}"
                
        style = "red" if status == "error" else "green" if status == "success" else "yellow"
        self.console.print(Panel(text, style=style)) 
        
    def show_file_comparison(self, cache_files: List[str], server_files: List[str], 
                            differences: Dict[str, str]):
        """Wyświetla porównanie plików w dwóch kolumnach"""
        layout = Layout()
        layout.split_row(
            Layout(name="cache", ratio=1),
            Layout(name="server", ratio=1)
        )
        
        # Tabela plików cache
        cache_table = Table(title="Pliki w cache", box=SIMPLE)
        cache_table.add_column("Status")
        cache_table.add_column("Ścieżka")
        
        # Tabela plików na serwerze
        server_table = Table(title="Pliki na serwerze", box=SIMPLE)
        server_table.add_column("Status")
        server_table.add_column("Ścieżka")
        
        # Wypełnianie tabel - tylko pliki ze zmianami
        for file in sorted(differences.keys()):
            if file in cache_files:
                cache_table.add_row("❌", file)
            if file in server_files:
                server_table.add_row("❌", file)
        
        # Aktualizacja layoutu
        layout["cache"].update(Panel(cache_table))
        layout["server"].update(Panel(server_table))
        
        self.console.print(layout)
        
    def show_file_diff(self, file1: Path, file2: Path):
        """Pokazuje różnice między plikami używając git diff"""
        try:
            # Najpierw spróbuj otworzyć w nowym oknie
            subprocess.Popen([
                "x-terminal-emulator", 
                "-e", 
                f"git diff --no-index --color {file1} {file2} | less -R"
            ])
        except Exception:
            # Jeśli nie udało się otworzyć nowego okna, pokaż w konsoli
            result = subprocess.run(
                ["git", "diff", "--no-index", "--color", str(file1), str(file2)],
                capture_output=True,
                text=True
            )
            self.console.print(result.stdout if result.returncode == 1 else "Brak różnic") 
        
    def confirm(self, message: str) -> bool:
        """Wyświetla pytanie tak/nie i zwraca odpowiedź użytkownika"""
        return Confirm.ask(message) 

    def show_file_options(self):
        self.console.print(Panel("""
[cyan]Dostępne opcje:[/cyan]
w - wyślij plik
p - przerwij wysyłanie
s - wyślij wszystkie pozostałe
n - pomiń ten plik
        """.strip())) 