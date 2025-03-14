from mancer.application.shell_runner import ShellRunner

def main():
    # Inicjalizacja runnera
    runner = ShellRunner(backend_type="bash")
    
    # Tworzenie komend
    ls = runner.create_command("ls").long().all()
    cd = runner.create_command("cd").to_directory("/tmp")
    cp = runner.create_command("cp").recursive().from_source("*.conf").to_destination("/backup")
    
    # Rejestracja prekonfigurowanych komend
    runner.register_command("ls_all", ls)
    runner.register_command("cd_tmp", cd)
    runner.register_command("backup", cp)
    
    # Użycie pojedynczej komendy
    result = runner.execute(ls)
    print("Wynik ls:")
    print(result)
    
    # Użycie łańcucha komend: cd /tmp, ls -la
    chain = cd.then(ls)
    result = runner.execute(chain)
    print("\nWynik cd /tmp | ls -la:")
    print(result)
    
    # Użycie łańcucha z zapisanymi komendami
    chain = runner.get_command("cd_tmp").then(runner.get_command("ls_all"))
    result = runner.execute(chain)
    print("\nWynik z zapisanych komend:")
    print(result)
    
    # Przykład pełnego łańcucha: cd /etc, znajdź pliki .conf, skopiuj je do /backup
    # Używamy exec_command, aby bezpośrednio wykonać cp dla każdego znalezionego pliku
    find = runner.create_command("find").with_name("*.conf").exec_command("cp -r {} /backup")
    
    complex_chain = (
        runner.create_command("cd").to_directory("/etc")
            .then(find)
    )
    
    print("\nUruchamianie złożonego łańcucha komend:")
    result = runner.execute(complex_chain)
    print(f"Status: {'Sukces' if result.is_success() else 'Błąd'}")
    if not result.is_success():
        print(f"Błąd: {result.error_message}")

if __name__ == "__main__":
    main()
