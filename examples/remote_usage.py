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
    
    # Konfiguracja wykonania zdalnego
    # Uwaga: Podaj właściwe dane do połączenia SSH
    print("\n=== Konfiguracja wykonania zdalnego ===")
    runner.set_remote_execution(
        host="example.com",  # Zmień na właściwy host
        user="username",     # Zmień na właściwą nazwę użytkownika
        # port=22,           # Opcjonalnie, domyślnie 22
        # key_file="~/.ssh/id_rsa"  # Opcjonalnie, ścieżka do klucza
    )
    
    # Przykład wykonania zdalnego
    print("\n=== Wykonanie zdalne ===")
    remote_ls = runner.create_command("ls").long().all()
    try:
        remote_result = runner.execute(remote_ls)
        print("Wynik ls zdalnie:")
        print(remote_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego: {e}")
    
    # Przykład łańcucha komend zdalnych
    print("\n=== Łańcuch komend zdalnych ===")
    cd = runner.create_command("cd").to_directory("/tmp")
    find = runner.create_command("find").with_name("*.log")
    
    try:
        chain_result = runner.execute(cd.then(find))
        print("Wynik cd /tmp | find -name \"*.log\" zdalnie:")
        print(chain_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania łańcucha zdalnego: {e}")
    
    # Przełączenie z powrotem na wykonanie lokalne
    print("\n=== Przełączenie na wykonanie lokalne ===")
    runner.set_local_execution()
    
    local_result = runner.execute(ls)
    print("Wynik ls lokalnie po przełączeniu:")
    print(local_result.raw_output)
    
    # Przykład mieszanego wykonania - niektóre komendy lokalne, niektóre zdalne
    print("\n=== Mieszane wykonanie (lokalne/zdalne) ===")
    print("Wykonanie lokalne:")
    local_ps = runner.create_command("ps").all()
    local_ps_result = runner.execute(local_ps)
    print(local_ps_result.raw_output[:200] + "..." if len(local_ps_result.raw_output) > 200 else local_ps_result.raw_output)
    
    print("\nPrzełączenie na zdalne:")
    runner.set_remote_execution(
        host="example.com",  # Zmień na właściwy host
        user="username"      # Zmień na właściwą nazwę użytkownika
    )
    
    try:
        remote_ps = runner.create_command("ps").all()
        remote_ps_result = runner.execute(remote_ps)
        print(remote_ps_result.raw_output[:200] + "..." if len(remote_ps_result.raw_output) > 200 else remote_ps_result.raw_output)
    except Exception as e:
        print(f"Błąd wykonania zdalnego: {e}")

if __name__ == "__main__":
    main() 