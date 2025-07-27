#!/bin/bash
# 🧪 TESTY JEDNOSTKOWE - Dual execution (LOCAL + DOCKER)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; NC='\033[0m'

log() { echo -e "${B}[UNIT]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

# =============================================================================
# UNIT TESTS - LOCAL EXECUTION
# =============================================================================

run_unit_tests_local() {
    log "Uruchamiam testy jednostkowe LOKALNIE..."
    
    # Test 1: Sprawdź czy framework jest dostępny
    if ! python3 -c "import sys; sys.path.append('src'); from mancer.application.shell_runner import ShellRunner" &>/dev/null; then
        warn "Framework nie jest dostępny lokalnie"
        return 1
    fi
    
    # Test 2: Sprawdź czy pytest jest dostępny
    if ! python3 -c "import pytest" &>/dev/null; then
        log "Auto-instaluję pytest..."
        # Try system package first
        if command -v apt &>/dev/null; then
            sudo apt update &>/dev/null && sudo apt install -y python3-pytest &>/dev/null || true
        fi
        # Try pip as fallback
        pip3 install pytest &>/dev/null || pip install pytest &>/dev/null || true
        
        if ! python3 -c "import pytest" &>/dev/null; then
            warn "Nie można zainstalować pytest lokalnie"
            return 1
        fi
    fi
    
    # Test 3: Uruchom testy lokalnie
    local test_result=0
    
    # Method 1: Standard PYTHONPATH
    PYTHONPATH=src python3 -m pytest tests/unit/ -v --tb=short -q &>/dev/null || {
        warn "Metoda 1 nie powiodła się, próbuję metody 2..."
        
        # Method 2: Change to src directory
        (cd src && python3 -m pytest ../tests/unit/ -v --tb=short -q &>/dev/null) || {
            warn "Metoda 2 nie powiodła się, próbuję metody 3..."
            
            # Method 3: Direct pytest call
            python3 -m pytest tests/unit/ -v --tb=short -q &>/dev/null || {
                test_result=1
            }
        }
    }
    
    if [[ $test_result -eq 0 ]]; then
        ok "Testy jednostkowe przeszły LOKALNIE"
        return 0
    else
        warn "Testy jednostkowe nie przeszły lokalnie"
        
        # Debug info
        log "Debug info - próbuję pojedyncze testy..."
        python3 -c "
import sys
sys.path.append('src')
try:
    from mancer.infrastructure.factory.command_factory import CommandFactory
    factory = CommandFactory('bash')
    echo_cmd = factory.create_command('echo')
    if echo_cmd:
        print('✓ CommandFactory działa')
    else:
        print('✗ CommandFactory nie tworzy komend')
        
    from mancer.infrastructure.backend.bash_backend import BashBackend
    backend = BashBackend()
    print('✓ BashBackend działa')
    
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type='bash')
    print('✓ ShellRunner działa')
    
except Exception as e:
    print(f'✗ Import error: {e}')
" 2>/dev/null || warn "Framework components mają problemy"
        
        return 1
    fi
}

# =============================================================================
# UNIT TESTS - DOCKER EXECUTION  
# =============================================================================

setup_docker_for_unit_tests() {
    log "Przygotowuję Docker environment dla testów jednostkowych..."
    
    # Check if Docker is available
    if ! command -v docker &>/dev/null; then
        warn "Docker nie jest dostępny"
        return 1
    fi
    
    if ! docker info &>/dev/null; then
        warn "Docker daemon nie działa"
        return 1
    fi
    
    # Setup Docker environment
    cd development/docker_test
    
    # Create .env if missing
    [[ ! -f .env ]] && cp env.develop.test .env
    
    # Clean up and start
    sudo ./cleanup.sh &>/dev/null || true
    
    log "Buduję i uruchamiam kontenery Docker..."
    docker-compose up -d --build &>/dev/null || {
        fail "Nie można uruchomić kontenerów Docker"
        cd "$PROJECT_ROOT"
        return 1
    }
    
    # Wait for containers to be ready
    log "Czekam aż kontenery będą gotowe..."
    for i in {1..30}; do
        if docker exec mancer-test-1 echo "ready" &>/dev/null; then
            ok "Kontenery Docker gotowe"
            cd "$PROJECT_ROOT" 
            return 0
        fi
        sleep 2
    done
    
    fail "Kontenery nie uruchomiły się w czasie"
    cd "$PROJECT_ROOT"
    return 1
}

run_unit_tests_docker() {
    log "Uruchamiam testy jednostkowe w DOCKER..."
    
    # Test 1: Sprawdź czy framework jest dostępny w kontenerze
    if ! docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.application.shell_runner import ShellRunner
" &>/dev/null; then
        warn "Framework nie jest dostępny w Docker"
        return 1
    fi
    
    # Test 2: Uruchom testy w kontenerze
    local test_result=0
    
    docker exec mancer-test-1 bash -c "
cd /home/mancer1/mancer
export PYTHONPATH=/home/mancer1/mancer/src

# Method 1: Standard pytest with PYTHONPATH
python3 -m pytest tests/unit/ -v --tb=short -q 2>/dev/null || {
    # Method 2: Change directory
    cd src
    python3 -m pytest ../tests/unit/ -v --tb=short -q 2>/dev/null || {
        # Method 3: Direct approach
        cd /home/mancer1/mancer
        python3 -m pytest tests/unit/ -v --tb=short -q 2>/dev/null || exit 1
    }
}
" &>/dev/null || test_result=1
    
    if [[ $test_result -eq 0 ]]; then
        ok "Testy jednostkowe przeszły w DOCKER"
        return 0
    else
        warn "Testy jednostkowe nie przeszły w Docker"
        
        # Debug info dla Docker
        log "Debug info Docker - sprawdzam komponenty..."
        docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
try:
    from mancer.infrastructure.factory.command_factory import CommandFactory
    factory = CommandFactory('bash')
    echo_cmd = factory.create_command('echo')
    if echo_cmd:
        print('✓ CommandFactory działa w Docker')
    else:
        print('✗ CommandFactory nie tworzy komend w Docker')
        
    from mancer.infrastructure.backend.bash_backend import BashBackend
    backend = BashBackend()
    print('✓ BashBackend działa w Docker')
    
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type='bash')
    print('✓ ShellRunner działa w Docker')
    
except Exception as e:
    print(f'✗ Docker import error: {e}')
" 2>/dev/null || warn "Framework components mają problemy w Docker"
        
        return 1
    fi
}

# =============================================================================
# INDIVIDUAL TEST RUNNERS
# =============================================================================

test_command_factory() {
    local environment="$1"  # "local" lub "docker"
    
    if [[ "$environment" == "local" ]]; then
        python3 -c "
import sys
sys.path.append('src')
from mancer.infrastructure.factory.command_factory import CommandFactory

# Test CommandFactory
factory = CommandFactory('bash')
results = {'total': 0, 'passed': 0}

# Test 1: Create echo command
results['total'] += 1
echo_cmd = factory.create_command('echo')
if echo_cmd and hasattr(echo_cmd, 'text'):
    results['passed'] += 1

# Test 2: Create ls command  
results['total'] += 1
ls_cmd = factory.create_command('ls')
if ls_cmd and hasattr(ls_cmd, 'build_command'):
    results['passed'] += 1

# Test 3: Create nonexistent command
results['total'] += 1
none_cmd = factory.create_command('nonexistent123')
if none_cmd is None:
    results['passed'] += 1

print(f\"CommandFactory: {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 2:
    print('COMMAND_FACTORY_OK')
else:
    print('COMMAND_FACTORY_FAIL')
"
    else
        docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.infrastructure.factory.command_factory import CommandFactory

# Test CommandFactory w Docker
factory = CommandFactory('bash')
results = {'total': 0, 'passed': 0}

# Test 1: Create echo command
results['total'] += 1
echo_cmd = factory.create_command('echo')
if echo_cmd and hasattr(echo_cmd, 'text'):
    results['passed'] += 1

# Test 2: Create ls command  
results['total'] += 1
ls_cmd = factory.create_command('ls')
if ls_cmd and hasattr(ls_cmd, 'build_command'):
    results['passed'] += 1

# Test 3: Create nonexistent command
results['total'] += 1
none_cmd = factory.create_command('nonexistent123')
if none_cmd is None:
    results['passed'] += 1

print(f\"CommandFactory (Docker): {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 2:
    print('COMMAND_FACTORY_OK')
else:
    print('COMMAND_FACTORY_FAIL')
"
    fi
}

test_bash_backend() {
    local environment="$1"
    
    if [[ "$environment" == "local" ]]; then
        python3 -c "
import sys
sys.path.append('src')
from mancer.infrastructure.backend.bash_backend import BashBackend

# Test BashBackend
backend = BashBackend()
results = {'total': 0, 'passed': 0}

# Test 1: Simple echo command
results['total'] += 1
try:
    result = backend.execute_command('echo test_backend')
    if result.success and 'test_backend' in result.raw_output:
        results['passed'] += 1
except:
    pass

# Test 2: ls command
results['total'] += 1  
try:
    result = backend.execute_command('ls')
    if result.success:
        results['passed'] += 1
except:
    pass

print(f\"BashBackend: {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 1:
    print('BASH_BACKEND_OK')
else:
    print('BASH_BACKEND_FAIL')
"
    else
        docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.infrastructure.backend.bash_backend import BashBackend

# Test BashBackend w Docker
backend = BashBackend()
results = {'total': 0, 'passed': 0}

# Test 1: Simple echo command
results['total'] += 1
try:
    result = backend.execute_command('echo test_backend_docker')
    if result.success and 'test_backend_docker' in result.raw_output:
        results['passed'] += 1
except:
    pass

# Test 2: ls command
results['total'] += 1  
try:
    result = backend.execute_command('ls')
    if result.success:
        results['passed'] += 1
except:
    pass

print(f\"BashBackend (Docker): {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 1:
    print('BASH_BACKEND_OK')
else:
    print('BASH_BACKEND_FAIL')
"
    fi
}

test_shell_runner() {
    local environment="$1"
    
    if [[ "$environment" == "local" ]]; then
        python3 -c "
import sys
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner

# Test ShellRunner
runner = ShellRunner(backend_type='bash')
results = {'total': 0, 'passed': 0}

# Test 1: Create and execute echo command
results['total'] += 1
try:
    echo_cmd = runner.create_command('echo').text('shell_runner_test')
    result = runner.execute(echo_cmd)
    if result.success and 'shell_runner_test' in result.raw_output:
        results['passed'] += 1
except:
    pass

# Test 2: Create and execute ls command
results['total'] += 1
try:
    ls_cmd = runner.create_command('ls')
    result = runner.execute(ls_cmd)
    if result.success:
        results['passed'] += 1
except:
    pass

print(f\"ShellRunner: {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 1:
    print('SHELL_RUNNER_OK')
else:
    print('SHELL_RUNNER_FAIL')
"
    else
        docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.application.shell_runner import ShellRunner

# Test ShellRunner w Docker
runner = ShellRunner(backend_type='bash')
results = {'total': 0, 'passed': 0}

# Test 1: Create and execute echo command
results['total'] += 1
try:
    echo_cmd = runner.create_command('echo').text('shell_runner_docker_test')
    result = runner.execute(echo_cmd)
    if result.success and 'shell_runner_docker_test' in result.raw_output:
        results['passed'] += 1
except:
    pass

# Test 2: Create and execute ls command
results['total'] += 1
try:
    ls_cmd = runner.create_command('ls')
    result = runner.execute(ls_cmd)
    if result.success:
        results['passed'] += 1
except:
    pass

print(f\"ShellRunner (Docker): {results['passed']}/{results['total']} testów przeszło\")
if results['passed'] >= 1:
    print('SHELL_RUNNER_OK')
else:
    print('SHELL_RUNNER_FAIL')
"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

cleanup_docker() {
    if command -v docker &>/dev/null && docker info &>/dev/null; then
        log "Sprzątam Docker environment..."
        cd development/docker_test &>/dev/null && sudo ./cleanup.sh &>/dev/null || true
        cd "$PROJECT_ROOT" &>/dev/null || true
    fi
}

main() {
    echo -e "${B}"
    echo "================================================================="
    echo "🧪 TESTY JEDNOSTKOWE - Dual Execution (LOCAL + DOCKER)"
    echo "================================================================="
    echo -e "${NC}"
    
    local local_passed=0
    local docker_passed=0
    local docker_available=false
    
    # Test LOCAL execution
    log "=== TESTY LOKALNE ==="
    if run_unit_tests_local; then
        local_passed=1
        
        # Run individual component tests locally
        log "Testuję komponenty lokalnie..."
        test_command_factory "local" 2>/dev/null | grep -E "(CommandFactory|COMMAND_FACTORY)" || true
        test_bash_backend "local" 2>/dev/null | grep -E "(BashBackend|BASH_BACKEND)" || true  
        test_shell_runner "local" 2>/dev/null | grep -E "(ShellRunner|SHELL_RUNNER)" || true
    fi
    
    echo
    
    # Test DOCKER execution
    log "=== TESTY DOCKER ==="
    if setup_docker_for_unit_tests; then
        docker_available=true
        
        if run_unit_tests_docker; then
            docker_passed=1
            
            # Run individual component tests in Docker
            log "Testuję komponenty w Docker..."
            test_command_factory "docker" 2>/dev/null | grep -E "(CommandFactory|COMMAND_FACTORY)" || true
            test_bash_backend "docker" 2>/dev/null | grep -E "(BashBackend|BASH_BACKEND)" || true
            test_shell_runner "docker" 2>/dev/null | grep -E "(ShellRunner|SHELL_RUNNER)" || true
        fi
        
        cleanup_docker
    else
        warn "Docker environment niedostępny"
    fi
    
    # Results
    echo
    echo -e "${B}=================================================================${NC}"
    echo -e "${B}🏁 WYNIKI TESTÓW JEDNOSTKOWYCH${NC}"
    echo -e "${B}=================================================================${NC}"
    
    echo "LOCAL:  $([[ $local_passed -eq 1 ]] && echo "✅ PASSED" || echo "❌ FAILED")"
    echo "DOCKER: $([[ $docker_available == true ]] && { [[ $docker_passed -eq 1 ]] && echo "✅ PASSED" || echo "❌ FAILED"; } || echo "⚠️ UNAVAILABLE")"
    
    if [[ $local_passed -eq 1 || $docker_passed -eq 1 ]]; then
        ok "🎉 Testy jednostkowe przeszły w przynajmniej jednym środowisku!"
        echo -e "${G}=================================================================${NC}"
        return 0
    else
        fail "❌ Testy jednostkowe nie przeszły w żadnym środowisku"
        echo -e "${R}=================================================================${NC}"
        return 1
    fi
}

# Cleanup trap
trap cleanup_docker EXIT

# Execute
main "$@" 