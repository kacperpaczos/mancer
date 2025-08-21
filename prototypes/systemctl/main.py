import base64
import concurrent.futures
import getpass
import json
import os
import subprocess
from datetime import datetime

from cryptography.fernet import Fernet


def get_encryption_key():
    # Używamy stałego klucza dla uproszczenia (w produkcji należy użyć bezpieczniejszego rozwiązania)
    key = b"TluxwB3fV_GWuLkR1_BzGs1Zk90TYAuhNMZP_0q4WyM="
    return base64.urlsafe_b64decode(key)


def encrypt_password(password):
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(password.encode()).decode()
    except Exception as e:
        print(f"Błąd szyfrowania hasła: {str(e)}")
        return None


def decrypt_password(encrypted_password):
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"Błąd deszyfrowania hasła: {str(e)}")
        return None


def get_systemd_units(server_info):
    hostname = server_info["hostname"]
    username = server_info["username"]
    password = server_info["password"]

    try:
        # Tworzymy unikalną nazwę pliku tymczasowego
        temp_filename = (
            f"systemd_units_temp_{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        remote_temp_file = f"/tmp/{temp_filename}"

        # Polecenie do pobrania wszystkich jednostek i zapisania do pliku
        systemctl_cmd = f"systemctl list-units --all --no-pager > {remote_temp_file}"

        # Wykonaj polecenie na zdalnym serwerze
        if password:
            ssh_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} '{systemctl_cmd}'"
        else:
            ssh_cmd = f"ssh {username}@{hostname} '{systemctl_cmd}'"

        # Wykonaj polecenie SSH
        subprocess.run(ssh_cmd, shell=True, check=True)

        # Skopiuj plik ze zdalnego serwera
        if password:
            scp_cmd = f"sshpass -p '{password}' scp {username}@{hostname}:{remote_temp_file} ./{temp_filename}"
        else:
            scp_cmd = f"scp {username}@{hostname}:{remote_temp_file} ./{temp_filename}"

        subprocess.run(scp_cmd, shell=True, check=True)

        # Usuń plik tymczasowy na zdalnym serwerze
        if password:
            cleanup_cmd = (
                f"sshpass -p '{password}' ssh {username}@{hostname} 'rm {remote_temp_file}'"
            )
        else:
            cleanup_cmd = f"ssh {username}@{hostname} 'rm {remote_temp_file}'"

        subprocess.run(cleanup_cmd, shell=True, check=True)

        # Odczytaj zawartość pliku lokalnego
        with open(temp_filename, "r", encoding="utf-8") as f:
            content = f.read()

        # Usuń lokalny plik tymczasowy
        os.remove(temp_filename)

        return {"hostname": hostname, "content": content, "status": "success"}

    except subprocess.CalledProcessError as e:
        print(f"Błąd wykonania polecenia dla {hostname}: {e}")
        return {
            "hostname": hostname,
            "content": None,
            "status": "error",
            "error": f"Błąd wykonania polecenia: {e}",
        }
    except Exception as e:
        print(f"Wystąpił błąd dla {hostname}: {str(e)}")
        return {
            "hostname": hostname,
            "content": None,
            "status": "error",
            "error": f"Wystąpił błąd: {str(e)}",
        }


def manage_systemd_service(server_info, service_name, action):
    hostname = server_info["hostname"]
    username = server_info["username"]
    password = server_info["password"]

    valid_actions = ["start", "stop", "restart", "status", "enable", "disable"]
    if action not in valid_actions:
        return {
            "hostname": hostname,
            "status": "error",
            "error": f"Nieprawidłowa akcja: {action}. Dostępne: {', '.join(valid_actions)}",
        }

    try:
        # Polecenie do zarządzania usługą
        systemctl_cmd = f"systemctl {action} {service_name}"

        # Wykonaj polecenie na zdalnym serwerze
        if password:
            ssh_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} '{systemctl_cmd}'"
        else:
            ssh_cmd = f"ssh {username}@{hostname} '{systemctl_cmd}'"

        # Wykonaj polecenie SSH i pobierz wynik
        result = subprocess.run(ssh_cmd, shell=True, check=True, capture_output=True, text=True)

        return {
            "hostname": hostname,
            "service": service_name,
            "action": action,
            "output": result.stdout,
            "status": "success",
        }

    except subprocess.CalledProcessError as e:
        return {
            "hostname": hostname,
            "service": service_name,
            "action": action,
            "status": "error",
            "error": f"Błąd wykonania polecenia: {e}",
            "output": e.stdout if hasattr(e, "stdout") else "",
        }
    except Exception as e:
        return {
            "hostname": hostname,
            "service": service_name,
            "action": action,
            "status": "error",
            "error": f"Wystąpił błąd: {str(e)}",
        }


def parse_units(units_output):
    units = {
        "summary": {"total": 0, "active": 0, "inactive": 0, "failed": 0},
        "by_type": {
            "service": [],
            "socket": [],
            "target": [],
            "path": [],
            "timer": [],
            "mount": [],
            "other": [],
        },
        "by_state": {"active": [], "inactive": [], "failed": [], "other": []},
        "dimark": {},  # Kategorie dimark według wzorca nazwy
        "user": [],
    }

    if not units_output:
        return units

    lines = units_output.split("\n")
    parsing_units = False

    for line in lines:
        # Pomijamy puste linie i nagłówki
        if not line.strip() or "UNIT" in line and "LOAD" in line and "ACTIVE" in line:
            continue

        # Sprawdzamy czy linia zawiera informacje o jednostce
        if "●" in line or ("." in line and not line.startswith("To show")):
            parsing_units = True
            parts = line.split()
            if len(parts) < 3:
                continue

            # Pobierz nazwę jednostki (pierwszy element zawierający kropkę)
            unit_name = next((part for part in parts if "." in part), "")
            if not unit_name:
                continue

            # Pobierz stan (active, inactive, failed)
            status = next(
                (part for part in parts if part.lower() in ["active", "inactive", "failed"]),
                "other",
            )

            unit_info = f"{unit_name} - {status}"

            # Aktualizuj statystyki
            units["summary"]["total"] += 1
            units["summary"][
                status if status in ["active", "inactive", "failed"] else "inactive"
            ] += 1

            # Kategoryzuj według typu
            unit_type = unit_name.split(".")[-1] if "." in unit_name else "other"
            if unit_type in units["by_type"]:
                units["by_type"][unit_type].append(unit_info)
            else:
                units["by_type"]["other"].append(unit_info)

            # Kategoryzuj według stanu
            if status in units["by_state"]:
                units["by_state"][status].append(unit_info)
            else:
                units["by_state"]["other"].append(unit_info)

            # Sprawdź czy to jednostka dimark i kategoryzuj według nazwy
            if "dimark_" in unit_name.lower():
                # Wyodrębnij nazwę kategorii z nazwy jednostki
                parts = unit_name.lower().split("dimark_")
                if len(parts) > 1:
                    category = parts[1].split("_")[0] if "_" in parts[1] else parts[1].split(".")[0]
                    if category not in units["dimark"]:
                        units["dimark"][category] = []
                    units["dimark"][category].append(unit_info)

            # Sprawdź czy to jednostka użytkownika
            if "@" in unit_name or "user" in unit_name:
                units["user"].append(unit_info)

        # Zakończ parsowanie gdy napotkamy podsumowanie
        elif "loaded units listed" in line.lower():
            break

    return units


def save_report(hostname, units):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"systemd_units_report_{hostname}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Raport jednostek systemd dla {hostname}\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

        # Podsumowanie
        f.write("PODSUMOWANIE:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Całkowita liczba jednostek: {units['summary']['total']}\n")
        f.write(f"Aktywne: {units['summary']['active']}\n")
        f.write(f"Nieaktywne: {units['summary']['inactive']}\n")
        f.write(f"Uszkodzone: {units['summary']['failed']}\n\n")

        # Sekcja jednostek Dimark
        f.write("JEDNOSTKI DIMARK:\n")
        f.write("-" * 20 + "\n")
        if units["dimark"]:
            for category, services in units["dimark"].items():
                f.write(f"\nKategoria {category.upper()}:\n")
                for unit in services:
                    f.write(f"{unit}\n")
        else:
            f.write("Brak jednostek dimark\n")
        f.write("\n")

        # Sekcja jednostek użytkownika
        f.write("JEDNOSTKI UŻYTKOWNIKA:\n")
        f.write("-" * 20 + "\n")
        if units["user"]:
            for unit in units["user"]:
                f.write(f"{unit}\n")
        else:
            f.write("Brak jednostek użytkownika\n")
        f.write("\n")

        # Sekcje według typu
        f.write("PODZIAŁ WEDŁUG TYPU:\n")
        f.write("-" * 20 + "\n")
        for unit_type, units_list in units["by_type"].items():
            if units_list:  # Pokazuj tylko typy, które mają jakieś jednostki
                f.write(f"\n{unit_type.upper()}:\n")
                for unit in units_list:
                    f.write(f"{unit}\n")
        f.write("\n")

        # Sekcje według stanu
        f.write("PODZIAŁ WEDŁUG STANU:\n")
        f.write("-" * 20 + "\n")
        for state, units_list in units["by_state"].items():
            if units_list:  # Pokazuj tylko stany, które mają jakieś jednostki
                f.write(f"\n{state.upper()}:\n")
                for unit in units_list:
                    f.write(f"{unit}\n")

    return filename


def load_servers_profile():
    if os.path.exists("servers_profile.json"):
        try:
            with open("servers_profile.json", "r") as f:
                servers = json.load(f)

                if servers and len(servers) > 0:
                    print(f"\nZnaleziono {len(servers)} zapisanych serwerów:")
                    for i, server in enumerate(servers, 1):
                        print(f"{i}. {server['hostname']} (użytkownik: {server['username']})")

                    use_profile = input("\nCzy chcesz użyć tych profili? (t/n): ").lower()
                    if use_profile == "t":
                        # Odszyfruj hasła
                        for server in servers:
                            if "password" in server and server["password"]:
                                server["password"] = decrypt_password(server["password"])
                        return servers
        except Exception as e:
            print(f"Błąd odczytu profilu serwerów: {str(e)}")
    return []


def save_servers_profile(servers):
    # Zaszyfruj hasła przed zapisem
    servers_to_save = []
    for server in servers:
        server_copy = server.copy()
        if "password" in server_copy and server_copy["password"]:
            server_copy["password"] = encrypt_password(server_copy["password"])
        servers_to_save.append(server_copy)

    try:
        with open("servers_profile.json", "w") as f:
            json.dump(servers_to_save, f, indent=4)
        print("Profile serwerów zostały zapisane")
    except Exception as e:
        print(f"Błąd zapisu profili serwerów: {str(e)}")


def add_server():
    hostname = input("Podaj adres hosta: ")
    username = input("Podaj nazwę użytkownika: ")
    password = getpass.getpass("Podaj hasło (zostaw puste dla autoryzacji kluczem): ")

    return {
        "hostname": hostname,
        "username": username,
        "password": password if password else None,
    }


def edit_server(server):
    print(f"Edycja serwera {server['hostname']} (użytkownik: {server['username']})")
    hostname = input(f"Nowy adres hosta [{server['hostname']}]: ") or server["hostname"]
    username = input(f"Nowa nazwa użytkownika [{server['username']}]: ") or server["username"]

    change_password = input("Czy chcesz zmienić hasło? (t/n): ").lower()
    password = server["password"]
    if change_password == "t":
        password = getpass.getpass("Podaj nowe hasło (zostaw puste dla autoryzacji kluczem): ")
        password = password if password else None

    return {"hostname": hostname, "username": username, "password": password}


def manage_servers():
    servers = load_servers_profile()

    while True:
        print("\nZARZĄDZANIE SERWERAMI")
        print("-" * 30)
        print(f"Liczba zapisanych serwerów: {len(servers)}")

        for i, server in enumerate(servers, 1):
            print(f"{i}. {server['hostname']} (użytkownik: {server['username']})")

        print("\nOpcje:")
        print("1. Dodaj nowy serwer")
        print("2. Edytuj serwer")
        print("3. Usuń serwer")
        print("4. Zapisz i wróć")

        choice = input("\nWybierz opcję (1-4): ")

        if choice == "1":
            server = add_server()
            servers.append(server)
            print(f"Dodano serwer {server['hostname']}")

        elif choice == "2":
            if not servers:
                print("Brak serwerów do edycji!")
                continue

            server_idx = int(input("Podaj numer serwera do edycji: ")) - 1
            if 0 <= server_idx < len(servers):
                updated_server = edit_server(servers[server_idx])
                servers[server_idx] = updated_server
                print(f"Zaktualizowano serwer {updated_server['hostname']}")
            else:
                print("Nieprawidłowy numer serwera!")

        elif choice == "3":
            if not servers:
                print("Brak serwerów do usunięcia!")
                continue

            server_idx = int(input("Podaj numer serwera do usunięcia: ")) - 1
            if 0 <= server_idx < len(servers):
                removed = servers.pop(server_idx)
                print(f"Usunięto serwer {removed['hostname']}")
            else:
                print("Nieprawidłowy numer serwera!")

        elif choice == "4":
            save_servers_profile(servers)
            break

        else:
            print("Nieprawidłowa opcja!")

    return servers


def process_servers(servers):
    if not servers:
        print("Brak serwerów do przetworzenia!")
        return

    print(f"\nPrzetwarzanie {len(servers)} serwerów...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(servers))) as executor:
        future_to_server = {
            executor.submit(get_systemd_units, server): server for server in servers
        }
        for future in concurrent.futures.as_completed(future_to_server):
            server = future_to_server[future]
            try:
                result = future.result()
                results.append(result)
                if result["status"] == "success":
                    print(f"✓ Pobrano dane z {result['hostname']}")
                else:
                    print(
                        f"✗ Błąd pobierania danych z {result['hostname']}: {result.get('error', 'Nieznany błąd')}"
                    )
            except Exception as e:
                print(f"✗ Wyjątek dla {server['hostname']}: {str(e)}")

    successful_results = [r for r in results if r["status"] == "success"]
    failed_results = [r for r in results if r["status"] != "success"]

    print(f"\nPodsumowanie: {len(successful_results)} sukces, {len(failed_results)} błąd")

    if successful_results:
        for result in successful_results:
            units = parse_units(result["content"])
            filename = save_report(result["hostname"], units)
            print(f"Raport dla {result['hostname']} zapisany do pliku: {filename}")

    return results


def main():
    while True:
        print("\nMENU GŁÓWNE")
        print("-" * 20)
        print("1. Zarządzaj serwerami")
        print("2. Pobierz dane z serwerów")
        print("3. Zarządzaj usługami")
        print("4. Wyjście")

        choice = input("\nWybierz opcję (1-4): ")

        if choice == "1":
            servers = manage_servers()

        elif choice == "2":
            servers = load_servers_profile()
            if not servers:
                print("Brak zapisanych serwerów. Najpierw dodaj serwery.")
                continue

            process_servers(servers)

            # Zapytaj czy chcemy dodać więcej serwerów
            add_more = input("\nCzy chcesz dodać więcej serwerów? (t/n): ").lower()
            if add_more == "t":
                servers = manage_servers()

        elif choice == "3":
            servers = load_servers_profile()
            if not servers:
                print("Brak zapisanych serwerów. Najpierw dodaj serwery.")
                continue

            # Wybierz serwer
            print("\nWybierz serwer:")
            for i, server in enumerate(servers, 1):
                print(f"{i}. {server['hostname']} (użytkownik: {server['username']})")

            server_idx = int(input("\nPodaj numer serwera: ")) - 1
            if not (0 <= server_idx < len(servers)):
                print("Nieprawidłowy numer serwera!")
                continue

            selected_server = servers[server_idx]

            # Wybierz akcję dla usługi
            print("\nZarządzanie usługami dla", selected_server["hostname"])
            print("1. Pokaż status usługi")
            print("2. Uruchom usługę")
            print("3. Zatrzymaj usługę")
            print("4. Zrestartuj usługę")
            print("5. Włącz usługę (enable)")
            print("6. Wyłącz usługę (disable)")

            action_choice = input("\nWybierz akcję (1-6): ")
            actions = {
                "1": "status",
                "2": "start",
                "3": "stop",
                "4": "restart",
                "5": "enable",
                "6": "disable",
            }

            if action_choice in actions:
                service_name = input("Podaj nazwę usługi: ")
                result = manage_systemd_service(
                    selected_server, service_name, actions[action_choice]
                )

                print(
                    f"\nWynik operacji {actions[action_choice]} dla {service_name} na {result['hostname']}:"
                )
                if result["status"] == "success":
                    print("Status: SUKCES")
                    if result.get("output"):
                        print(result["output"])
                else:
                    print(f"Status: BŁĄD - {result.get('error', 'Nieznany błąd')}")
                    if result.get("output"):
                        print(result["output"])
            else:
                print("Nieprawidłowa opcja!")

        elif choice == "4":
            print("Do widzenia!")
            break

        else:
            print("Nieprawidłowa opcja!")


if __name__ == "__main__":
    main()
