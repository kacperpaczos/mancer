from mancer.application.shell_runner import ShellRunner
import time
import json
import os
import threading
import datetime
import random

# Próba importu bibliotek do wizualizacji
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation
    VISUALIZATION_AVAILABLE = True
except ImportError:
    print("Biblioteka matplotlib nie jest zainstalowana. Wizualizacja nie będzie dostępna.")
    print("Zainstaluj matplotlib: pip install matplotlib")
    VISUALIZATION_AVAILABLE = False

class CacheVisualizer:
    """Klasa do wizualizacji danych z cache'a ShellRunner"""
    
    def __init__(self, runner: ShellRunner, update_interval: float = 1.0):
        """
        Inicjalizuje wizualizator cache'a.
        
        Args:
            runner: Instancja ShellRunner z włączonym cache
            update_interval: Interwał odświeżania wizualizacji w sekundach
        """
        self.runner = runner
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        
        # Dane do wizualizacji
        self.timestamps = []
        self.success_counts = []
        self.error_counts = []
        self.command_types = {}  # Słownik zliczający typy komend
        
        # Inicjalizacja wykresu
        if VISUALIZATION_AVAILABLE:
            self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
            self.fig.suptitle('Wizualizacja cache ShellRunner', fontsize=16)
            
            # Wykres historii wykonania komend
            self.success_line, = self.ax1.plot([], [], 'g-', label='Sukces')
            self.error_line, = self.ax1.plot([], [], 'r-', label='Błąd')
            self.ax1.set_title('Historia wykonania komend')
            self.ax1.set_xlabel('Czas')
            self.ax1.set_ylabel('Liczba komend')
            self.ax1.legend()
            self.ax1.grid(True)
            
            # Wykres typów komend (pie chart)
            self.ax2.set_title('Typy wykonanych komend')
            
            # Formatowanie osi czasu
            self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.ax1.xaxis.set_major_locator(mdates.SecondLocator(interval=5))
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.9)
    
    def start(self):
        """Uruchamia wizualizację w osobnym wątku"""
        if not VISUALIZATION_AVAILABLE:
            print("Wizualizacja nie jest dostępna - brak biblioteki matplotlib")
            return
            
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_visualization)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Zatrzymuje wizualizację"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _run_visualization(self):
        """Główna pętla wizualizacji"""
        ani = FuncAnimation(self.fig, self._update_plot, interval=self.update_interval*1000)
        plt.show()
    
    def _update_plot(self, frame):
        """Aktualizuje wykresy na podstawie danych z cache"""
        # Pobierz dane z cache
        history = self.runner.get_command_history()
        stats = self.runner.get_cache_statistics()
        
        # Aktualizuj dane historyczne
        current_time = datetime.datetime.now()
        self.timestamps.append(current_time)
        
        # Ogranicz historię do ostatnich 60 punktów
        if len(self.timestamps) > 60:
            self.timestamps = self.timestamps[-60:]
            self.success_counts = self.success_counts[-60:]
            self.error_counts = self.error_counts[-60:]
        
        # Zlicz sukcesy i błędy
        success_count = stats.get('success_count', 0)
        error_count = stats.get('error_count', 0)
        
        self.success_counts.append(success_count)
        self.error_counts.append(error_count)
        
        # Aktualizuj wykres historii
        self.success_line.set_data(self.timestamps, self.success_counts)
        self.error_line.set_data(self.timestamps, self.error_counts)
        
        # Dostosuj zakres osi
        if self.timestamps:
            self.ax1.set_xlim(min(self.timestamps), max(self.timestamps))
            max_count = max(max(self.success_counts, default=0), max(self.error_counts, default=0), 1)
            self.ax1.set_ylim(0, max_count * 1.1)
        
        # Aktualizuj wykres typów komend
        self.command_types = {}
        for cmd_id, _, _ in history:
            # W rzeczywistej implementacji należałoby pobrać typ komendy z cache
            # Tutaj używamy losowych typów dla demonstracji
            result = self.runner.get_cached_result(cmd_id)
            if result:
                cmd_type = result.metadata.get('command_type', 'unknown') if result.metadata else 'unknown'
                self.command_types[cmd_type] = self.command_types.get(cmd_type, 0) + 1
        
        # Aktualizuj pie chart
        self.ax2.clear()
        self.ax2.set_title('Typy wykonanych komend')
        if self.command_types:
            self.ax2.pie(
                self.command_types.values(), 
                labels=self.command_types.keys(),
                autopct='%1.1f%%', 
                startangle=90
            )
            self.ax2.axis('equal')
        
        return self.success_line, self.error_line

def simulate_commands(runner, count=20, interval=0.5):
    """Symuluje wykonanie różnych komend dla celów demonstracyjnych"""
    # Używamy wszystkich dostępnych komend
    commands = [
        runner.create_command("ls").long(),
        runner.create_command("ps").aux(),
        runner.create_command("hostname"),
        runner.create_command("netstat").with_param("options", "all"),
        runner.create_command("systemctl").with_param("command", "status").with_param("service", "ssh"),
        runner.create_command("df").human_readable(),
        runner.create_command("echo").text("Hello from visualization example!"),
        runner.create_command("cat").file("/etc/hostname"),
        runner.create_command("grep").pattern("root").file("/etc/passwd"),
        runner.create_command("tail").lines(5).file("/var/log/syslog"),
        runner.create_command("head").lines(5).file("/etc/passwd")
    ]
    
    for i in range(count):
        cmd = random.choice(commands)
        # Dodajemy losowe metadane dla celów demonstracyjnych
        cmd_type = cmd._command_name if hasattr(cmd, '_command_name') else "unknown"
        
        # Wykonujemy komendę z dodatkowymi metadanymi
        result = runner.execute(cmd)
        
        # Dodajemy metadane do wyniku (w rzeczywistej implementacji należałoby to zrobić inaczej)
        if hasattr(result, 'metadata') and result.metadata is None:
            result.metadata = {}
        if hasattr(result, 'metadata'):
            result.metadata['command_type'] = cmd_type
        
        print(f"Wykonano komendę {i+1}/{count}: {cmd_type}")
        time.sleep(interval)

def main():
    # Inicjalizacja runnera z włączonym cache
    runner = ShellRunner(
        backend_type="bash",
        enable_cache=True,
        cache_max_size=200,
        cache_auto_refresh=True,
        cache_refresh_interval=10
    )
    
    print("=== Demonstracja wizualizacji cache w ShellRunner ===\n")
    
    if VISUALIZATION_AVAILABLE:
        # Inicjalizacja wizualizatora
        visualizer = CacheVisualizer(runner, update_interval=1.0)
        
        # Uruchomienie wizualizacji w osobnym wątku
        visualizer.start()
        
        # Symulacja wykonania komend
        print("Symulacja wykonania komend...")
        simulate_commands(runner, count=30, interval=0.3)
        
        print("\nWizualizacja działa w osobnym oknie.")
        print("Naciśnij Ctrl+C, aby zakończyć.")
        
        try:
            # Czekamy na zamknięcie okna wizualizacji
            while visualizer.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nPrzerwano przez użytkownika.")
        finally:
            visualizer.stop()
    else:
        # Jeśli wizualizacja nie jest dostępna, po prostu symulujemy komendy
        print("Symulacja wykonania komend bez wizualizacji...")
        simulate_commands(runner, count=10, interval=0.5)
        
        # Wyświetlamy statystyki cache
        print("\nStatystyki cache:")
        stats = runner.get_cache_statistics()
        print(json.dumps(stats, indent=2))
        
        # Wyświetlamy historię komend
        print("\nHistoria wykonanych komend:")
        history = runner.get_command_history()
        for i, (cmd_id, timestamp, success) in enumerate(history):
            print(f"{i+1}. ID: {cmd_id[:8]}... | Czas: {timestamp} | Status: {'Sukces' if success else 'Błąd'}")

if __name__ == "__main__":
    main() 