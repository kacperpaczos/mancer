#!/usr/bin/env python3
"""
Przykład użycia różnych metod uwierzytelniania SSH w bibliotece mancer.
"""

from mancer.application.shell_runner import ShellRunner
from mancer.domain.model.command_result import CommandResult

def print_auth_example(title: str, result: CommandResult):
    """Wyświetla wynik przykładu uwierzytelniania"""
    print(f"{title}")
    if result.is_success():
        print(f"Wynik: {result.raw_output}")
    else:
        print(f"Błąd: {result.error_message}")

def main():
    # Inicjalizacja runnera
    runner = ShellRunner(backend_type="bash")
    
    print("=== Przykłady różnych metod uwierzytelniania SSH ===\n")
    
    # Tworzymy komendę hostname do testów
    hostname_cmd = runner.create_command("hostname")
    
    # 1. Uwierzytelnianie za pomocą hasła
    print("1. Uwierzytelnianie za pomocą hasła")
    # Symulujemy połączenie SSH - w rzeczywistości wykonujemy lokalnie
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        password="password123",
    )
    
    try:
        # Przykładowa komenda
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 2. Uwierzytelnianie za pomocą klucza prywatnego
    print("\n2. Uwierzytelnianie za pomocą klucza prywatnego")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        key_file="~/.ssh/id_rsa",
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 3. Uwierzytelnianie za pomocą agenta SSH
    print("\n3. Uwierzytelnianie za pomocą agenta SSH")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        use_agent=True,
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 4. Uwierzytelnianie za pomocą certyfikatu SSH
    print("\n4. Uwierzytelnianie za pomocą certyfikatu SSH")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        certificate_file="~/.ssh/id_rsa-cert.pub",
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 5. Uwierzytelnianie GSSAPI (Kerberos)
    print("\n5. Uwierzytelnianie GSSAPI (Kerberos)")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        gssapi_auth=True,
        gssapi_delegate_creds=True,
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 6. Uwierzytelnianie z niestandardowymi opcjami SSH
    print("\n6. Uwierzytelnianie z niestandardowymi opcjami SSH")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        ssh_options={
            "PubkeyAuthentication": "yes",
            "PreferredAuthentications": "publickey,password",
            "ConnectTimeout": "10",
            "ServerAliveInterval": "60",
            "ServerAliveCountMax": "3",
        }
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # 7. Kombinacja różnych metod uwierzytelniania
    print("\n7. Kombinacja różnych metod uwierzytelniania")
    runner.set_remote_execution(
        host="localhost",
        user="testuser",
        key_file="~/.ssh/id_rsa",
        use_agent=True,
        identity_only=True,
        ssh_options={
            "PreferredAuthentications": "publickey",
            "ConnectTimeout": "5",
        }
    )
    
    try:
        result = runner.execute(hostname_cmd)
        print_auth_example("Wynik:", result)
    except Exception as e:
        print(f"Błąd: {e}")
    
    # Przywracamy tryb lokalny
    runner.set_local_execution()
    print("\n8. Wykonanie lokalne (bez SSH)")
    result = runner.execute(hostname_cmd)
    print_auth_example("Wynik:", result)

if __name__ == "__main__":
    main() 