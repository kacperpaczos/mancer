"""
Lista wszystkich podstawowych komend basha wspieranych w frameworku.

Ten moduł zawiera listę wszystkich podstawowych komend basha, które są wspierane
w frameworku, wraz z ich opisami i przykładami użycia.
"""
from typing import Dict, List, Tuple

# Format: (komenda, opis, przykład użycia)
BASH_COMMANDS: List[Tuple[str, str, str]] = [
    # Podstawowe komendy
    ("ls", "Listuje zawartość katalogu", "ls -la"),
    ("cd", "Zmienia katalog roboczy", "cd /home/user"),
    ("pwd", "Wyświetla aktualny katalog roboczy", "pwd"),
    ("mkdir", "Tworzy katalog", "mkdir -p /path/to/dir"),
    ("rmdir", "Usuwa pusty katalog", "rmdir dir"),
    ("touch", "Tworzy pusty plik lub aktualizuje datę modyfikacji", "touch file.txt"),
    ("cp", "Kopiuje pliki lub katalogi", "cp -r source dest"),
    ("mv", "Przenosi pliki lub katalogi", "mv source dest"),
    ("rm", "Usuwa pliki lub katalogi", "rm -rf dir"),
    ("cat", "Wyświetla zawartość pliku", "cat file.txt"),
    ("echo", "Wyświetla tekst", "echo 'Hello, World!'"),
    
    # Wyszukiwanie i filtrowanie
    ("grep", "Wyszukuje wzorzec w pliku lub strumieniu", "grep 'pattern' file.txt"),
    ("find", "Wyszukuje pliki w katalogu", "find . -name '*.py'"),
    ("which", "Lokalizuje plik wykonywalny", "which python"),
    ("locate", "Szybko wyszukuje pliki w bazie danych", "locate file.txt"),
    
    # Edycja tekstu
    ("sed", "Edytuje strumień tekstu", "sed 's/old/new/g' file.txt"),
    ("awk", "Przetwarza i analizuje tekst", "awk '{print $1}' file.txt"),
    ("cut", "Wycina fragmenty linii", "cut -d':' -f1 /etc/passwd"),
    ("sort", "Sortuje linie tekstu", "sort file.txt"),
    ("uniq", "Usuwa powtarzające się linie", "sort file.txt | uniq"),
    ("wc", "Liczy linie, słowa i znaki", "wc -l file.txt"),
    ("head", "Wyświetla początek pliku", "head -n 10 file.txt"),
    ("tail", "Wyświetla koniec pliku", "tail -n 10 file.txt"),
    
    # Zarządzanie procesami
    ("ps", "Wyświetla procesy", "ps aux"),
    ("kill", "Zabija proces", "kill -9 1234"),
    ("killall", "Zabija procesy o podanej nazwie", "killall firefox"),
    ("top", "Wyświetla aktywne procesy", "top"),
    ("htop", "Interaktywny top", "htop"),
    ("bg", "Wznawia proces w tle", "bg %1"),
    ("fg", "Wznawia proces na pierwszym planie", "fg %1"),
    ("jobs", "Wyświetla zadania w tle", "jobs"),
    ("nohup", "Uruchamia komendę odporną na rozłączenie", "nohup command &"),
    
    # Sieć
    ("ping", "Pinguje host", "ping -c 4 example.com"),
    ("curl", "Pobiera zawartość URL", "curl -O https://example.com/file"),
    ("wget", "Pobiera pliki z sieci", "wget https://example.com/file"),
    ("ssh", "Łączy się z hostem przez SSH", "ssh user@host"),
    ("scp", "Kopiuje pliki przez SSH", "scp file.txt user@host:/path"),
    ("rsync", "Synchronizuje pliki", "rsync -avz source/ dest/"),
    ("netstat", "Wyświetla połączenia sieciowe", "netstat -tuln"),
    ("ifconfig", "Konfiguruje interfejsy sieciowe", "ifconfig eth0"),
    ("ip", "Zarządza interfejsami sieciowymi", "ip addr show"),
    ("dig", "Odpytuje serwery DNS", "dig example.com"),
    ("nslookup", "Odpytuje serwery DNS", "nslookup example.com"),
    ("traceroute", "Śledzi trasę pakietów", "traceroute example.com"),
    
    # Archiwizacja i kompresja
    ("tar", "Archiwizuje pliki", "tar -czvf archive.tar.gz dir/"),
    ("gzip", "Kompresuje pliki", "gzip file.txt"),
    ("gunzip", "Dekompresuje pliki gzip", "gunzip file.txt.gz"),
    ("zip", "Tworzy archiwum ZIP", "zip -r archive.zip dir/"),
    ("unzip", "Rozpakowuje archiwum ZIP", "unzip archive.zip"),
    
    # Zarządzanie systemem
    ("df", "Wyświetla użycie dysku", "df -h"),
    ("du", "Wyświetla użycie dysku przez katalogi", "du -sh dir/"),
    ("free", "Wyświetla użycie pamięci", "free -h"),
    ("uname", "Wyświetla informacje o systemie", "uname -a"),
    ("uptime", "Wyświetla czas działania systemu", "uptime"),
    ("who", "Wyświetla zalogowanych użytkowników", "who"),
    ("whoami", "Wyświetla aktualnego użytkownika", "whoami"),
    ("id", "Wyświetla identyfikatory użytkownika", "id"),
    ("chmod", "Zmienia uprawnienia pliku", "chmod 755 file.sh"),
    ("chown", "Zmienia właściciela pliku", "chown user:group file.txt"),
    ("chgrp", "Zmienia grupę pliku", "chgrp group file.txt"),
    ("passwd", "Zmienia hasło użytkownika", "passwd"),
    ("su", "Przełącza użytkownika", "su - user"),
    ("sudo", "Wykonuje komendę jako inny użytkownik", "sudo command"),
    ("systemctl", "Zarządza usługami systemd", "systemctl status service"),
    ("journalctl", "Wyświetla logi systemd", "journalctl -u service"),
    
    # Zmienne środowiskowe
    ("env", "Wyświetla zmienne środowiskowe", "env"),
    ("export", "Ustawia zmienną środowiskową", "export VAR=value"),
    ("set", "Wyświetla lub ustawia opcje powłoki", "set -e"),
    ("unset", "Usuwa zmienną środowiskową", "unset VAR"),
    
    # Inne
    ("date", "Wyświetla lub ustawia datę i czas", "date"),
    ("cal", "Wyświetla kalendarz", "cal"),
    ("history", "Wyświetla historię komend", "history"),
    ("clear", "Czyści ekran terminala", "clear"),
    ("man", "Wyświetla podręcznik", "man ls"),
    ("info", "Wyświetla dokumentację info", "info ls"),
    ("alias", "Tworzy alias komendy", "alias ll='ls -la'"),
    ("crontab", "Zarządza zadaniami cron", "crontab -e"),
    ("at", "Planuje jednorazowe zadanie", "at 10:00"),
    ("xargs", "Buduje i wykonuje komendy z wejścia", "find . -name '*.txt' | xargs grep 'pattern'"),
    ("tee", "Zapisuje wyjście do pliku i wyświetla", "command | tee file.txt"),
]


def get_command_info(command: str) -> Tuple[str, str, str]:
    """
    Zwraca informacje o komendzie.
    
    Args:
        command: Nazwa komendy
        
    Returns:
        Tuple[str, str, str]: (komenda, opis, przykład użycia)
        
    Raises:
        ValueError: Gdy komenda nie jest wspierana
    """
    for cmd in BASH_COMMANDS:
        if cmd[0] == command:
            return cmd
    raise ValueError(f"Komenda '{command}' nie jest wspierana")


def get_all_commands() -> List[str]:
    """
    Zwraca listę wszystkich wspieranych komend.
    
    Returns:
        List[str]: Lista nazw komend
    """
    return [cmd[0] for cmd in BASH_COMMANDS]


def get_commands_by_category() -> Dict[str, List[str]]:
    """
    Zwraca komendy pogrupowane według kategorii.
    
    Returns:
        Dict[str, List[str]]: Słownik kategorii i komend
    """
    categories = {
        "podstawowe": ["ls", "cd", "pwd", "mkdir", "rmdir", "touch", "cp", "mv", "rm", "cat", "echo"],
        "wyszukiwanie": ["grep", "find", "which", "locate"],
        "edycja_tekstu": ["sed", "awk", "cut", "sort", "uniq", "wc", "head", "tail"],
        "procesy": ["ps", "kill", "killall", "top", "htop", "bg", "fg", "jobs", "nohup"],
        "siec": ["ping", "curl", "wget", "ssh", "scp", "rsync", "netstat", "ifconfig", "ip", "dig", "nslookup", "traceroute"],
        "archiwizacja": ["tar", "gzip", "gunzip", "zip", "unzip"],
        "system": ["df", "du", "free", "uname", "uptime", "who", "whoami", "id", "chmod", "chown", "chgrp", "passwd", "su", "sudo", "systemctl", "journalctl"],
        "zmienne": ["env", "export", "set", "unset"],
        "inne": ["date", "cal", "history", "clear", "man", "info", "alias", "crontab", "at", "xargs", "tee"]
    }
    return categories 