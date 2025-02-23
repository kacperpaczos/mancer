import os
import json
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
import threading
import queue
import time
import sys, tty, termios
from select import select

class NginxMonitor:
    def __init__(self):
        self.console = Console()
        self.profiles_file = os.path.expanduser("~/.nginx_monitor_profiles.json")
        self.profiles = self.load_profiles()

    def load_profiles(self):
        if os.path.exists(self.profiles_file):
            with open(self.profiles_file, 'r') as f:
                return json.load(f)
        return {}

    def save_profile(self, name, host, username, key_path=None):
        self.profiles[name] = {
            'host': host,
            'username': username,
            'key_path': key_path
        }
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f)

    def run_command(self, command, remote=False, host=None, username=None, key_path=None):
        try:
            if remote:
                ssh_command = ['ssh']
                if key_path:
                    ssh_command.extend(['-i', key_path])
                ssh_command.append(f'{username}@{host}')
                ssh_command.append(command)
                result = subprocess.run(ssh_command, capture_output=True, text=True)
            else:
                # Dodaj sudo dla lokalnych poleceń, które tego wymagają
                if command.startswith('sudo '):
                    cmd_parts = command.split()
                else:
                    cmd_parts = ['sudo'] + command.split()
                result = subprocess.run(cmd_parts, capture_output=True, text=True)
            return result.stdout.strip(), result.returncode
        except Exception as e:
            return None, 1

    def check_nginx(self, remote=False, host=None, username=None, key_path=None):
        results = {}
        
        # Dodaj sprawdzanie lokalizacji plików konfiguracyjnych
        nginx_conf_cmd = "find /etc/nginx -name '*.conf' -type f"
        output, code = self.run_command(nginx_conf_cmd, remote, host, username, key_path)
        results['config_files'] = output.split('\n') if output else []
        
        # Znajdź ścieżki do logów
        log_paths = set()
        for conf_file in results['config_files']:
            grep_cmd = f"grep -E 'access_log|error_log' {conf_file}"
            output, code = self.run_command(grep_cmd, remote, host, username, key_path)
            if output:
                for line in output.split('\n'):
                    if 'access_log' in line or 'error_log' in line:
                        parts = line.strip().split()
                        if len(parts) > 1:
                            log_path = parts[1]
                            if log_path != 'off' and not log_path.startswith('syslog:'):
                                log_paths.add(log_path)
        
        results['log_paths'] = list(log_paths)

        # Sprawdzanie jednostki systemd
        systemd_cmd = 'systemctl is-active nginx'
        output, code = self.run_command(systemd_cmd, remote, host, username, key_path)
        results['systemd_active'] = output == 'active' if output else False

        # Sprawdzanie procesu i portu
        netstat_cmd = "netstat -tulpn | grep ':80'"
        output, code = self.run_command(netstat_cmd, remote, host, username, key_path)
        
        # Domyślne wartości
        results['port_80_active'] = False
        results['port_80_process'] = None
        results['port_80_pid'] = None
        results['port_80_ipv4'] = None
        results['port_80_ipv6'] = None
        results['port_80_details'] = None

        if output:
            for line in output.split('\n'):
                # tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      37273/nginx: master 
                if ':80' in line:
                    results['port_80_active'] = True
                    parts = line.strip().split()
                    # Znajdź część z PID/procesem (ostatnia kolumna)
                    process_info = parts[-2]  # np. "37273/nginx: master"
                    if '/' in process_info:
                        pid, process = process_info.split('/', 1)
                        results['port_80_pid'] = pid
                        results['port_80_process'] = process.strip()

                    # Znajdź adres IP (czwarta kolumna)
                    local_addr = parts[3]  # np. "0.0.0.0:80" lub ":::80"
                    if parts[0] == 'tcp':
                        results['port_80_ipv4'] = local_addr
                    elif parts[0] == 'tcp6':
                        results['port_80_ipv6'] = local_addr

                    if results['port_80_pid']:
                        ps_cmd = f'ps -p {results["port_80_pid"]} -o comm,args'
                        ps_output, _ = self.run_command(ps_cmd, remote, host, username, key_path)
                        if ps_output:
                            results['port_80_details'] = ps_output.split('\n')[-1]
                    break  # Weź pierwszy znaleziony wpis dla portu 80

        # Sprawdzanie wersji nginx
        nginx_cmd = 'nginx -v 2>&1'
        output, code = self.run_command(nginx_cmd, remote, host, username, key_path)
        results['version'] = output if output else "Nie znaleziono"
        
        return results

    def display_results(self, results, location):
        table = Table(title=f"Status Nginx na {location}")
        table.add_column("Sprawdzenie", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row(
            "Jednostka systemd",
            "✓ Aktywna" if results['systemd_active'] else "✗ Nieaktywna"
        )
        
        if results['port_80_active']:
            port_info = []
            if results['port_80_process']:
                port_info.append(f"Program: {results['port_80_process']}")
            if results['port_80_pid']:
                port_info.append(f"PID: {results['port_80_pid']}")
            if results['port_80_ipv4']:
                port_info.append(f"IPv4: {results['port_80_ipv4']}")
            if results['port_80_ipv6']:
                port_info.append(f"IPv6: {results['port_80_ipv6']}")
            if results['port_80_details']:
                port_info.append(f"Szczegóły: {results['port_80_details']}")
                
            port_status = "\n".join(port_info)
            if 'nginx' in str(results['port_80_process']).lower():
                table.add_row("Port 80", f"✓ Nasłuchuje (nginx)\n{port_status}")
            else:
                table.add_row("Port 80", f"⚠ Zajęty przez inny proces\n{port_status}")
        else:
            table.add_row("Port 80", "✗ Nie nasłuchuje")
            
        table.add_row("Wersja Nginx", results['version'])
        
        # Dodaj sekcję z informacjami o logach
        if results.get('config_files'):
            self.console.print("\nZnalezione pliki konfiguracyjne:")
            for conf in results['config_files']:
                self.console.print(f"  • {conf}")
            
        if results.get('log_paths'):
            self.console.print("\nŚcieżki do logów:")
            for log_path in results['log_paths']:
                self.console.print(f"  • {log_path}")
        
        self.console.print(table)

    def watch_logs(self, log_path, remote=False, host=None, username=None, key_path=None):
        try:
            # Inicjalizacja kolejki i listy logów
            log_queue = queue.Queue()
            log_lines = []
            max_lines = 1000
            scroll_position = 0
            console = Console()

            def read_logs():
                if remote:
                    tail_cmd = f"tail -f {log_path}"
                    ssh_command = ['ssh']
                    if key_path:
                        ssh_command.extend(['-i', key_path])
                    ssh_command.append(f'{username}@{host}')
                    ssh_command.append(f'sudo {tail_cmd}')
                    process = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                else:
                    tail_cmd = f"sudo tail -f {log_path}"
                    process = subprocess.Popen(tail_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

                try:
                    while True:
                        line = process.stdout.readline()
                        if line:
                            log_queue.put(line.strip())
                        if process.poll() is not None:
                            break
                finally:
                    process.terminate()

            # Uruchom wątek czytający logi
            log_thread = threading.Thread(target=read_logs, daemon=True)
            log_thread.start()

            def generate_output():
                nonlocal scroll_position
                
                # Pobierz nowe logi z kolejki
                while not log_queue.empty():
                    new_line = log_queue.get()
                    formatted_line = self.format_and_display_log_line(new_line)
                    log_lines.append(formatted_line)
                    if len(log_lines) > max_lines:
                        log_lines.pop(0)

                # Oblicz widoczny zakres
                console_height = console.height - 4  # Wysokość konsoli minus marginesy
                total_lines = len(log_lines)
                
                # Upewnij się, że scroll_position jest w prawidłowym zakresie
                max_scroll = max(0, total_lines - console_height)
                scroll_position = min(max_scroll, max(0, scroll_position))

                # Przygotuj tekst do wyświetlenia
                visible_lines = log_lines[scroll_position:scroll_position + console_height]
                text = Text("\n").join([Text(line) for line in visible_lines])
                
                return Panel(
                    text,
                    title=f"[bold blue]Log Monitor[/bold blue]",
                    subtitle=f"[dim]Linie {scroll_position + 1}-{min(scroll_position + console_height, total_lines)} z {total_lines} (↑/↓ do scrollowania)[/dim]",
                    border_style="blue"
                )

            self.console.print(f"\n[bold green]Rozpoczynam monitorowanie logów z {log_path}[/bold green]")
            self.console.print("[dim]Użyj strzałek ↑/↓ do scrollowania. Ctrl+C aby zakończyć...[/dim]\n")

            with Live(generate_output(), auto_refresh=False, screen=True) as live:
                while True:
                    # Obsługa klawiszy
                    if sys.stdin in select([sys.stdin], [], [], 0)[0]:
                        char = getch()
                        if char == '\x1b':  # Escape sequence
                            char = getch()
                            if char == '[':
                                char = getch()
                                if char == 'A':  # Strzałka w górę
                                    scroll_position = max(0, scroll_position - 1)
                                elif char == 'B':  # Strzałka w dół
                                    scroll_position += 1

                    live.update(generate_output())
                    time.sleep(0.1)  # Zmniejsz obciążenie CPU

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Zatrzymano monitorowanie logów[/yellow]")

    def format_and_display_log_line(self, line):
        """Pomocnicza funkcja do formatowania linii logu"""
        try:
            # Dla access.log
            if 'access.log' in log_path:
                # Kolorowanie różnych typów requestów
                if 'GET' in line:
                    line = line.replace('GET', '[green]GET[/green]')
                elif 'POST' in line:
                    line = line.replace('POST', '[blue]POST[/blue]')
                elif 'DELETE' in line:
                    line = line.replace('DELETE', '[red]DELETE[/red]')
                
                # Kolorowanie kodów odpowiedzi
                for status_code in ['200', '201', '204']:
                    line = line.replace(f' {status_code} ', f' [green]{status_code}[/green] ')
                for status_code in ['404', '400', '401', '403']:
                    line = line.replace(f' {status_code} ', f' [yellow]{status_code}[/yellow] ')
                for status_code in ['500', '502', '503', '504']:
                    line = line.replace(f' {status_code} ', f' [red]{status_code}[/red] ')
            
            # Dla error.log
            elif 'error.log' in log_path:
                if 'error' in line.lower():
                    line = f'[red]{line}[/red]'
                elif 'warn' in line.lower():
                    line = f'[yellow]{line}[/yellow]'
                else:
                    line = f'[blue]{line}[/blue]'
        except:
            pass
        
        return line

    def analyze_nginx_logs(self, remote=False, host=None, username=None, key_path=None):
        """Analizuje wszystkie logi NGINX"""
        logs = {
            'default': {
                'name': 'Domyślne logi NGINX',
                'logs': {
                    'access': ['/var/log/nginx/access.log'],
                    'error': ['/var/log/nginx/error.log']
                }
            }
        }
        
        # Sprawdź standardowe lokalizacje konfiguracji
        config_locations = [
            "/etc/nginx/sites-enabled/",
            "/etc/nginx/conf.d/"
        ]
        
        for location in config_locations:
            ls_cmd = f"ls -1 {location} 2>/dev/null"
            output, code = self.run_command(ls_cmd, remote, host, username, key_path)
            
            if output:
                self.console.print(f"\nZnaleziono konfiguracje w {location}:")
                for site in output.split('\n'):
                    if site and (site.endswith('.conf') or not '.' in site):
                        app_info = {'name': site, 'logs': {'access': [], 'error': []}}
                        
                        cat_cmd = f"cat {location}{site}"
                        conf_output, _ = self.run_command(cat_cmd, remote, host, username, key_path)
                        
                        if conf_output:
                            for line in conf_output.split('\n'):
                                line = line.strip()
                                if 'access_log' in line:
                                    parts = line.split()
                                    if len(parts) > 1 and parts[1] != 'off':
                                        app_info['logs']['access'].append(parts[1])
                                elif 'error_log' in line:
                                    parts = line.split()
                                    if len(parts) > 1 and parts[1] != 'off':
                                        app_info['logs']['error'].append(parts[1])
                        
                        if app_info['logs']['access'] or app_info['logs']['error']:
                            logs[site] = app_info

        return logs

    def display_logs(self, logs):
        """Wyświetla informacje o wszystkich znalezionych logach"""
        if not logs:
            self.console.print("\n[yellow]Nie znaleziono żadnych logów[/yellow]")
            return

        table = Table(title="Dostępne logi NGINX")
        table.add_column("Nazwa", style="cyan")
        table.add_column("Access Logi", style="green")
        table.add_column("Error Logi", style="red")

        for name, info in logs.items():
            access_logs = "\n".join(info['logs']['access']) or "Brak"
            error_logs = "\n".join(info['logs']['error']) or "Brak"
            table.add_row(name, access_logs, error_logs)

        self.console.print(table)

    def main(self):
        self.console.print(Panel.fit("Monitor Nginx", style="bold blue"))
        
        mode = Prompt.ask("Wybierz tryb (l/z)", choices=["l", "z"])
        
        if mode == "l":
            results = self.check_nginx()
            self.display_results(results, "localhost")
            
            self.console.print("\n=== Analiza logów NGINX ===")
            
            # Analiza logów
            logs = self.analyze_nginx_logs()
            if logs:
                self.display_logs(logs)
                
                # Opcja monitorowania logów
                if Confirm.ask("\nCzy chcesz monitorować logi?"):
                    available_logs = []
                    for name, info in logs.items():
                        for log_type, log_paths in info['logs'].items():
                            for log_path in log_paths:
                                available_logs.append((name, log_type, log_path))
                    
                    if available_logs:
                        self.console.print("\nDostępne logi:")
                        for i, (name, log_type, log_path) in enumerate(available_logs, 1):
                            self.console.print(f"{i}. {name} ({log_type}): {log_path}")
                        
                        choice = int(Prompt.ask(
                            "Wybierz numer logu do monitorowania",
                            choices=[str(i) for i in range(1, len(available_logs) + 1)]
                        ))
                        
                        selected_name, log_type, log_path = available_logs[choice - 1]
                        self.console.print(f"\nMonitorowanie logów {log_type} dla {selected_name}")
                        
                        # Sprawdź czy plik istnieje przed monitorowaniem
                        check_cmd = f"test -f {log_path} && echo 'exists'"
                        print(check_cmd)
                        _, exists = self.run_command(check_cmd)
                        print(exists)
                        
                        if exists:
                            self.watch_logs(log_path)
                        else:
                            self.console.print(f"[red]Plik logu {log_path} nie istnieje![/red]")
                    else:
                        self.console.print("[yellow]Nie znaleziono żadnych dostępnych logów[/yellow]")
            else:
                self.console.print("[yellow]Nie znaleziono żadnych logów[/yellow]")
        
        else:
            if self.profiles and Confirm.ask("Czy chcesz użyć zapisanego profilu?"):
                profile_names = list(self.profiles.keys())
                profile_name = Prompt.ask("Wybierz profil", choices=profile_names)
                profile = self.profiles[profile_name]
                results = self.check_nginx(
                    remote=True,
                    host=profile['host'],
                    username=profile['username'],
                    key_path=profile['key_path']
                )
            else:
                host = Prompt.ask("Podaj host")
                username = Prompt.ask("Podaj nazwę użytkownika")
                use_key = Confirm.ask("Czy chcesz użyć klucza SSH?")
                key_path = None
                
                if use_key:
                    key_path = Prompt.ask("Podaj ścieżkę do klucza SSH")
                
                results = self.check_nginx(
                    remote=True,
                    host=host,
                    username=username,
                    key_path=key_path
                )
                
                if Confirm.ask("Czy chcesz zapisać ten profil?"):
                    name = Prompt.ask("Podaj nazwę profilu")
                    self.save_profile(name, host, username, key_path)
            
            if results:
                self.display_results(results, host)
                
                # Analiza logów
                logs = self.analyze_nginx_logs(
                    remote=(mode == "z"),
                    host=host if mode == "z" else None,
                    username=username if mode == "z" else None,
                    key_path=key_path if mode == "z" else None
                )
                self.display_logs(logs)
                
                # Opcja monitorowania logów
                if logs:
                    if Confirm.ask("\nCzy chcesz monitorować logi?"):
                        # Przygotuj listę wszystkich dostępnych logów
                        available_logs = []
                        for name, info in logs.items():
                            for log_type, log_paths in info['logs'].items():
                                for log_path in log_paths:
                                    available_logs.append((name, log_type, log_path))
                        
                        if available_logs:
                            self.console.print("\nDostępne logi:")
                            for i, (name, log_type, log_path) in enumerate(available_logs, 1):
                                self.console.print(f"{i}. {name} ({log_type}): {log_path}")
                            
                            choice = int(Prompt.ask(
                                "Wybierz numer logu do monitorowania",
                                choices=[str(i) for i in range(1, len(available_logs) + 1)]
                            ))
                            
                            selected_name, log_type, log_path = available_logs[choice - 1]
                            self.console.print(f"\nMonitorowanie logów {log_type} dla {selected_name}")
                            
                            # Sprawdź czy plik istnieje przed monitorowaniem
                            check_cmd = f"test -f {log_path} && echo 'exists'"
                            exists, _ = self.run_command(check_cmd)
                            
                            if exists:
                                self.watch_logs(
                                    log_path,
                                    remote=(mode == "z"),
                                    host=host if mode == "z" else None,
                                    username=username if mode == "z" else None,
                                    key_path=key_path if mode == "z" else None
                                )
                            else:
                                self.console.print(f"[red]Plik logu {log_path} nie istnieje![/red]")
                        else:
                            self.console.print("[yellow]Nie znaleziono żadnych dostępnych logów[/yellow]")

if __name__ == "__main__":
    monitor = NginxMonitor()
    monitor.main()
