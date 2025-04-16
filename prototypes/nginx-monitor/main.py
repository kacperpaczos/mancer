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
import select as select_module  # Zmiana nazwy importu
from textual.app import App
from textual.widgets import Header, Footer, Tree, Static, ScrollView
from textual.containers import Container, Horizontal
from textual.binding import Binding

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

    def getch():
        """Pomocnicza funkcja do odczytu pojedynczego znaku"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def create_layout(self):
        layout = Layout()
        layout.split_row(
            Layout(name="apps", ratio=1),
            Layout(name="logs", ratio=1),
            Layout(name="content", ratio=2)
        )
        return layout

    def watch_logs(self, log_path, remote=False, host=None, username=None, key_path=None):
        try:
            log_lines = []
            max_lines = 1000
            scroll_position = 0
            auto_scroll = True
            console = Console()
            layout = self.create_layout()

            # Przygotuj panele
            def generate_apps_panel():
                # Lista zainstalowanych aplikacji
                table = Table(title="Aplikacje")
                table.add_column("Nazwa")
                for app in self.profiles.keys():
                    table.add_row(app)
                return Panel(table, title="Aplikacje Nginx")

            def generate_logs_panel(selected_app):
                # Lista dostępnych logów
                table = Table(title="Logi")
                table.add_column("Typ")
                table.add_column("Ścieżka")
                # Dodaj dostępne logi
                return Panel(table, title=f"Logi - {selected_app}")

            def generate_content_panel():
                # Zawartość logów
                visible_lines = log_lines[-console.height:] if auto_scroll else log_lines[scroll_position:scroll_position + console.height]
                return Panel("\n".join(visible_lines), title="Zawartość logów")

            # Konfiguracja tail
            if remote:
                tail_cmd = f"tail -n 100 -f {log_path}"
                ssh_command = ['ssh']
                if key_path:
                    ssh_command.extend(['-i', key_path])
                ssh_command.append(f'{username}@{host}')
                ssh_command.append(f'sudo {tail_cmd}')
                process = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            else:
                tail_cmd = f"sudo tail -n 100 -f {log_path}"
                process = subprocess.Popen(tail_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            def update_layout():
                layout["apps"].update(generate_apps_panel())
                layout["logs"].update(generate_logs_panel("selected_app"))
                layout["content"].update(generate_content_panel())
                return layout

            with Live(update_layout(), auto_refresh=True, screen=True) as live:
                while True:
                    # Czytaj nową linię z tail
                    line = process.stdout.readline().strip()
                    if line:
                        formatted_line = self.format_and_display_log_line(line, log_path)
                        log_lines.append(formatted_line)
                        if len(log_lines) > max_lines:
                            log_lines.pop(0)
                    
                    # Sprawdź klawisze
                    if sys.stdin in select_module.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key == 'k':  # Scroll up
                            auto_scroll = False
                            scroll_position = max(0, scroll_position - 1)
                        elif key == 'j':  # Scroll down
                            auto_scroll = False
                            scroll_position += 1
                        elif key == 'a':  # Toggle auto-scroll
                            auto_scroll = not auto_scroll
                    
                    live.update(update_layout())

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Zatrzymano monitorowanie logów[/yellow]")
        finally:
            if process:
                process.terminate()

    def format_and_display_log_line(self, line, log_path):
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

    def run_monitor(self, logs, mode, host=None, username=None, key_path=None):
        app = NginxMonitorApp(self, logs, mode, host, username, key_path)
        app.run()

    def main(self):
        # ... (poprzedni kod bez zmian do momentu sprawdzenia statusu Nginx)

        # Wyświetl status Nginx
        self.display_results(results, host)

        # Jeśli Nginx działa, uruchom monitor
        if results['systemd_active']:
            self.console.print("\n[green]Nginx działa! Uruchamiam monitor...[/green]")
            
            logs = self.analyze_nginx_logs(
                remote=(mode == "z"),
                host=host if mode == "z" else None,
                username=username if mode == "z" else None,
                key_path=key_path if mode == "z" else None
            )
            
            try:
                self.run_monitor(logs, mode, host, username, key_path)
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Zatrzymano monitor[/yellow]")
        else:
            self.console.print("\n[red]Nginx nie jest aktywny![/red]")

class NginxMonitorApp(App):
    BINDINGS = [
        Binding("q", "quit", "Wyjście"),
        Binding("tab", "next_panel", "Następny panel"),
        Binding("shift+tab", "prev_panel", "Poprzedni panel"),
    ]

    def __init__(self, nginx_monitor, logs, mode, host=None, username=None, key_path=None):
        super().__init__()
        self.nginx_monitor = nginx_monitor
        self.logs = logs
        self.mode = mode
        self.host = host
        self.username = username
        self.key_path = key_path
        self.selected_app = None
        self.selected_log = None

    def compose(self):
        yield Header()
        yield Container(
            Horizontal(
                Tree("Aplikacje", id="apps_tree"),
                Tree("Logi", id="logs_tree"),
                ScrollView(Static(id="log_content")),
                id="main_container"
            )
        )
        yield Footer()

    def on_mount(self):
        # Wypełnij drzewo aplikacji
        apps_tree = self.query_one("#apps_tree", Tree)
        for app_name, app_data in self.logs.items():
            apps_tree.root.add(app_name)

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        tree_id = event.tree.id
        if tree_id == "apps_tree":
            self.selected_app = event.node.label
            # Aktualizuj drzewo logów
            logs_tree = self.query_one("#logs_tree", Tree)
            logs_tree.clear()
            if self.selected_app in self.logs:
                for log_type, paths in self.logs[self.selected_app]['logs'].items():
                    for path in paths:
                        logs_tree.root.add(path)
        elif tree_id == "logs_tree":
            self.selected_log = event.node.label
            # Rozpocznij monitorowanie wybranego logu
            self.monitor_log(self.selected_log)

    def monitor_log(self, log_path):
        # Konfiguracja procesu tail
        if self.mode == "z":
            tail_cmd = f"tail -n 100 -f {log_path}"
            ssh_command = ['ssh']
            if self.key_path:
                ssh_command.extend(['-i', self.key_path])
            ssh_command.append(f'{self.username}@{self.host}')
            ssh_command.append(f'sudo {tail_cmd}')
            process = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        else:
            tail_cmd = f"sudo tail -n 100 -f {log_path}"
            process = subprocess.Popen(tail_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        def update_log_content():
            content = self.query_one("#log_content", Static)
            while True:
                line = process.stdout.readline()
                if line:
                    formatted_line = self.nginx_monitor.format_and_display_log_line(line.strip(), log_path)
                    content.update(Text(formatted_line))
                if process.poll() is not None:
                    break

        # Uruchom wątek monitorujący
        import threading
        monitor_thread = threading.Thread(target=update_log_content, daemon=True)
        monitor_thread.start()

    def action_next_panel(self):
        # Implementacja przełączania między panelami
        pass

    def action_prev_panel(self):
        # Implementacja przełączania między panelami
        pass

def run_monitor(self, logs, mode, host=None, username=None, key_path=None):
    app = NginxMonitorApp(self, logs, mode, host, username, key_path)
    app.run()

if __name__ == "__main__":
    monitor = NginxMonitor()
    monitor.main()
