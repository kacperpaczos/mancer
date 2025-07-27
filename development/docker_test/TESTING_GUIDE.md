# 🧪 Przewodnik Testowania Custom Aplikacji w Docker

## Szybki Start

### 1. Przygotowanie środowiska
```bash
# Przejdź do katalogu testowego
cd development/docker_test

# Uruchom środowisko Docker
sudo ./start_test.sh

# Zainstaluj zależności testowe (jeśli nie ma)
pip install pytest pytest-docker-compose pytest-xdist paramiko
```

### 2. Uruchamianie testów

#### Wszystkie testy automatyczne:
```bash
./run_automated_tests.sh
```

#### Przykład testowania custom aplikacji:
```bash
cd ../..
python3 examples/docker_testing_example.py
```

#### Specyficzne testy:
```bash
# Test tylko SSH connectivity
pytest tests/integration/test_bash_commands.py::TestMancerDockerIntegration::test_ssh_connectivity -v

# Test prototypów
pytest tests/integration/test_bash_commands.py::TestMancerPrototypes -v

# Test z pełnymi detalami
pytest tests/integration/ -v --tb=long --capture=no
```

## Jak testować własne aplikacje

### 1. Użyj MancerTestUtils
```python
from tests.integration.test_utils import MancerTestUtils

# Sprawdź instalację Mancer
validation = MancerTestUtils.validate_mancer_installation(ssh_client)

# Uruchom aplikację i zbierz wyniki
stdout, stderr, exit_code = MancerTestUtils.execute_mancer_app(
    ssh_client, 
    "prototypes/twoja_aplikacja", 
    ["--param", "value"]
)

# Zbierz metryki wydajności
metrics = MancerTestUtils.collect_app_metrics(ssh_client, "twoja_aplikacja")
```

### 2. Struktura testu
```python
def test_custom_application(ssh_connection):
    """Test Twojej custom aplikacji"""
    
    # 1. Przygotuj środowisko testowe
    sftp = ssh_connection.open_sftp()
    
    # 2. Uruchom aplikację
    stdin, stdout, stderr = ssh_connection.exec_command(
        'cd /home/mancer1/mancer/prototypes/twoja_app && python3 main.py'
    )
    
    # 3. Zbierz wyniki
    output = stdout.read().decode()
    
    # 4. Sprawdź oczekiwane rezultaty
    assert "expected_result" in output
    
    # 5. Zbierz metryki (opcjonalnie)
    metrics = MancerTestUtils.collect_app_metrics(ssh_connection, "twoja_app")
    
    # 6. Zapisz wyniki
    results = {"output": output, "metrics": metrics}
    MancerTestUtils.save_test_results(results, "twoja_app_results.json")
```

## Dostępne kontenery testowe

- **mancer-test-1** (port 2221): Główny kontener testowy
- **mancer-test-2** (port 2222): Drugi kontener dla testów multi-container
- **mancer-test-3** (port 2223): Trzeci kontener dla testów distributed

## Najczęstsze problemy

### Problem: SSH timeout
**Rozwiązanie:**
```bash
# Sprawdź czy kontenery działają
docker ps --filter name=mancer-test

# Restartuj środowisko
sudo ./cleanup.sh
sudo ./start_test.sh
```

### Problem: Brak modułów Python
**Rozwiązanie:**
```bash
# Zaloguj się do kontenera i zainstaluj
ssh mancer1@localhost -p 2221
pip3 install --user nazwa_modulu
```

### Problem: Błędy importu Mancer
**Rozwiązanie:**
```python
# W testach użyj pełnej ścieżki
sys.path.append("/home/mancer1/mancer/src")
```

## Wyniki testów

### Lokalizacje plików wyników:
- **HTML Coverage**: `htmlcov/index.html`
- **JUnit XML**: `test_results.xml`
- **JSON Results**: `logs/*.json`

### Przykład analizy wyników:
```python
import json

# Wczytaj wyniki
with open('logs/test_results.json') as f:
    results = json.load(f)

# Analizuj metryki
for test in results['tests']:
    print(f"Test: {test['test_name']}")
    print(f"Status: {test['status']}")
    print(f"Czas: {test['timestamp']}")
```

## Best Practices

1. **Czyść środowisko** przed każdym testem
2. **Używaj fixtures** dla powtarzalnych setup'ów
3. **Zbieraj metryki** dla analizy wydajności
4. **Dokumentuj testy** - dodawaj docstringi
5. **Testuj edge cases** - nie tylko happy path

## Integracja z CI/CD

```yaml
# .github/workflows/docker-tests.yml
name: Docker Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Docker Tests
        run: |
          cd development/docker_test
          sudo ./run_automated_tests.sh
``` 