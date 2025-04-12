# Narzędzia deweloperskie Mancer

Ten katalog zawiera narzędzia pomocnicze do pracy z projektem Mancer w wersji deweloperskiej.

## Instalacja środowiska deweloperskiego

Aby zainstalować projekt w trybie deweloperskim, uruchom:

```bash
./tools/install_dev.py
```

Ten skrypt:
1. Automatycznie zwiększy numer wersji w pliku `setup.py` (część Z w formacie X.Y.Z)
2. Utworzy wirtualne środowisko Python w katalogu `.venv` (jeśli jeszcze nie istnieje)
3. Zainstaluje wszystkie zależności z pliku `requirements.txt`
4. Zainstaluje pakiet Mancer w trybie deweloperskim (`pip install -e .`)
5. Zapyta, czy chcesz automatycznie aktywować środowisko wirtualne w nowym terminalu

Opcje:
- `--force` lub `-f` - pomija pytania i wymusza instalację
- `--activate` lub `-a` - automatycznie aktywuje środowisko po instalacji

## Uruchamianie aplikacji

Aby uruchomić aplikację w środowisku deweloperskim, użyj:

```bash
./tools/run_dev.py
```

Ten skrypt:
1. Automatycznie wykryje czy znajdujesz się w środowisku wirtualnym
2. Jeśli nie, aktywuje środowisko i uruchomi się ponownie
3. Uruchomi aplikację Mancer z aktualnej wersji deweloperskiej

## Usuwanie środowiska deweloperskiego

Jeśli chcesz usunąć środowisko deweloperskie, możesz użyć:

```bash
./tools/uninstall_dev.py
```

Ten skrypt:
1. Sprawdzi czy nie jesteś aktualnie w środowisku wirtualnym
2. Jeśli jesteś, poprosi o ręczne wykonanie deaktywacji (polecenie `deactivate`)
3. Poprosi o potwierdzenie przed usunięciem (można pominąć z flagą `--force`)
4. Usunie katalog środowiska wirtualnego `.venv`
5. Usunie pliki instalacyjne (`.egg-info`, `__pycache__`, pliki `.pyc`)
6. Usunie katalogi `build` i `dist` jeśli istnieją

⚠️ **Ważne:** Przed uruchomieniem skryptu upewnij się, że środowisko wirtualne nie jest aktywne. 
Jeśli widzisz `(.venv)` na początku wiersza poleceń, wpisz `deactivate` przed uruchomieniem skryptu.

Jeżeli po wykonaniu `deactivate` skrypt nadal wykrywa aktywne środowisko, użyj flagi `--ignore-venv`:

```bash
./tools/uninstall_dev.py --ignore-venv
```

Twój kod źródłowy i pliki projektu pozostaną nietknięte.

## Wskazówki

- Skrypty działają zarówno na systemach Linux/macOS jak i Windows
- Po każdym uruchomieniu `install_dev.py` wersja aplikacji jest automatycznie zwiększana
- Skrypty automatycznie zarządzają środowiskiem wirtualnym, aktywując je w razie potrzeby
- Użyj flagi `--force` lub `-f` z dowolnym skryptem, aby pominąć pytania i potwierdzenia
- Użyj `install_dev.py --activate`, aby automatycznie aktywować środowisko po instalacji
- Jeśli masz problemy z deaktywacją środowiska, użyj `uninstall_dev.py --ignore-venv`
- Do deaktywacji środowiska zawsze używaj polecenia `deactivate` bezpośrednio w terminalu

## Rozwiązywanie problemów

Jeśli napotkasz problemy:

1. Upewnij się, że masz zainstalowany Python 3.8 lub nowszy
2. Sprawdź czy masz uprawnienia do zapisu w katalogu projektu
3. W przypadku problemów z zależnościami, sprawdź plik `requirements.txt`
4. Jeśli po wykonaniu `deactivate` skrypt nadal wykrywa środowisko:
   - Uruchom nowy terminal bez aktywacji środowiska
   - Użyj flagi `--ignore-venv` aby wymusić usunięcie
5. Zawsze używaj komend aktywacji/deaktywacji bezpośrednio w terminalu:
   - Aktywacja: `source .venv/bin/activate` (Linux/macOS) lub `.venv\Scripts\activate` (Windows)
   - Deaktywacja: `deactivate` (wszystkie systemy)

W razie pytań lub problemów, skontaktuj się z autorem: kacperpaczos2024@proton.me 