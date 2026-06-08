# Mancer 2.0 (System ORM) — wprowadzenie

Ten rozdział opisuje **kierunek rozwoju Mancer do wersji 2.0**: przejście z modelu „uruchom komendę i sparsuj tekst” do modelu **System ORM**, w którym system operacyjny jest traktowany jak baza danych, a obiekty systemowe (pliki, procesy, usługi itd.) są „rekordami”, na których wykonuje się zapytania i operacje.

## Cel

Mancer 2.0 ma udostępniać **dwa komplementarne style pracy**:

- **Deklaratywny model zapytań (System ORM)**: „zbuduj zapytanie, a potem je zmaterializuj / wykonaj akcję”
- **Imperatywne wykonywanie poleceń (Command/Engine API)**: „wykonaj komendę teraz i zwróć wynik”

Deklaratywny model zapytań **nie zastępuje** imperatywnego wykonywania poleceń — **opiera się na nim**. ORM buduje intencję, Core ją kompiluje, a Engine wykonuje finalną komendę.

W praktyce oznacza to:

- **Warstwa ORM** buduje zapytanie (lazy), bez natychmiastowego wykonywania.
- **Warstwa Core (Compiler + Dialect)** kompiluje zapytanie do komend shell specyficznych dla środowiska.
- **Warstwa Engine** wykonuje skompilowaną komendę lokalnie lub zdalnie, optymalnie (m.in. z utrzymywaniem sesji SSH).
- **Parsery** zwracają dane już w formie ustrukturyzowanej (lista słowników / dataclasses), a nie surowy tekst.

Równolegle:

- **Warstwa imperatywna** pozostaje dostępna dla programisty jako bezpośrednie uruchamianie poleceń (np. do diagnostyki, prototypowania, niestandardowych przypadków).

## Dlaczego to jest potrzebne (motywacja)

W obecnym Mancer (v0.7.x) dominują wzorce:

- budowanie polecenia jako string,
- wykonanie przez `subprocess`,
- pobranie dużego stdout,
- parsowanie/transformacje w Pythonie.

To jest proste i działa, ale ma limity:

- **wydajność** (duży transfer tekstu + parsowanie po stronie Pythona),
- **zmienność środowiska** (GNU vs BusyBox vs BSD, różne flagi i formaty),
- **brak „push-down”** (logika nie jest spychana do narzędzi systemowych),
- **trudniejsza kompozycja** (łączenie filtrów/operacji staje się ręcznym składaniem komend).

## Założenia projektowe Mancer 2.0

- **System ORM**: spójny model domenowy dla OS: Filesystem, Processes, Services, Network, Containers.
- **Data-first**: Python pracuje na danych ustrukturyzowanych; tekst jest detalem transportowym.
- **Push-down**: filtrowanie, projekcje i agregacje realizowane głównie w shell (np. `find`, `awk`, `grep`), a Python dostaje wynik już „w rekordach”.
- **Dialekty**: różnice środowisk (GNU/BusyBox/BSD) są formalnym elementem architektury, a nie zestawem `ifów` rozsianych po kodzie.
- **Lazy evaluation**: zapytanie nie odpala komend dopóki nie jest „zmaterializowane” (iteracja, `count`, akcja terminalna).
- **Dual API**: deklaratywne zapytania + imperatywne wykonanie jako równorzędne ścieżki.
- **Escape hatch**: użytkownik zawsze ma możliwość zejścia do „raw shell”, gdy abstrakcja nie wystarcza.
- **Version-awareness**: wybór flag, formatów i parserów zależy od wykrytej wersji narzędzia (np. `find`, `ps`, `docker`).

## Zakres MVP (pierwsze wydanie Mancer 2.0)

Docelowo ORM obejmuje:

- **Filesystem**: wyszukiwanie, selekcja, metadane, operacje masowe (np. usuwanie/archiwizacja).
- **Processes**: listowanie, filtrowanie, sygnały, podstawowa inspekcja.
- **Services**: systemd (tam gdzie dostępne), status/start/stop/restart, filtrowanie.
- **Network**: podstawowa inspekcja (zależnie od dostępnych narzędzi).
- **Containers**: Docker tam, gdzie zainstalowany (z pełnym wykrywaniem wersji i fallbackami).

## Co nie jest celem „od razu”

- **Wymuszenie „zero-dependency” w repo**: to jest osobny strumień prac (pozostaje jako TODO w roadmapie), niezależny od samej architektury System ORM.
- **Pełne pokrycie wszystkich niszowych narzędzi**: priorytetem jest spójność modelu i możliwość rozszerzania, a nie kompletność listy komend na starcie.

## Jak czytać dalszą dokumentację

- [Stan obecny (v0.7.x)](stan-obecny.md) — co dziś działa i jakie są ograniczenia.
- [Architektura docelowa (v2.0)](architektura-docelowa.md) — warstwy, odpowiedzialności, przepływ danych.
- [Roadmap migracji](roadmap-migracji.md) — etapy prac, ryzyka, kryteria zakończenia.

