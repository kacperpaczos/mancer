# Konfiguracja Narzędzi do Lintowania i Sprawdzania Kodu

## Podsumowanie

Projekt Mancer używa następujących narzędzi do kontroli jakości kodu:

### 1. **Ruff** (v0.4.0+)
- Szybki linter i formatter Python
- Sprawdza zgodność z PEP8, wykrywa błędy
- Konfiguracja: `pyproject.toml` → `[tool.ruff]`

### 2. **Black** (v24.3.0+)
- Automatyczne formatowanie kodu
- Konfiguracja: `pyproject.toml` → `[tool.black]`
- Długość linii: 100 znaków

### 3. **isort** (v5.13.0+)
- Sortowanie i grupowanie importów
- Profil: black-compatible
- Konfiguracja: `pyproject.toml` → `[tool.isort]`

### 4. **mypy** (v1.6.0+)
- Statyczne sprawdzanie typów
- Konfiguracja: `pyproject.toml` → `[tool.mypy]`
- Ignoruje brakujące importy: `ignore_missing_imports = true`

### 5. **pytest** (v7.0.0+)
- Framework testowy
- Konfiguracja: `pyproject.toml` → `[tool.pytest.ini_options]`

---

## Pre-commit Hooks (Lokalne Sprawdzanie)

Projekt używa **pre-commit** (odpowiednik Husky dla Python) do automatycznego uruchamiania narzędzi podczas `git commit` i `git push`.

### Instalacja

```bash
# Zainstaluj pre-commit w venv
pip install pre-commit

# Zainstaluj hooki w repozytorium
pre-commit install --install-hooks -t pre-commit -t pre-push
```

### Jak to działa

**Pre-commit (podczas `git commit`):**
- **ruff** - auto-fix błędów lintowania
- **ruff-format** - auto-formatowanie kodu
- **black** - auto-formatowanie kodu
- **isort** - auto-sortowanie importów
- **mypy** - sprawdzanie typów (opcjonalne)

**Pre-push (podczas `git push`):**
- **ruff** - sprawdzenie bez auto-fix (tylko raportowanie)
- **black** - sprawdzenie formatowania (bez zmian)
- **isort** - sprawdzenie sortowania importów (bez zmian)
- **mypy** - sprawdzanie typów (raportowanie błędów, ale nie blokuje push)

### Ręczne Uruchamianie

```bash
# Uruchom wszystkie hooki pre-commit
pre-commit run --all-files

# Uruchom hooki pre-push
pre-commit run --hook-stage pre-push --all-files

# Uruchom konkretny hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

---

## GitHub CI/CD

Te same narzędzia są używane w pipeline CI/CD (`.github/workflows/ci.yml`):

```yaml
- name: Lint with ruff
  run: ruff check src/ tests/

- name: Format check with black
  run: black --check src/ tests/

- name: Import sorting check with isort
  run: isort --check-only src/ tests/

- name: Type check with mypy
  run: mypy src/
```

---

## Konfiguracja w pyproject.toml

### Ruff
```toml
[tool.ruff]
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "I"]  # pycodestyle/pyflakes/isort
ignore = ["E501", "F401", "F841", "E722"]  # ignorowane reguły
```

### Black
```toml
[tool.black]
line-length = 100
target-version = ["py38"]
```

### isort
```toml
[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["mancer"]
```

### mypy
```toml
[tool.mypy]
python_version = "3.8"
ignore_missing_imports = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unreachable = true
strict_optional = true
check_untyped_defs = true
exclude = ["^prototypes/", "^development/"]
```

---

## Zależności Deweloperskie

W `pyproject.toml` dodano sekcję `[project.optional-dependencies]`:

```toml
[project.optional-dependencies]
dev = [
  "ruff>=0.4.0",
  "black>=24.3.0",
  "isort>=5.13.0",
  "mypy>=1.6.0",
  "pre-commit>=3.6.0",
  "types-PyYAML>=6.0.0",
  "types-requests>=2.31.0",
]
```

Instalacja:
```bash
pip install -e ".[dev]"
```

---

## Rozwiązywanie Problemów

### Problem: Pre-commit nie działa
```bash
# Reinstaluj hooki
pre-commit uninstall
pre-commit install --install-hooks -t pre-commit -t pre-push
```

### Problem: Mypy raportuje błędy
- Mypy jest skonfigurowany z `ignore_missing_imports = true`
- Błędy typowania w CI/CD są obecnie raportowane, ale nie blokują merge
- Stopniowo naprawiamy błędy typowania w kodzie

### Problem: Ruff/Black/isort modyfikują pliki
- To normalne zachowanie podczas pre-commit
- Zmiany są automatycznie stagowane
- Sprawdź zmiany przed commitem: `git diff`

---

## Najlepsze Praktyki

1. **Przed commitem:** Uruchom `pre-commit run --all-files` aby sprawdzić wszystkie pliki
2. **Przed pushem:** Uruchom `pre-commit run --hook-stage pre-push --all-files`
3. **Po pull/merge:** Uruchom `pre-commit run --all-files` aby upewnić się, że kod jest zgodny ze standardami
4. **IDE:** Skonfiguruj swoje IDE do używania Black/Ruff podczas zapisywania plików

---

## Status Mypy

⚠️ **Uwaga:** Projekt ma obecnie ~185 błędów typowania mypy. Są one stopniowo naprawiane.

Główne kategorie błędów:
- Brakujące adnotacje typów w niektórych miejscach
- Problemy z TypeVar w metodach generycznych
- Opcjonalne wartości (Optional) wymagające sprawdzenia None
- Niekompatybilne typy w assignmentach

Priorytety napraw:
1. Krytyczne błędy typowania w głównych modułach (wykonane częściowo)
2. Błędy w testach (w trakcie)
3. Błędy w narzędziach pomocniczych (zaplanowane)

---

## Kontakt

W razie pytań lub problemów, otwórz issue na GitHubie.

