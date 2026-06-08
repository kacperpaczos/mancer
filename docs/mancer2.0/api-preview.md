# Mancer 2.0 API Preview & Implementation Details

Ten dokument przedstawia **konkretne przykłady kodu** (Developer Experience) dla nadchodzącej wersji Mancer 2.0. Pokazuje dwa wspierane style pracy oraz detale implementacyjne inspirowane sprawdzonymi rozwiązaniami (SQLAlchemy, Django).

## 1. Dual API: Porównanie stylów

Mancer 2.0 wspiera oba style. Programista wybiera narzędzie odpowiednie do problemu.

### Scenariusz: "Znajdź i zabij procesy 'node', które zużywają >500MB RAM"

#### A. Styl Imperatywny (Low-Level / Engine API)
*Dla precyzyjnej kontroli nad potokami i flagami, ale z użyciem obiektów (Builder Pattern).*

```python
from mancer.core import Engine, LocalEngine
from mancer.commands import Ps, Awk, Kill

# 1. Inicjalizacja silnika
engine = LocalEngine()

# 2. Budowanie komendy obiektami (Builder Pattern)
# Zamiast sklejać stringi, używamy łańcucha obiektów.
# Engine automatycznie skompiluje to do: "ps aux | awk '...'"
cmd = (
    Ps()
    .flags("-aux")  # lub .all_users() jeśli komenda ma helpery
    .pipe(
        Awk('$6 > 512000 && /node/ {print $2}')
    )
)

# 3. Wykonanie (Engine przyjmuje obiekt komendy)
result = engine.execute(cmd)

if result.failed:
    print(f"Błąd komendy: {result.stderr}")
    exit(1)

# 4. Ręczne parsowanie i iteracja
pids = result.stdout.strip().split('\n')
for pid in pids:
    if not pid: continue
    
    # 5. Wykonanie akcji (kolejny obiekt Buildera)
    # kill -9 <pid>
    kill_cmd = Kill(pid).signal(9)
    res = engine.execute(kill_cmd)
    
    if res.success:
        print(f"Zabito PID {pid}")
```

**Cechy:**
- **Builder Pattern**: Metody `.flags()`, `.pipe()`, `.signal()` zamiast ręcznego formatowania stringów.
- **Bezpieczeństwo**: Automatyczne escapowanie argumentów (np. w `Kill(pid)`).
- **Kontrola**: Programista decyduje dokładnie jakie flagi (`-aux`) są użyte, w przeciwieństwie do ORM, który sam je dobiera.

#### B. Styl Deklaratywny (System ORM)
*Dla złożonej logiki biznesowej, czytelności i przenośności.*

```python
from mancer.orm import System

# 1. Inicjalizacja (automatyczne wykrycie dialektu)
system = System.localhost()

# 2. Budowanie zapytania (Lazy Evaluation - nic się jeszcze nie wykonuje)
# ORM sam dobierze odpowiednie polecenie 'ps' i flagi dla danego OS
query = system.processes.filter(
    name__contains="node",
    memory_rss__gt="500MB"
)

# 3. Wykonanie akcji (Terminal Operation)
# To tutaj następuje kompilacja do shella i wykonanie
killed_count = query.kill(signal=9)

print(f"Zabito {killed_count} procesów")
```

**Co dzieje się pod spodem (ORM):**
1. **Kompilacja**: ORM tłumaczy filtry na: `ps -eo pid,rss,comm | awk ...` (dla Linux) lub `ps -ax -o ...` (dla BSD).
2. **Push-down**: Filtrowanie po pamięci i nazwie odbywa się w `awk` (na zdalnej maszynie), Python dostaje tylko listę PID do zabicia.
3. **Execution**: Engine wykonuje optymalną sekwencję.

---

## 2. Nowy System Logowania (Structured Logging)

Mancer 2.0 wprowadza logowanie kontekstowe, inspirowane `structlog`. Logi są czytelne dla człowieka i maszyny.

### Stare logi (v0.x - szum informacyjny)
```text
[INFO] Executing command: ssh user@host 'ps aux | grep node'
[DEBUG] Output received: root 1234 0.5 1.2 ...
[INFO] Command finished successfully
[INFO] Executing command: ssh user@host 'kill -9 1234'
[INFO] Command finished successfully
```

### Nowe logi (v2.0 - kontekst i struktura)
Logi grupują operacje w logiczne jednostki pracy (Unit of Work).

```text
[INFO] [System.localhost] ProcessQuery.kill started
       ├── filters: {name__contains="node", memory_rss__gt="500MB"}
       ├── signal: 9
       │
       ├── [Engine] Executing: ps -eo pid,rss,comm | awk '$2 > 512000 && $3 ~ /node/ {print $1}'
       │   └── Result: 2 PIDs found (duration: 0.01s)
       │
       ├── [Engine] Executing: kill -9 1234 5678
       │   └── Result: Exit 0 (success)
       │
       └── Completed: 2 processes killed (total_duration: 0.05s)
```

**Cechy:**
- **Drzewiasta struktura**: widać, która operacja ORM wywołała które komendy Engine.
- **Parametryzacja**: loguje intencję (`filters`), a nie tylko surowe stringi.
- **Timing**: czasy wykonania na każdym poziomie.

---

## 3. Szczegóły Implementacyjne (Building Blocks)

Jak zbudować taki system? Oto konkretne wzorce projektowe.

### A. Definicja Modelu (Schema Definition)
Wzorowane na `pydantic` i `SQLAlchemy`. Definiujemy, jak mapować wyjście komendy na obiekt Pythona.

```python
from mancer.core.schema import Schema, Field

class Process(Schema):
    pid: int = Field(source="pid")
    name: str = Field(source="comm")
    memory: int = Field(source="rss", unit="KB")
    user: str = Field(source="user")

    class Meta:
        # Definicja, jak pobrać dane w różnych dialektach
        sources = {
            "linux": "ps -eo pid,rss,user,comm",
            "bsd": "ps -ax -o pid,rss,user,comm",
            "busybox": "ps -o pid,rss,user,comm"
        }
```

### B. Kompilator Zapytań (Visitor Pattern)
Wzorzec Visitor do zamiany drzewa filtrów na string komendy (np. `awk`).

```python
class AwkCompiler:
    def compile(self, query):
        conditions = []
        for filter in query.filters:
            if filter.field == "memory_rss":
                # Konwersja 500MB -> 512000 KB
                val = convert_to_kb(filter.value)
                conditions.append(f"${self.col_map['rss']} > {val}")
            
            elif filter.field == "name":
                conditions.append(f"${self.col_map['comm']} ~ /{filter.value}/")
        
        # Złożenie warunków
        awk_cond = " && ".join(conditions)
        return f"awk '{awk_cond} {{print $1}}'"
```

### C. Engine & Connection Pooling
Wzorzec Pool dla SSH, aby uniknąć kosztu handshake (podobnie jak baza danych).

```python
class SSHEngine(Engine):
    def __init__(self, host, ...):
        # ControlMaster socket path
        self._socket = f"/tmp/mancer_ssh_{hash(host)}.sock"
    
    def connect(self):
        # Uruchomienie Master procesu (background)
        subprocess.Popen(f"ssh -M -S {self._socket} -fN {self.host} ...")
    
    def execute(self, cmd):
        # Wykonanie przez istniejący socket (błyskawiczne)
        return subprocess.run(f"ssh -S {self._socket} {self.host} {cmd}")
```

### D. Lazy Evaluation (Generator Pattern)
Zapytanie nie wykonuje się przy definicji, tylko przy iteracji.

```python
class Query:
    def __init__(self, ...):
        self._filters = []
        self._cache = None

    def filter(self, **kwargs):
        # Tylko dodaje do listy, zwraca nowe zapytanie (Immutable)
        new_q = self.clone()
        new_q._filters.append(kwargs)
        return new_q

    def __iter__(self):
        # Dopiero tutaj następuje kompilacja i wykonanie
        if self._cache is None:
            cmd = self.compiler.compile(self)
            raw_data = self.engine.execute(cmd)
            self._cache = self.parser.parse(raw_data)
        
        return iter(self._cache)
```
