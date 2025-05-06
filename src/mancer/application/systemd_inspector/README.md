# SystemdInspector

Narzędzie do monitorowania i raportowania stanu jednostek systemd na zdalnych serwerach.

## Opis

SystemdInspector to narzędzie umożliwiające:

- Pobieranie listy jednostek systemd z zdalnych serwerów
- Analizowanie ich stanu i typu
- Generowanie raportów z podsumowaniem
- Zarządzanie profilami połączeń

## Wymagania

- Python 3.6+
- Biblioteka cryptography
- Narzędzie sshpass (do uwierzytelniania hasłem)
- Dostęp SSH do zdalnego serwera

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Zainstaluj sshpass (na Ubuntu/Debian)
sudo apt-get install sshpass
```

## Użycie

### Pobieranie i generowanie raportu

```bash
# Użycie interaktywne
python -m mancer.application.systemd_inspector inspect

# Użycie z parametrami
python -m mancer.application.systemd_inspector inspect -H server.example.com -u root

# Użycie z zapisanym profilem
python -m mancer.application.systemd_inspector inspect -p mojserwer

# Określenie katalogu wyjściowego dla raportu
python -m mancer.application.systemd_inspector inspect -p mojserwer -o /path/to/reports
```

### Zarządzanie profilami

```bash
# Dodanie nowego profilu
python -m mancer.application.systemd_inspector profile add mojserwer -H server.example.com -u root --password

# Wyświetlenie listy zapisanych profili
python -m mancer.application.systemd_inspector profile list

# Usunięcie profilu
python -m mancer.application.systemd_inspector profile remove mojserwer
```

## Bezpieczeństwo

Hasła są szyfrowane przed zapisaniem do pliku profilu, jednak należy pamiętać, że klucz szyfrowania jest wbudowany w kod. W środowisku produkcyjnym zaleca się dostosowanie mechanizmu przechowywania kluczy szyfrowania do własnych potrzeb bezpieczeństwa.

## Przykładowy raport

```
Raport jednostek systemd dla server.example.com
Data: 2023-05-01 12:34:56
==================================================

PODSUMOWANIE:
--------------------
Całkowita liczba jednostek: 123
Aktywne: 78
Nieaktywne: 42
Uszkodzone: 3

JEDNOSTKI DIMARK:
--------------------
dimark_app.service - active
dimark_db.service - active

JEDNOSTKI UŻYTKOWNIKA:
--------------------
user-1000.slice - active
user@1000.service - active

PODZIAŁ WEDŁUG TYPU:
--------------------

SERVICE:
apache2.service - active
mysql.service - active
...

SOCKET:
systemd-journald.socket - active
...

TARGET:
multi-user.target - active
...

PODZIAŁ WEDŁUG STANU:
--------------------

ACTIVE:
apache2.service - active
...

INACTIVE:
bluetooth.service - inactive
...

FAILED:
some-service.service - failed
...
``` 