import concurrent.futures
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..shared.profile_producer import ProfileProducer


class SystemdService:
    """
    Usługa domenowa do zarządzania jednostkami systemd na zdalnych serwerach.
    Wykorzystuje ProfileProducer do zarządzania połączeniami.
    """

    def __init__(self, profile_producer: Optional[ProfileProducer] = None):
        """
        Inicjalizuje usługę systemd.

        Args:
            profile_producer: Opcjonalny obiekt ProfileProducer
        """
        self.profile_producer = profile_producer or ProfileProducer()

    def get_systemd_units(
        self, profile_names: List[str], parallel: bool = True, max_workers: int = 5
    ) -> Dict[str, Any]:
        """
        Pobiera jednostki systemd z wielu serwerów.

        Args:
            profile_names: Lista nazw profili połączeń
            parallel: Czy wykonywać zapytania równolegle
            max_workers: Maksymalna liczba równoległych zapytań

        Returns:
            Dict[str, Any]: Wyniki operacji dla każdego serwera
        """
        results = {}

        # Funkcja do wykonania dla każdego serwera
        def fetch_units(profile_name: str) -> Dict[str, Any]:
            conn = self.profile_producer.create_connection(profile_name)
            if not conn:
                return {
                    "profile_name": profile_name,
                    "status": "error",
                    "error": f"Nie można utworzyć połączenia dla profilu {profile_name}",
                }

            profile = self.profile_producer.get_profile(profile_name)
            hostname = profile.hostname if profile else profile_name

            try:
                # Tworzymy unikalną nazwę pliku tymczasowego
                temp_filename = (
                    f"systemd_units_temp_{hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                remote_temp_file = f"/tmp/{temp_filename}"
                local_temp_file = f"/tmp/{temp_filename}"

                # Polecenie do pobrania wszystkich jednostek i zapisania do pliku
                systemctl_cmd = f"systemctl list-units --all --no-pager > {remote_temp_file}"

                # Wykonaj polecenie na zdalnym serwerze
                cmd_result = conn.execute_command(systemctl_cmd)
                if not cmd_result.success:
                    return {
                        "profile_name": profile_name,
                        "hostname": hostname,
                        "status": "error",
                        "error": f"Błąd wykonania polecenia: {cmd_result.error_message}",
                    }

                # Pobierz plik ze zdalnego serwera
                download_result = conn.download_file(remote_temp_file, local_temp_file)
                if not download_result.success:
                    return {
                        "profile_name": profile_name,
                        "hostname": hostname,
                        "status": "error",
                        "error": f"Błąd pobierania pliku: {download_result.error_message}",
                    }

                # Usuń plik tymczasowy na zdalnym serwerze
                cleanup_cmd = f"rm {remote_temp_file}"
                conn.execute_command(cleanup_cmd)

                # Odczytaj zawartość pliku lokalnego
                try:
                    with open(local_temp_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Usuń lokalny plik tymczasowy
                    os.remove(local_temp_file)

                    return {
                        "profile_name": profile_name,
                        "hostname": hostname,
                        "content": content,
                        "status": "success",
                    }
                except Exception as e:
                    return {
                        "profile_name": profile_name,
                        "hostname": hostname,
                        "status": "error",
                        "error": f"Błąd odczytu pliku: {str(e)}",
                    }

            except Exception as e:
                return {
                    "profile_name": profile_name,
                    "hostname": hostname,
                    "status": "error",
                    "error": f"Wystąpił błąd: {str(e)}",
                }

        # Wykonaj dla każdego profilu
        if parallel and len(profile_names) > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(max_workers, len(profile_names))
            ) as executor:
                future_to_profile = {
                    executor.submit(fetch_units, profile_name): profile_name
                    for profile_name in profile_names
                }
                for future in concurrent.futures.as_completed(future_to_profile):
                    profile_name = future_to_profile[future]
                    try:
                        result = future.result()
                        results[profile_name] = result
                    except Exception as e:
                        results[profile_name] = {
                            "profile_name": profile_name,
                            "status": "error",
                            "error": f"Wyjątek: {str(e)}",
                        }
        else:
            for profile_name in profile_names:
                results[profile_name] = fetch_units(profile_name)

        return results

    def manage_systemd_service(
        self, profile_name: str, service_name: str, action: str
    ) -> Dict[str, Any]:
        """
        Zarządza usługą systemd na zdalnym serwerze.

        Args:
            profile_name: Nazwa profilu połączenia
            service_name: Nazwa usługi systemd
            action: Akcja do wykonania (start, stop, restart, status, enable, disable)

        Returns:
            Dict[str, Any]: Wynik operacji
        """
        valid_actions = ["start", "stop", "restart", "status", "enable", "disable"]
        if action not in valid_actions:
            return {
                "profile_name": profile_name,
                "service": service_name,
                "action": action,
                "status": "error",
                "error": f"Nieprawidłowa akcja: {action}. Dostępne: {', '.join(valid_actions)}",
            }

        conn = self.profile_producer.create_connection(profile_name)
        if not conn:
            return {
                "profile_name": profile_name,
                "service": service_name,
                "action": action,
                "status": "error",
                "error": f"Nie można utworzyć połączenia dla profilu {profile_name}",
            }

        profile = self.profile_producer.get_profile(profile_name)
        hostname = profile.hostname if profile else profile_name

        try:
            # Polecenie do zarządzania usługą
            systemctl_cmd = f"systemctl {action} {service_name}"

            # Wykonaj polecenie na zdalnym serwerze i pobierz wynik
            cmd_result = conn.execute_command(systemctl_cmd)

            return {
                "profile_name": profile_name,
                "hostname": hostname,
                "service": service_name,
                "action": action,
                "output": cmd_result.raw_output,
                "status": "success" if cmd_result.success else "error",
                "error": cmd_result.error_message if not cmd_result.success else None,
            }
        except Exception as e:
            return {
                "profile_name": profile_name,
                "hostname": hostname,
                "service": service_name,
                "action": action,
                "status": "error",
                "error": f"Wystąpił błąd: {str(e)}",
            }

    def parse_units(self, units_output: str) -> Dict[str, Any]:
        """
        Parsuje wyjście systemctl list-units.

        Args:
            units_output: Wyjście komendy systemctl list-units

        Returns:
            Dict[str, Any]: Przeanalizowane jednostki systemd
        """
        units: Dict[str, Any] = {
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
                        category = (
                            parts[1].split("_")[0] if "_" in parts[1] else parts[1].split(".")[0]
                        )
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

    def save_report(
        self, hostname: str, units: Dict[str, Any], output_dir: Optional[str] = None
    ) -> str:
        """
        Zapisuje raport z jednostkami systemd do pliku.

        Args:
            hostname: Nazwa hosta
            units: Analizowane jednostki systemd
            output_dir: Opcjonalny katalog wyjściowy

        Returns:
            str: Ścieżka do zapisanego pliku
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"systemd_units_report_{hostname}_{timestamp}.txt"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
        else:
            file_path = filename

        with open(file_path, "w", encoding="utf-8") as f:
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

        return file_path
