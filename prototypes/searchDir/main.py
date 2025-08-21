import json
import os
import subprocess
from datetime import datetime

CONFIG_FILE = "ssh_config.json"
HISTORY_FILE = "ssh_history.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(history_entry):
    history = load_history()
    history.append(history_entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


def ssh_search_and_scp(remote_user, remote_host, password):
    # Używamy SSHPASS dla automatycznego podawania hasła
    os.environ["SSHPASS"] = password

    # Najpierw sprawdzamy połączenie SSH i hasło
    test_connection = (
        f"sshpass -e ssh -o StrictHostKeyChecking=no {remote_user}@{remote_host} 'echo test'"
    )
    try:
        subprocess.run(test_connection, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Błąd połączenia SSH. Sprawdź dane logowania.")
        return

    # Używamy bieżącego katalogu jako miejsca docelowego
    local_path = os.getcwd()

    # Komenda do wyszukania folderów na zdalnym hoście
    find_command = f"sshpass -e ssh {remote_user}@{remote_host} 'find / -type d 2>/dev/null | grep -i \"{folder_name}\"'"

    try:
        # Wykonanie komendy find przez SSH
        result = subprocess.run(
            find_command, shell=True, capture_output=True, text=True, check=True
        )
        paths = [path for path in result.stdout.strip().split("\n") if path]

        if not paths:
            print("Nie znaleziono żadnych pasujących folderów.")
            return

        # Lista do przechowywania znalezionych ścieżek
        found_paths = []
        downloaded_paths = []

        for path in paths:
            print(f"Znaleziono: {path}")
            found_paths.append(path)

        # Pytanie o pobranie po wyświetleniu wszystkich znalezionych folderów
        print("\nZnalezione foldery:")
        for i, path in enumerate(found_paths, 1):
            print(f"{i}. {path}")

        while True:
            choice = (
                input("\nKtóry folder chcesz pobrać? (podaj numer lub 'q' aby zakończyć): ")
                .strip()
                .lower()
            )
            if choice == "q":
                break
            try:
                index = int(choice) - 1
                if 0 <= index < len(found_paths):
                    # Pobranie wybranego folderu przez SCP
                    selected_path = found_paths[index]
                    scp_command = f'sshpass -e scp -r {remote_user}@{remote_host}:"{selected_path}" "{local_path}"'
                    try:
                        subprocess.run(scp_command, shell=True, check=True)
                        print(f"Folder pobrany do: {local_path}")
                        downloaded_paths.append(selected_path)
                    except subprocess.CalledProcessError as e:
                        print(f"Błąd podczas pobierania folderu: {e}")
                else:
                    print("Nieprawidłowy numer folderu.")
            except ValueError:
                print("Proszę podać prawidłowy numer lub 'q'.")

        # Zapisz historię wyszukiwania i pobierania
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "remote_user": remote_user,
            "remote_host": remote_host,
            "search_term": folder_name,
            "found_paths": found_paths,
            "downloaded_paths": downloaded_paths,
        }
        save_history(history_entry)

    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas wyszukiwania: {e}")


def show_history():
    history = load_history()
    if not history:
        print("Brak historii wyszukiwań.")
        return None

    print("\nOstatnie wyszukiwania:")
    for i, entry in enumerate(history, 1):
        print(f"\n{i}. Data: {entry['timestamp']}")
        print(f"   Host: {entry['remote_user']}@{entry['remote_host']}")
        print(f"   Szukana fraza: {entry['search_term']}")
        print(f"   Pobrane foldery: {len(entry['downloaded_paths'])}")

    choice = input("\nWybierz numer wyszukiwania do powtórzenia (lub Enter aby pominąć): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(history):
        return history[int(choice) - 1]
    return None


if __name__ == "__main__":
    # Sprawdź czy istnieją zapisane dane logowania
    config = load_config()
    if (
        config
        and input("Czy chcesz użyć zapisanych danych logowania? (t/n): ").lower().strip() == "t"
    ):
        remote_user = config["remote_user"]
        remote_host = config["remote_host"]
        password = config["password"]
        print(f"Używam zapisanych danych: {remote_user}@{remote_host}")
    else:
        remote_user = input("Podaj nazwę użytkownika zdalnego hosta: ").strip()
        remote_host = input("Podaj adres zdalnego hosta: ").strip()
        password = input("Podaj hasło SSH: ").strip()
        if input("Czy zapisać dane logowania? (t/n): ").lower().strip() == "t":
            save_config(
                {
                    "remote_user": remote_user,
                    "remote_host": remote_host,
                    "password": password,
                }
            )

    # Sprawdź historię
    last_search = show_history()
    if (
        last_search
        and input("Czy chcesz powtórzyć ostatnie wyszukiwanie? (t/n): ").lower().strip() == "t"
    ):
        folder_name = last_search["search_term"]
    else:
        folder_name = input("Podaj nazwę folderu do wyszukania: ").strip()

    print("\nSprawdzam połączenie SSH...")
    print(f"Pliki zostaną pobrane do bieżącego katalogu: {os.getcwd()}")

    ssh_search_and_scp(remote_user, remote_host, password)
