# Mancer 2.0 — architektura docelowa (co ma być)

Ten dokument opisuje **docelową architekturę Mancer 2.0** jako „System ORM”, inspirowaną wzorcami znanymi z SQLAlchemy (separacja Core vs ORM, dialekty, kompilator).

Kluczowa zmiana: Mancer 2.0 nie jest wyłącznie „wrapperem komend”, ale **spójnym mechanizmem zapytań i operacji na obiektach systemu** — przy jednoczesnym zachowaniu **pełnoprawnego, imperatywnego wykonywania poleceń** jako API dla programisty.

## Model mentalny: system jak baza danych

W System ORM:

- **obiekty systemu** (plik, proces, usługa, kontener) są odpowiednikami rekordów,
- **zapytania** są deklaratywne (budujesz intencję),
- **kompilator** zamienia intencję na polecenia shell,
- **dialekt** decyduje o składni i możliwościach (GNU/BusyBox/BSD, wersje narzędzi),
- **parser** zwraca rekordy w ujednoliconej strukturze (bez „surowego tekstu” jako głównego API).

Równolegle, w Mancer 2.0 istnieje ścieżka „low-level”:

- programista może **imperatywnie** uruchomić polecenie (lokalnie/zdalnie),
- może otrzymać wynik wykonania i samodzielnie go zinterpretować,
- może też użyć tego jako „escape hatch” lub narzędzia diagnostycznego.

## Filary Mancer 2.0

### Data-first

Python pracuje na danych ustrukturyzowanych. Tekst jest transportem, nie interfejsem.

### Push-down

Jeśli da się wykonać filtrację, projekcję lub agregację na maszynie docelowej, to:

- robimy to narzędziami systemowymi (find/awk/sed/grep/stat),
- wysyłamy do Pythona minimalny, regularny format wyników,
- parser po stronie Pythona jest prosty i przewidywalny.

### Lazy evaluation

Budowanie zapytania nie powoduje efektów ubocznych.

Wykonanie następuje dopiero w „punktach terminalnych”, np.:

- iteracja po wynikach,
- pobranie liczności,
- akcja (delete/kill/restart).

### Escape hatch

Zawsze istnieje możliwość:

- wykonania „surowej” komendy,
- dołączenia brakującego parametru lub flagi,
- ręcznego wyboru dialektu/strategii wykonania.

To jest świadome zabezpieczenie przed „przeciekaniem” abstrakcji.

### Dual API (deklaratywne + imperatywne)

Mancer 2.0 ma mieć **dwa współistniejące, komplementarne interfejsy**:

- **Deklaratywny** (ORM): budujesz zapytania i akcje na modelu domenowym, a wykonanie jest opóźnione do punktu terminalnego.
- **Imperatywny** (Engine/Commands): uruchamiasz polecenia bezpośrednio, kontrolując detale wykonania.

Najważniejsza zasada architektoniczna: **deklaratywny ORM jest zbudowany na imperatywnym wykonaniu**. Innymi słowy, ORM nie „robi magii” — tylko generuje i uruchamia komendy w sposób uporządkowany.

### Version-awareness i capability-based behavior

System musi podejmować decyzje na podstawie:

- systemu operacyjnego i narzędzi użytkowych,
- wersji narzędzi,
- dostępnych opcji/flag,
- ograniczeń środowiska (np. BusyBox bez pewnych funkcji).

Zamiast „hard-code” w wielu miejscach, Mancer 2.0 używa:

- **dialektów**,
- **macierzy możliwości (capabilities)**,
- **strategii fallback**.

## „Onion architecture”: 4 warstwy

Mancer 2.0 jest zorganizowany w cztery warstwy (od dołu do góry):

1) Engine (Transport & Execution)  
2) Core: Dialect + Compiler + Parsers  
3) ORM (Domain Abstraction)  
4) Escape Hatch

Uwaga: **imperatywne wykonywanie** jest realizowane bezpośrednio przez Warstwę 1 (Engine) i może być używane niezależnie od ORM. ORM jest „nadbudową” na Engine + Core.

Poniżej opis odpowiedzialności każdej warstwy.

### Warstwa 1: Engine (transport i wykonanie)

**Odpowiedzialność**: niezawodne i efektywne uruchamianie komend lokalnie i zdalnie oraz mapowanie wyników na jednolity rezultat wykonania.

Engine nie wie nic o „filesystem query” czy „process query”. Dla Engine istnieje tylko:

- komenda do wykonania,
- środowisko wykonania (lokalne/zdalne),
- parametry wykonawcze (timeout, cwd, env),
- wynik (exit code + stdout/stderr + metadane wykonania).

Engine jest jednocześnie podstawą dla dwóch stylów pracy:

- **imperatywnego** (programista wywołuje wykonanie bezpośrednio),
- **deklaratywnego** (ORM zleca wykonanie po kompilacji).

**Wymóg wydajnościowy dla SSH**: transport powinien wspierać utrzymywanie sesji i redukcję kosztów powtarzanych wywołań (connection reuse / multiplexing).  
W praktyce oznacza to zarządzanie cyklem życia „kanału” do hosta i mechanizmy health-check/reconnect.

### Warstwa 2: Core (Dialect & Compiler)

To jest „serce” System ORM.

#### Dialect

**Odpowiedzialność**: opisać różnice środowiska i przekazać kompilatorowi:

- jak brzmią flagi i składnia w danym systemie,
- jakie są ograniczenia,
- jakie strategie push-down są dostępne,
- jak formatować output, by parser był prosty.

Przykłady różnic (na poziomie idei):

- GNU vs BusyBox: brak niektórych flag lub inna semantyka,
- BSD/macOS: inne zachowanie `stat`, inne opcje narzędzi,
- różne wersje `find`/`ps`/`docker`: dostępność wyjść maszynowych, JSON, formatów.

#### Compiler

**Odpowiedzialność**: przetłumaczyć obiekt zapytania (AST zapytań System ORM) na finalne polecenie wykonawcze zgodne z dialektem.

Kluczowe cechy kompilatora:

- deterministyczna kompilacja (to samo zapytanie → ta sama komenda),
- możliwość introspekcji (debug: „co zostanie wykonane i dlaczego”),
- kontrola strategii push-down (np. „zamiast pobrać wszystko, policz po stronie hosta”),
- świadome budowanie formatów wyników (tak, aby parser był trywialny).

#### Parsery

**Odpowiedzialność**: przekształcić „format maszynowy” w rekordy domenowe.

Założenie jest takie, że parsery są „ubogie”, bo większość pracy jest zrobiona wcześniej:

- output ma stabilne separatory,
- output jest jednoliniowy per rekord,
- pola są jednoznaczne,
- brak heurystyk zależnych od wizualnych kolumn dla ludzi.

### Warstwa 3: ORM (abstrakcja domenowa)

**Odpowiedzialność**: zapewnić developerowi spójny, fluent interfejs dla:

- budowania filtrów,
- deklarowania projekcji (jakie pola pobrać),
- deklarowania sortowania/limitów,
- wykonywania akcji terminalnych.

ORM nie wykonuje „ręcznego sklejania komend”. ORM buduje obiekt zapytania, który jest potem kompilowany w Core i wykonany przez Engine.

#### Główne przestrzenie domenowe (namespaces)

Docelowo `Remote`/`System` eksponuje przestrzenie:

- Filesystem
- Processes
- Services
- Network
- Containers

Każda z nich ma swój model zapytań i akcji, ale korzysta ze wspólnego Engine i wspólnego mechanizmu dialektów.

#### Punkty terminalne i materializacja

ORM powinien rozróżniać:

- operacje „budujące zapytanie” (bez efektów ubocznych),
- operacje „terminalne” (wykonują komendy i powodują materializację wyników lub side effects).

To jest ważne, aby:

- utrzymać przewidywalność,
- umożliwić optymalizacje (push-down),
- ułatwić testowanie.

### Warstwa 4: Escape hatch

To jest element architektury, a nie „wyjątek”.

Escape hatch obejmuje:

- uruchomienie surowej komendy (z pominięciem ORM),
- ręczne dołożenie flag/fragmentów,
- wymuszenie dialektu lub strategii kompilacji,
- dopięcie własnego parsera lub własnej strategii formatowania.

## Implementation Details & Patterns

### 1. Connection Pooling (SSH ControlMaster)
Aby osiągnąć wydajność bliską lokalnej przy pracy zdalnej, Engine wykorzystuje mechanizm **OpenSSH ControlMaster**.
Zamiast nawiązywać nowe połączenie TCP i wykonywać handshake dla każdej komendy (koszt ~300ms+), Engine:
1. Nawiązuje jedno połączenie "Master" w tle, tworząc socket domenowy uniksowy.
2. Kolejne wywołania `execute()` używają tego socketu do multipleksowania sesji (koszt <10ms).
3. Engine zarządza cyklem życia socketu (auto-cleanup, reconnect przy zerwaniu).

### 2. Push-Down Predicates (Visitor Pattern)
Kompilator ORM implementuje wzorzec **Visitor**, który przechodzi przez drzewo wyrażeń filtra (AST) i transformuje je na natywne komendy.
Przykład:
- Filtr: `processes.filter(memory__gt="500MB")`
- Visitor (Linux Dialect): Transformuje to na fragment `awk '$6 > 512000'`.
- Visitor (Windows Dialect): Transformuje to na fragment PowerShell `Where-Object { $_.WS -gt 500MB }`.
To zapewnia, że ciężka filtracja danych odbywa się "blisko danych" (na zdalnym host'cie), a nie w Pythonie.

### 3. Unit of Work & Structured Logging
Każda "akcja terminalna" w ORM (np. `query.delete()`) tworzy logiczny **Unit of Work**.
System logowania śledzi ten kontekst, dzięki czemu w logach widzimy drzewiastą strukturę:
- "Biznesowa" operacja (np. `CleanTmpFiles`)
  - Konkretne zapytanie ORM (`FileSystemQuery`)
    - Wygenerowana komenda Engine (`find /tmp ...`)
      - Wynik surowy
    - Czas parsowania
Dzięki temu logi są czytelne zarówno dla administratora (co system robi?), jak i programisty (dlaczego ta komenda padła?).

## Przepływ danych (od intencji do efektu)

Docelowy przepływ wygląda tak:

- Użytkownik buduje zapytanie w ORM.
- ORM tworzy obiekt zapytania (AST) i trzyma go bez wykonywania.
- W punkcie terminalnym ORM zleca kompilację do Core.
- Kompilator używa dialektu (wybranego na podstawie wykrycia środowiska i wersji narzędzi).
- Engine wykonuje finalną komendę lokalnie lub zdalnie.
- Parser zamienia output na rekordy domenowe.
- ORM zwraca rekordy lub raportuje wynik akcji.

## Dialekty i wykrywanie środowiska

W Mancer 2.0 wykrywanie środowiska nie może być „jednym stringiem”.

Docelowo jest to proces:

- rozpoznanie platformy (Linux/BSD/macOS),
- rozpoznanie narzędzi (GNU vs BusyBox),
- wykrycie wersji kluczowych narzędzi,
- zbudowanie profilu możliwości (capabilities),
- wybór dialektu i strategii kompilacji.

Ważna zasada: użytkownik zawsze może wymusić dialekt ręcznie, gdy wykrycie jest niepewne.

## Model błędów i niezawodność

Ponieważ Mancer operuje na systemie (side effects), model błędów musi być jednoznaczny:

- błąd transportu (brak połączenia, timeout),
- błąd narzędzia (exit code + stderr),
- brak możliwości dialektu (feature nieobsługiwany),
- błąd parsowania (output niezgodny z formatem).

To powinno być mapowane na spójny typ błędu na poziomie domeny (z metadanymi diagnostycznymi), a nie tylko na „string w stderr”.

## Konsekwencje dla API (breaking change)

Mancer 2.0 zakłada, że API może się znacząco zmienić:

- nowy główny „entry point” ukierunkowany na System ORM,
- imperatywne wykonanie poleceń pozostaje jako **oficjalny, wspierany poziom low-level** (Engine/Commands),
- komendy jako klasy mogą pozostać jako część tej ścieżki low-level lub jako element kompatybilności,
- ORM jest docelowym interfejsem „high-level”, ale nie blokuje użycia trybu imperatywnego.
