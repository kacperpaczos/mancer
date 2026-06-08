# Roadmap migracji do Mancer 2.0

Ten dokument opisuje **strategię migracji** z obecnego Mancer v0.7.x do Mancer 2.0 (System ORM): etapy prac, ryzyka, zależności i kryteria „gotowości” architektury.

## Założenia migracji (uzgodnione)

- **Refaktoryzacja inkrementalna**: budujemy nową architekturę krokami, nie „big-bang rewrite”.
- **Breaking change**: Mancer 2.0 może wprowadzać nowy interfejs i nowe idiomy (to major bump).
- **Dual API**: tryb deklaratywny (System ORM) współistnieje z trybem imperatywnym (Engine/Commands) i jest na nim zbudowany.
- **Zakres docelowy**: filesystem, procesy, usługi, sieć, kontenery (pełny scope), ale realizowany etapami.
- **Zależności zewnętrzne**: ich usuwanie jest odłożone (oddzielny strumień prac) — celem roadmapy jest architektura System ORM.

## Etap 1 — Engine (transport i wykonanie)

### Cel

Zbudować spójną warstwę wykonawczą, która:

- stabilnie uruchamia komendy lokalnie i zdalnie,
- zarządza cyklem życia połączeń,
- dostarcza jednolity rezultat wykonania z metadanymi.

### Kluczowe zmiany względem obecnego stanu

- wprowadzenie jawnego „Engine” jako podstawowego kontraktu wykonawczego,
- dla SSH: mechanizm utrzymywania sesji / reużycia połączeń, health-check, reconnect,
- spójne timeouts, kontrola cwd/env, obsługa błędów transportowych.

### Kryteria zakończenia etapu

- engine potrafi wykonywać sekwencje wielu komend z minimalnym narzutem po stronie SSH,
- błąd transportu jest jednoznacznie raportowany i rozróżnialny od błędu narzędzia,
- istnieją testy integracyjne w środowiskach „lokalnie” i „zdalnie”.

## Etap 2 — Core: Dialect + Compiler + Parsery

### Cel

Zbudować „Core” System ORM, który:

- ma formalne dialekty środowiska,
- kompiluje obiekty zapytań do poleceń shell,
- stosuje push-down (minimalizacja danych przesyłanych do Pythona),
- parsuje format maszynowy do rekordów.

### Zakres funkcjonalny (MVP)

Najpierw funkcje najbardziej deterministyczne:

- Filesystem: wyszukiwanie + metadane + operacje masowe
- Processes: listowanie + podstawowe filtrowanie i akcje

Usługi/sieć/kontenery mogą wejść jako osobne moduły, gdy „szkielet” Core jest stabilny.

### Ryzyka etapu

- wykrywanie środowiska i wersji narzędzi (wieloetapowe, z fallbackami),
- różnice dialektów (BusyBox/BSD) i brak spójnych opcji,
- konieczność zaprojektowania „capabilities” zamiast wielu wyjątków.

### Kryteria zakończenia etapu

- istnieje co najmniej 1 kompletny pion: Query object → Compiler → Dialect → Engine → Parser → rekordy,
- dialekty są rozszerzalne i mają mechanizm fallback,
- parsery nie opierają się na heurystykach „kolumn dla ludzi” (format maszynowy jest regułą).

## Etap 3 — ORM (fluent API i lazy evaluation)

### Cel

Zbudować interfejs programistyczny, który:

- pozwala budować zapytania bez natychmiastowego wykonania,
- ma spójne filtrowanie i akcje terminalne,
- jest zorganizowany w przestrzenie domenowe (filesystem/proc/services/net/docker),
- potrafi pracować w sposób przewidywalny (materializacja i cache wyników).

### Elementy projektowe do dopięcia

- jednolity model filtrowania (operatory, nazewnictwo, walidacja),
- definicja „punktów terminalnych” (kiedy następuje wykonanie),
- spójny model błędów i diagnostyki (różne klasy błędów),
- ergonomia debug (inspekcja skompilowanych poleceń i wybranych dialektów).

### Kryteria zakończenia etapu

- użytkownik może wykonać typowe scenariusze (np. selekcja plików i akcja masowa) bez ręcznego sklejania komend,
- lazy evaluation działa konsekwentnie,
- escape hatch jest dostępny i udokumentowany.

## Etap 4 — Ecosystem: dokumentacja, test matrix, migracja, „polish”

### Cel

Domknąć projekt tak, aby dało się go używać i rozwijać:

- dokumentacja architektury i zachowania,
- przewodnik migracji (co się zmieniło, jak przejść),
- testy na wielu środowiskach (Linux GNU, Linux BusyBox, macOS/BSD w miarę możliwości),
- benchmarki wydajności (zwłaszcza SSH i push-down).

### Kryteria zakończenia etapu

- gotowa sekcja dokumentacji System ORM (architektura, dialekty, przykłady użycia),
- pipeline testów pokrywa kluczowe środowiska,
- zdefiniowane i mierzalne metryki regresji wydajności.

## Największe ryzyka całego programu (i strategie redukcji)

### Parsery bez ciężkich bibliotek

Ryzyko: parsowanie „ludzkich” tabel jest kruche (zmienność formatów).

Strategia: push-down i format maszynowy jako zasada:

- output powinien mieć stabilne separatory,
- minimalne poleganie na „ładnym” formatowaniu,
- w razie braku opcji narzędzia: dialekt dobiera alternatywną strategię (np. inne narzędzie lub inny format).

### Dialekty i macierz możliwości

Ryzyko: BusyBox/BSD mogą nie wspierać części funkcji.

Strategia:

- capabilities (co jest dostępne) zamiast założeń,
- fallback i jasne komunikaty „feature not supported”,
- możliwość ręcznego wymuszenia dialektu przez użytkownika.

### Transport zdalny i cykl życia sesji

Ryzyko: utrzymywanie sesji zwiększa złożoność (health-check, reconnect).

Strategia:

- jawny cykl życia engine (open/close),
- spójne raportowanie błędów transportowych,
- testy integracyjne w warunkach niestabilnego połączenia.

## Co z „zero-dependency”

To jest **oddzielny strumień prac**:

- można go realizować równolegle, gdy architektura 2.0 jest już ustabilizowana,
- wymaga decyzji: co jest „core”, a co jest opcjonalnym adapterem/ekosystemem,
- wymaga planu migracji typów danych i formatowania wyników (co zastępuje DataFrame itd.).

W tej dokumentacji traktujemy to jako przyszłą iterację, aby nie blokować architektury System ORM.

