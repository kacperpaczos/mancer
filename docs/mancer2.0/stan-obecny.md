# Mancer v0.7.x — stan obecny (co jest)

Ten dokument opisuje **obecną architekturę Mancer (v0.7.x)** z perspektywy tego, co trzeba zachować (wartościowe elementy), oraz co ogranicza dalszy rozwój w stronę „System ORM”.

## Obecna filozofia działania

Mancer dzisiaj jest przede wszystkim:

- **frameworkiem do uruchamiania komend** (lokalnie i zdalnie),
- z **własnymi klasami komend** (np. `ls`, `find`, `ps`, `df`) i fabryką (`CommandFactory`),
- z warstwą „backendów” (bash/ssh), które wykonują komendy i zwracają wynik.

W typowym przepływie:

- kod użytkownika tworzy obiekt komendy,
- komenda buduje string polecenia,
- backend wykonuje polecenie i zbiera stdout/stderr,
- wynik jest mapowany do `CommandResult`,
- (czasem) komenda parsuje stdout do bardziej ustrukturyzowanej postaci.

## Aktualne warstwy architektoniczne (DDD)

W repozytorium istnieje już jasny podział:

- **Interface**: wejścia użytkownika (CLI/API), fabryka komend, formatowanie rezultatów.
- **Application**: orkiestracja wykonania (ShellRunner, CommandManager, chainy).
- **Domain**: modele (`CommandContext`, `CommandResult`), interfejsy, usługi (wersje narzędzi, konwersje danych, logowanie).
- **Infrastructure**: konkretne implementacje komend i backendów (bash/ssh), konfiguracja, integracje.

To jest dobra baza pod Mancer 2.0, bo rozdziela odpowiedzialności i pozwala dobudować nowe moduły bez „wylewania” architektury.

## Komendy: model „Command objects”

### Cechy

- Komendy mają postać klas dziedziczących po bazowej klasie (immutable builder).
- Budowanie polecenia odbywa się zwykle przez składanie:
  - opcji,
  - parametrów,
  - flag,
  - argumentów pozycyjnych.
- Parsowanie jest implementowane per-komenda (często proste split/regex), a tam gdzie potrzeba — bardziej szczegółowe (np. `ls` w trybie tabelarycznym).

### Zalety

- Zwięzłe API budowania poleceń.
- Łatwość rozszerzania o nowe komendy.
- Możliwość testowania per-komenda.

### Ograniczenia w kontekście System ORM

- Komendy są „wąskie” i nie stanowią spójnego modelu obiektowego OS (filesystem/procesy/usługi to osobne wycinki, bez wspólnego języka zapytań).
- Logika filtrowania i transformacji często dzieje się **po stronie Pythona**, co jest przeciwne filozofii push-down.
- Parsowanie jest silnie zależne od tekstowego formatu wyjścia, które zmienia się między środowiskami i wersjami narzędzi.

## Backendy: lokalny bash i zdalny SSH

### Bash (lokalnie)

- Wykonanie poleceń odbywa się przez standardowe uruchamianie procesów.
- Występuje tryb „live output” oraz tryb standardowy.

### SSH (zdalnie)

- Zdalne wykonanie realizowane jest jako wywołanie systemowego klienta SSH.
- Istnieje abstrakcja „sesji” po stronie Pythona (zarządzanie stanem), ale typowe wykonanie komendy jest w praktyce **oddzielnym uruchomieniem procesu `ssh`**.
- W obecnym stanie brak jest spójnej strategii „persistent transport”, czyli utrzymywania jednego kanału wykonawczego do serwera, tak aby uniknąć kosztu handshake.

### Ograniczenia

- **Wydajność**: ponawiane handshaki SSH w scenariuszach, gdzie wykonuje się wiele krótkich komend.
- **Stabilność semantyki**: „zdalny bash” nie jest modelowany jako jednolite środowisko wykonawcze z jawnie zarządzanym cyklem życia.

## Wyniki i formatowanie danych

### `CommandResult` jako standardowy nośnik

Zwracany jest obiekt wyniku zawierający:

- `raw_output` (surowy stdout),
- `structured_output` (różne typy: lista, słownik, tabela),
- `exit_code`, `success`, `error_message`,
- metadane i historia wykonania.

### Zaleta

Jest to dobry punkt zaczepienia do Mancer 2.0: w docelowym System ORM wynik powinien być ustrukturyzowany i posiadać ślad wykonania.

### Ograniczenia

- W `structured_output` pojawiają się różne formaty zależne od komendy i preferencji, co utrudnia konsekwentne API na poziomie domeny.
- W praktyce nadal często trzeba operować na tekście, bo dane nie są „wymuszane” na źródle (push-down).

## Version-awareness (świadomość wersji narzędzi)

W projekcie istnieje mechanika:

- mapowania komend do nazw narzędzi (`tool_name`),
- wykrywania wersji i ostrzeżeń kompatybilności,
- miejscami: przygotowania alternatywnych parserów/adapterów dla wersji.

To jest kluczowy fundament pod dialekty w Mancer 2.0, ale w obecnym stanie bywa nierównomiernie stosowany (różne komendy w różnym stopniu).

## Najważniejsze problemy do rozwiązania w 2.0

- **Brak formalnej warstwy kompilacji (Compiler)**: obecnie komendy budują string bez pośredniego AST/Query object.
- **Brak dialektów środowiska**: różnice GNU/BusyBox/BSD nie są pierwszorzędnym elementem projektu.
- **Za dużo logiki w Pythonie**: filtrowanie i formatowanie danych po stronie klienta zamiast na systemie docelowym.
- **Transport SSH nie jest zoptymalizowany**: potrzeba mechanizmu utrzymywania sesji i multiplexingu.

## Co z obecnej architektury warto zachować

- **DDD i rozdział modułów**: daje skalowalność i testowalność.
- **Jednolity model wyniku (`CommandResult`)**: może stać się standardem „Result rowset” w ORM.
- **Mechanika wersji narzędzi**: to naturalny „szkielet” dla wyboru dialektu i kompilacji.
- **Testy i fixtures**: można je wykorzystać do walidacji zachowania kompilatorów i parserów.

