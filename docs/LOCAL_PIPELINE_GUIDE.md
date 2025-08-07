# 🚀 **Lokalny Pipeline Testowy - Przewodnik Użytkownika**

## 📋 **Wprowadzenie**

Lokalny pipeline testowy to kompletny system CI/CD działający na Twojej maszynie lokalnej. Symuluje profesjonalne środowisko CI/CD z wszystkimi etapami testowania, od lintingu do E2E testów w Docker.

---

## 🎯 **Dostępne Pipeline'y**

### **1. Pełny Pipeline (Full)**
```bash
./scripts/local_pipeline.sh
```
**Co robi:** Kompletny pipeline - wszystkie etapy w kolejności
**Czas:** ~5-8 minut
**Użyj gdy:** Przed release, po większych zmianach, validation kompletna

### **2. Quick Pipeline (Development)**
```bash
./scripts/quick_pipeline.sh
```
**Co robi:** Szybkie sprawdzenie - lint + unit tests + smoke test
**Czas:** ~30-60 sekund  
**Użyj gdy:** Development workflow, przed commitami, szybka weryfikacja

### **3. Stage Pipeline (Selective)**
```bash
./scripts/pipeline_stage.sh STAGE_NAME
```
**Co robi:** Uruchamia konkretny etap pipeline'u
**Czas:** Zależy od etapu
**Użyj gdy:** Debugging konkretnego problemu, selective testing

---

## 🔧 **Instalacja i Setup**

### **Wymagania:**
```bash
# System requirements
- Linux/macOS
- Docker & Docker Compose
- Python 3.8+
- sudo access (dla Docker operations)

# Sprawdź wymagania:
docker --version
docker-compose --version
python3 --version
```

### **Pierwsza instalacja:**
```bash
# 1. Przejdź do katalogu projektu
cd /path/to/mancer

# 2. Ustaw uprawnienia dla skryptów
chmod +x scripts/*.sh

# 3. Zainstaluj dependencies
pip install -r requirements.txt

# 4. Przetestuj quick pipeline
./scripts/quick_pipeline.sh
```

---

## 🚀 **Użycie Pipeline'ów**

### **A) Full Pipeline - Kompletne testowanie**

#### **Podstawowe użycie:**
```bash
./scripts/local_pipeline.sh
```

#### **Z dodatkowymi opcjami:**
```bash
# Continue nawet jeśli stage fails
./scripts/local_pipeline.sh --continue-on-failure

# Skip konkretny stage
./scripts/local_pipeline.sh --skip-stage lint

# Help
./scripts/local_pipeline.sh --help
```

#### **Co się dzieje krok po kroku:**
```
🔧 SETUP           → Install dependencies, verify environment
🔍 LINT             → Code quality (flake8, black, isort)  
🧪 UNIT TESTS       → Unit tests + coverage report
🐳 BUILD DOCKER     → Docker containers + network setup
🔗 INTEGRATION      → Integration tests w Docker
🎯 E2E TESTS        → End-to-end scenarios
📊 COVERAGE         → Combined coverage report
⚡ PERFORMANCE      → Performance benchmarks
🔒 SECURITY         → Security vulnerability scan
📦 ARTIFACTS        → Generate reports and artifacts
🧹 CLEANUP          → Clean up Docker environment
```

### **B) Quick Pipeline - Development workflow**

#### **Codziennie podczas development:**
```bash
# Przed każdym commitem
./scripts/quick_pipeline.sh

# Jeśli wszystko OK:
git add .
git commit -m "feature: new functionality"

# Jeśli są problemy - napraw i powtórz
```

#### **Co sprawdza:**
- ✅ **Lint check** - Code quality issues
- ✅ **Unit tests** - Core functionality
- ✅ **Smoke test** - Framework imports & basic execution
- ✅ **Security check** - Basic security patterns

### **C) Stage Pipeline - Selective testing**

#### **Lista dostępnych stages:**
```bash
./scripts/pipeline_stage.sh --list

# Output:
setup                Setup environment and install dependencies
lint                 Code quality analysis (flake8, black, isort)
unit_tests           Run unit tests with coverage
build_docker         Build and start Docker test environment
integration_tests    Run integration tests in Docker
e2e_tests            Run end-to-end tests
coverage_report      Generate combined coverage report
performance_tests    Run performance benchmarks
security_scan        Security vulnerability scanning
cleanup              Clean up Docker environment and temp files
```

#### **Uruchamianie konkretnych stages:**
```bash
# Tylko unit tests
./scripts/pipeline_stage.sh unit_tests

# Tylko build Docker environment
./scripts/pipeline_stage.sh build_docker --verbose

# Tylko linting
./scripts/pipeline_stage.sh lint

# Coverage report
./scripts/pipeline_stage.sh coverage_report
```

---

## 📊 **Interpretacja Wyników**

### **Status Codes i Znaczenie:**

| Status | Znaczenie | Action |
|--------|-----------|--------|
| ✅ **SUCCESS** | Wszystko OK | Continue development |
| ⚠️ **WARNING** | Issues ale nie critical | Review warnings, może fix |
| ❌ **FAILED** | Critical issues | **MUST FIX** przed continue |

### **Quality Gates - Minimalne wymagania:**

```yaml
✅ Unit Test Coverage: ≥80%        # Przynajmniej 80% pokrycia kodu
✅ Lint Issues: ≤5                 # Maksymalnie 5 lint problemów  
✅ Security Issues: 0              # Zero znanych vulnerabilities
✅ Performance: ≤100ms avg         # Średni czas wykonania komend
```

### **Lokalizacja wyników:**
```
pipeline/
├── reports/                    # 📊 Wszystkie raporty
│   ├── coverage_combined/      # HTML coverage report
│   ├── unit_tests.xml         # Unit test results (JUnit)
│   ├── integration_tests.xml  # Integration test results
│   ├── lint_report.txt        # Linting issues
│   ├── security_report.txt    # Security scan results
│   └── performance_results.json # Performance benchmarks
├── logs/                       # 📋 Logi wykonania
│   ├── pipeline.log           # Master pipeline log
│   ├── unit_tests.log         # Unit tests output
│   ├── docker_build.log       # Docker build log
│   └── integration_tests.log  # Integration tests output
└── artifacts/                  # 📦 Artefakty
    ├── pipeline_summary.json  # Pipeline execution summary
    ├── pipeline_report.html   # HTML report
    └── pipeline_artifacts.tar.gz # Archived results
```

---

## 🛠️ **Development Workflows**

### **Workflow 1: Feature Development**
```bash
# 1. Start development
git checkout -b feature/new-command

# 2. Make changes to code
vim src/mancer/infrastructure/command/...

# 3. Quick check during development
./scripts/quick_pipeline.sh

# 4. If OK, continue development
# If issues, fix and repeat step 3

# 5. Before finishing feature
./scripts/local_pipeline.sh

# 6. If full pipeline passes
git add .
git commit -m "feature: implement new command"
git push origin feature/new-command
```

### **Workflow 2: Bug Fixing**
```bash
# 1. Reproduce bug
./scripts/pipeline_stage.sh unit_tests  # See if tests catch it

# 2. Write test that reproduces bug
vim tests/unit/test_new_bug.py

# 3. Verify test fails
./scripts/pipeline_stage.sh unit_tests

# 4. Fix the bug
vim src/mancer/...

# 5. Verify fix
./scripts/pipeline_stage.sh unit_tests  # Should pass now

# 6. Full validation
./scripts/local_pipeline.sh
```

### **Workflow 3: Refactoring**
```bash
# 1. Baseline - ensure all tests pass
./scripts/local_pipeline.sh

# 2. Make refactoring changes
vim src/mancer/...

# 3. Quick check
./scripts/quick_pipeline.sh

# 4. If unit tests pass, run integration
./scripts/pipeline_stage.sh integration_tests

# 5. Full validation
./scripts/local_pipeline.sh
```

---

## 🔧 **Debugging Pipeline Issues**

### **Problem: Unit tests fail**
```bash
# 1. Run tylko unit tests z verbose
./scripts/pipeline_stage.sh unit_tests --verbose

# 2. Check test output
cat pipeline/logs/unit_tests.log

# 3. Run specific failing test
pytest tests/unit/test_specific.py::test_failing_method -v

# 4. Fix and retest
./scripts/pipeline_stage.sh unit_tests
```

### **Problem: Docker nie startuje**
```bash
# 1. Check Docker daemon
sudo systemctl status docker

# 2. Manual Docker test
cd development/docker_test
sudo ./start_test.sh

# 3. If Docker issues, clean and rebuild
sudo ./cleanup.sh
./scripts/pipeline_stage.sh build_docker --verbose

# 4. Check Docker logs
docker-compose logs
```

### **Problem: Integration tests fail**
```bash
# 1. Ensure Docker environment is running
./scripts/pipeline_stage.sh build_docker

# 2. Test Docker connectivity manually
docker exec mancer-test-1 echo "test"

# 3. Run integration tests with verbose
./scripts/pipeline_stage.sh integration_tests --verbose

# 4. Check framework installation in container
docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.application.shell_runner import ShellRunner
print('Framework OK')
"
```

### **Problem: Performance tests fail**
```bash
# 1. Run performance tests isolated
./scripts/pipeline_stage.sh performance_tests --verbose

# 2. Check system load
top
free -h

# 3. Profile individual commands
python3 -c "
import time
import sys
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type='bash')
start = time.time()
result = runner.execute(runner.create_command('echo').text('test'))
print(f'Time: {(time.time() - start) * 1000:.2f}ms')
"
```

---

## 📈 **Optymalizacja i Tuning**

### **Szybsze uruchamianie:**
```bash
# Use specific stages tylko dla changed areas
git diff --name-only | grep "^src/" && ./scripts/pipeline_stage.sh unit_tests
git diff --name-only | grep "^tests/" && ./scripts/quick_pipeline.sh

# Skip Docker rebuild if not needed
./scripts/local_pipeline.sh --skip-stage build_docker  # (jeśli Docker już działa)
```

### **Parallel testing:**
```bash
# Unit tests w parallel (jeśli pytest-xdist installed)
pytest tests/unit/ -n auto

# Multiple pipeline stages można uruchomić w parallel w separate terminals:
# Terminal 1:
./scripts/pipeline_stage.sh lint

# Terminal 2: 
./scripts/pipeline_stage.sh unit_tests

# Terminal 3:
./scripts/pipeline_stage.sh security_scan
```

### **Resource optimization:**
```bash
# Limit Docker resources in pipeline/config/pipeline.yaml:
docker:
  resources:
    memory: "256m"      # Reduce if needed
    cpu: "0.5"          # Reduce if needed
```

---

## 🎯 **Best Practices**

### **Daily Development:**
1. **Start each day:** `./scripts/quick_pipeline.sh`
2. **Before each commit:** `./scripts/quick_pipeline.sh`
3. **After major changes:** `./scripts/local_pipeline.sh`
4. **Before push:** `./scripts/local_pipeline.sh`

### **Quality Maintenance:**
1. **Monitor coverage:** Ensure nie spada poniżej 80%
2. **Fix lint issues:** Don't accumulate technical debt
3. **Performance watching:** Monitor command execution times
4. **Security updates:** Regular dependency updates

### **Troubleshooting:**
1. **Start simple:** Quick pipeline first, then full
2. **Isolate issues:** Use stage pipeline do identify problems
3. **Check logs:** Always check pipeline logs dla details
4. **Clean environment:** When in doubt, cleanup and rebuild

---

## 🆘 **FAQ**

### **Q: Pipeline jest wolny, jak przyspieszyć?**
A: 
```bash
# Use quick pipeline dla development
./scripts/quick_pipeline.sh

# Skip unnecessary stages
./scripts/local_pipeline.sh --skip-stage security_scan

# Use stage pipeline dla specific areas
./scripts/pipeline_stage.sh unit_tests
```

### **Q: Docker nie startuje, co robić?**
A:
```bash
# 1. Check Docker service
sudo systemctl status docker

# 2. Clean environment
cd development/docker_test
sudo ./cleanup.sh

# 3. Manual start
sudo ./start_test.sh

# 4. Check permissions
sudo usermod -aG docker $USER
newgrp docker
```

### **Q: Testy unit przechodzą ale integration fail?**
A:
```bash
# 1. Check framework installation w container
docker exec mancer-test-1 python3 -c "import sys; sys.path.append('/home/mancer1/mancer/src'); import mancer"

# 2. Check container logs
docker logs mancer-test-1

# 3. Manual test in container
docker exec -it mancer-test-1 bash
cd /home/mancer1/mancer
python3 -c "from src.mancer.application.shell_runner import ShellRunner; print('OK')"
```

### **Q: Jak dodać nowy stage do pipeline'u?**
A:
1. Dodaj stage function w `scripts/local_pipeline.sh`
2. Dodaj stage name w `PIPELINE_STAGES` array
3. Dodaj implementation w `scripts/pipeline_stage.sh`  
4. Update configuration w `pipeline/config/pipeline.yaml`
5. Test new stage: `./scripts/pipeline_stage.sh your_new_stage`

---

## 🎉 **Podsumowanie**

**Lokalny Pipeline Testowy daje Ci:**
- ✅ **Professional CI/CD** na lokalnej maszynie
- ✅ **Quality gates** - Automated quality control
- ✅ **Fast feedback** - Quick pipeline dla development
- ✅ **Comprehensive testing** - Unit → Integration → E2E
- ✅ **Docker isolation** - Testowanie w clean environments
- ✅ **Detailed reporting** - Coverage, performance, security
- ✅ **Flexible execution** - Full, quick, lub selective stages

**Start developing z confidence! 🚀** 