# RemoteConfigManager

Zaawansowane narzędzie do zarządzania i synchronizacji plików konfiguracyjnych na zdalnych serwerach.

## Opis

RemoteConfigManager to narzędzie umożliwiające:

- Bezpieczne połączenie z serwerami przez SSH
- Tworzenie kopii zapasowych plików konfiguracyjnych
- Wykrywanie różnic między plikami lokalnymi i zdalnymi
- Synchronizację plików konfiguracyjnych
- Restart usług po aktualizacji konfiguracji
- Zarządzanie profilami dla wielu serwerów

## Wymagania

- Python 3.6+
- Paramiko (biblioteka SSH)
- Rich (interfejs konsolowy)
- Dostęp SSH do serwerów

## Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt
```

## Użycie

### Zarządzanie profilami

Przed połączeniem z serwerem należy utworzyć profil, który zawiera dane dostępowe i konfiguracyjne.

```bash
# Dodaj nowy profil
python -m mancer.application.remote_config_manager profile add my_server -H example.com -u admin -d /var/www/html -s nginx,php-fpm

# Wyświetl listę dostępnych profili
python -m mancer.application.remote_config_manager profile list

# Aktywuj profil
python -m mancer.application.remote_config_manager profile activate my_server

# Usuń profil
python -m mancer.application.remote_config_manager profile remove my_server
```

### Połączenie z serwerem

```bash
# Połącz z serwerem używając aktywnego profilu
python -m mancer.application.remote_config_manager connect

# Połącz z serwerem używając określonego profilu
python -m mancer.application.remote_config_manager connect -p my_server
```

### Tworzenie kopii zapasowych

```bash
# Utwórz kopię zapasową plików konfiguracyjnych na serwerze
python -m mancer.application.remote_config_manager backup
```

### Wyświetlanie różnic

```bash
# Pokaż różnice między plikami w pamięci podręcznej a plikami serwerowymi
python -m mancer.application.remote_config_manager diff
```

### Aktualizacja plików

```bash
# Zaktualizuj pliki na serwerze na podstawie plików w pamięci podręcznej
python -m mancer.application.remote_config_manager update
```

## Organizacja plików

Po utworzeniu kopii zapasowej, pliki są przechowywane w następujących katalogach:

- `~/.remote_config_manager/servers/` - Aktualne pliki z serwerów
- `~/.remote_config_manager/cache/` - Pliki w pamięci podręcznej (kopia robocza)
- `~/.remote_config_manager/backups/` - Kopie zapasowe z datą utworzenia
- `~/.remote_config_manager/profiles/` - Profile połączeń

## Bezpieczeństwo

Hasła są przechowywane w plikach profili w formie niezaszyfrowanej. Zaleca się odpowiednie zabezpieczenie tych plików lub korzystanie z uwierzytelniania kluczem SSH.

## Przykładowy przepływ pracy

1. Utwórz profil dla serwera
2. Połącz się z serwerem
3. Utwórz kopię zapasową plików konfiguracyjnych
4. Dokonaj zmian w plikach w katalogu pamięci podręcznej (`~/.remote_config_manager/cache/`)
5. Sprawdź różnice za pomocą polecenia `diff`
6. Zaktualizuj pliki na serwerze za pomocą polecenia `update`
7. Zrestartuj usługi (opcjonalnie podczas aktualizacji) 