from mancer.application.shell_runner import ShellRunner

def main():
    # Inicjalizacja runnera
    runner = ShellRunner(backend_type="bash")
    
    # Przykład wykonania lokalnego
    print("=== Wykonanie lokalne ===")
    ls = runner.create_command("ls").long().all()
    result = runner.execute(ls)
    print("Wynik ls lokalnie:")
    print(result.raw_output)
    
    # Konfiguracja wykonania zdalnego z hasłem
    print("\n=== Konfiguracja wykonania zdalnego z hasłem ===")
    runner.set_remote_execution(
        host="example.com",      # Zmień na właściwy host
        user="username",         # Zmień na właściwą nazwę użytkownika
        password="password123",  # Zmień na właściwe hasło
        # port=22,               # Opcjonalnie, domyślnie 22
        # key_file="~/.ssh/id_rsa"  # Opcjonalnie, ścieżka do klucza
    )
    
    # Przykład wykonania zdalnego z hasłem
    print("\n=== Wykonanie zdalne z hasłem ===")
    remote_ls = runner.create_command("ls").long().all()
    try:
        remote_result = runner.execute(remote_ls)
        print("Wynik ls zdalnie:")
        print(remote_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego: {e}")
    
    # Konfiguracja wykonania zdalnego z sudo
    print("\n=== Konfiguracja wykonania zdalnego z sudo ===")
    runner.set_remote_execution(
        host="example.com",      # Zmień na właściwy host
        user="username",         # Zmień na właściwą nazwę użytkownika
        password="password123",  # Zmień na właściwe hasło
        use_sudo=True,           # Używaj sudo automatycznie, gdy potrzeba
        sudo_password="sudo_password123"  # Zmień na właściwe hasło sudo
    )
    
    # Przykład wykonania zdalnego z sudo
    print("\n=== Wykonanie zdalne z sudo ===")
    # Komenda, która wymaga uprawnień roota
    remote_apt = runner.create_command("apt").with_param("update", "")
    try:
        apt_result = runner.execute(remote_apt)
        print("Wynik apt update zdalnie z sudo:")
        print(apt_result.raw_output[:200] + "..." if len(apt_result.raw_output) > 200 else apt_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego z sudo: {e}")
    
    # Przykład jawnego oznaczenia komendy jako wymagającej sudo
    print("\n=== Wykonanie komendy jawnie oznaczonej jako wymagającej sudo ===")
    # Komenda, którą jawnie oznaczamy jako wymagającą sudo
    remote_service = runner.create_command("systemctl").with_param("status", "nginx").with_sudo()
    try:
        service_result = runner.execute(remote_service)
        print("Wynik systemctl status nginx zdalnie z sudo:")
        print(service_result.raw_output[:200] + "..." if len(service_result.raw_output) > 200 else service_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego z sudo: {e}")
    
    # Przykład automatycznego wykrycia potrzeby sudo
    print("\n=== Automatyczne wykrycie potrzeby sudo ===")
    # Konfiguracja z automatycznym sudo, ale bez jawnego oznaczenia komendy
    runner.set_remote_execution(
        host="example.com",      # Zmień na właściwy host
        user="username",         # Zmień na właściwą nazwę użytkownika
        password="password123",  # Zmień na właściwe hasło
        use_sudo=True,           # Używaj sudo automatycznie, gdy potrzeba
        sudo_password="sudo_password123"  # Zmień na właściwe hasło sudo
    )
    
    # Komenda, która może wymagać sudo, ale nie jest jawnie oznaczona
    remote_cat = runner.create_command("cat").with_param("path", "/var/log/syslog")
    try:
        cat_result = runner.execute(remote_cat)
        print("Wynik cat /var/log/syslog zdalnie (automatyczne sudo jeśli potrzeba):")
        print(cat_result.raw_output[:200] + "..." if len(cat_result.raw_output) > 200 else cat_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego: {e}")

if __name__ == "__main__":
    main() 