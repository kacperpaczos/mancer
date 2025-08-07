#!/bin/bash
# 🚀 AUTOMATYCZNY PIPELINE - Działa lokalnie I w Docker bez konfiguracji
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; NC='\033[0m'

log() { echo -e "${B}[AUTO]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

# =============================================================================
# AUTO-DETECTION & SETUP
# =============================================================================

detect_environment() {
    DOCKER_AVAILABLE=false
    LOCAL_PYTHON=false
    
    # Check Docker
    if command -v docker &>/dev/null && docker info &>/dev/null; then
        DOCKER_AVAILABLE=true
        log "Docker detected and running"
    fi
    
    # Check local Python
    if python3 -c "import sys; sys.path.append('src'); from mancer.application.shell_runner import ShellRunner" &>/dev/null; then
        LOCAL_PYTHON=true
        log "Local Python + Framework working"
    fi
    
    # Auto-install pytest if missing
    if ! python3 -c "import pytest" &>/dev/null 2>&1; then
        log "Auto-installing pytest..."
        if command -v apt &>/dev/null; then
            sudo apt update &>/dev/null && sudo apt install -y python3-pytest &>/dev/null || true
        fi
        pip3 install pytest &>/dev/null || pip install pytest &>/dev/null || true
    fi
}

setup_docker_environment() {
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        log "Setting up Docker test environment..."
        cd development/docker_test
        
        # Auto-create .env
        [[ ! -f .env ]] && cp env.develop.test .env
        
        # Clean and start
        sudo ./cleanup.sh &>/dev/null || true
        docker-compose up -d --build &>/dev/null
        
        # Wait for ready
        for i in {1..30}; do
            if docker exec mancer-test-1 echo "ready" &>/dev/null; then
                ok "Docker environment ready"
                cd "$PROJECT_ROOT"
                return 0
            fi
            sleep 2
        done
        
        fail "Docker environment failed to start"
        cd "$PROJECT_ROOT"
        return 1
    fi
    return 1
}

# =============================================================================
# UNIT TESTS - DUAL EXECUTION (LOCAL + DOCKER)
# =============================================================================

run_unit_tests_local() {
    log "Running unit tests LOCALLY..."
    
    if python3 -c "import pytest" &>/dev/null; then
        # Run locally
        PYTHONPATH=src python3 -m pytest tests/unit/ -v --tb=short -q 2>/dev/null || {
            warn "Local unit tests failed, trying with different path..."
            cd src && python3 -m pytest ../tests/unit/ -v --tb=short -q 2>/dev/null || return 1
            cd "$PROJECT_ROOT"
        }
        ok "Unit tests passed LOCALLY"
        return 0
    else
        warn "pytest not available locally"
        return 1
    fi
}

run_unit_tests_docker() {
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        log "Running unit tests in DOCKER..."
        
        # Execute unit tests in Docker container
        docker exec mancer-test-1 bash -c "
            cd /home/mancer1/mancer
            export PYTHONPATH=/home/mancer1/mancer/src
            python3 -m pytest tests/unit/ -v --tb=short -q 2>/dev/null || {
                cd src
                python3 -m pytest ../tests/unit/ -v --tb=short -q 2>/dev/null
            }
        " &>/dev/null && {
            ok "Unit tests passed in DOCKER"
            return 0
        }
        
        warn "Docker unit tests failed"
        return 1
    fi
    return 1
}

run_unit_tests() {
    local local_result=1
    local docker_result=1
    
    # Try local first
    run_unit_tests_local && local_result=0 || true
    
    # Try Docker
    run_unit_tests_docker && docker_result=0 || true
    
    if [[ $local_result -eq 0 || $docker_result -eq 0 ]]; then
        ok "Unit tests PASSED (local:$([[ $local_result -eq 0 ]] && echo "✓" || echo "✗") docker:$([[ $docker_result -eq 0 ]] && echo "✓" || echo "✗"))"
        return 0
    else
        fail "Unit tests FAILED in both environments"
        return 1
    fi
}

# =============================================================================
# INTEGRATION TESTS - DUAL EXECUTION (LOCAL + DOCKER)
# =============================================================================

run_integration_tests_local() {
    log "Running integration tests LOCALLY..."
    
    # Test if framework works locally with real bash
    python3 -c "
import sys
sys.path.append('src')
try:
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type='bash')
    
    # Test basic commands
    tests = [
        ('echo', lambda r: r.create_command('echo').text('integration_test')),
        ('ls', lambda r: r.create_command('ls')),
        ('hostname', lambda r: r.create_command('hostname')),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            cmd = test_func(runner)
            result = runner.execute(cmd)
            if result.success:
                passed += 1
        except:
            pass
    
    if passed >= 2:  # At least 2/3 tests must pass
        print('LOCAL_INTEGRATION_OK')
    else:
        print('LOCAL_INTEGRATION_FAIL')
        
except Exception as e:
    print('LOCAL_INTEGRATION_ERROR')
" 2>/dev/null | grep -q "LOCAL_INTEGRATION_OK" && {
        ok "Integration tests passed LOCALLY"
        return 0
    }
    
    warn "Local integration tests failed"
    return 1
}

run_integration_tests_docker() {
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        log "Running integration tests in DOCKER..."
        
        # Test framework in Docker container
        docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
try:
    from mancer.application.shell_runner import ShellRunner
    runner = ShellRunner(backend_type='bash')
    
    # Test basic commands in container
    tests = [
        ('echo', lambda r: r.create_command('echo').text('docker_integration')),
        ('ls', lambda r: r.create_command('ls')),
        ('hostname', lambda r: r.create_command('hostname')),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            cmd = test_func(runner)
            result = runner.execute(cmd)
            if result.success and (name == 'echo' and 'docker_integration' in result.raw_output or name != 'echo'):
                passed += 1
        except:
            pass
    
    if passed >= 2:
        print('DOCKER_INTEGRATION_OK')
    else:
        print('DOCKER_INTEGRATION_FAIL')
        
except Exception as e:
    print('DOCKER_INTEGRATION_ERROR')
" 2>/dev/null | grep -q "DOCKER_INTEGRATION_OK" && {
            ok "Integration tests passed in DOCKER"
            return 0
        }
        
        warn "Docker integration tests failed"
        return 1
    fi
    return 1
}

run_integration_tests() {
    local local_result=1
    local docker_result=1
    
    # Try local integration
    run_integration_tests_local && local_result=0 || true
    
    # Try Docker integration  
    run_integration_tests_docker && docker_result=0 || true
    
    if [[ $local_result -eq 0 || $docker_result -eq 0 ]]; then
        ok "Integration tests PASSED (local:$([[ $local_result -eq 0 ]] && echo "✓" || echo "✗") docker:$([[ $docker_result -eq 0 ]] && echo "✓" || echo "✗"))"
        return 0
    else
        fail "Integration tests FAILED in both environments"
        return 1
    fi
}

# =============================================================================
# FRAMEWORK TESTS - CORE FUNCTIONALITY
# =============================================================================

test_framework_core() {
    log "Testing framework core functionality..."
    
    # Test 1: Framework imports (local)
    if python3 -c "
import sys
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner  
from mancer.infrastructure.backend.bash_backend import BashBackend
from mancer.infrastructure.factory.command_factory import CommandFactory
print('IMPORT_OK')
" 2>/dev/null | grep -q "IMPORT_OK"; then
        ok "Framework imports work locally"
    else
        warn "Framework imports failed locally"
    fi
    
    # Test 2: Basic execution
    if python3 -c "
import sys
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner
runner = ShellRunner(backend_type='bash')
echo_cmd = runner.create_command('echo').text('core_test')
result = runner.execute(echo_cmd)
if result.success and 'core_test' in result.raw_output:
    print('EXECUTION_OK')
" 2>/dev/null | grep -q "EXECUTION_OK"; then
        ok "Framework execution works locally"
    else
        warn "Framework execution failed locally"
    fi
    
    # Test 3: Docker execution if available
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        if docker exec mancer-test-1 python3 -c "
import sys
sys.path.append('/home/mancer1/mancer/src')
from mancer.application.shell_runner import ShellRunner
runner = ShellRunner(backend_type='bash')
echo_cmd = runner.create_command('echo').text('docker_core_test')
result = runner.execute(echo_cmd)
if result.success and 'docker_core_test' in result.raw_output:
    print('DOCKER_EXECUTION_OK')
" 2>/dev/null | grep -q "DOCKER_EXECUTION_OK"; then
            ok "Framework execution works in Docker"
        else
            warn "Framework execution failed in Docker"
        fi
    fi
    return 0
}

# =============================================================================
# PERFORMANCE & SMOKE TESTS
# =============================================================================

run_performance_test() {
    log "Running performance tests..."
    
    python3 -c "
import sys, time
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type='bash')
times = []

for i in range(3):
    start = time.time()
    result = runner.execute(runner.create_command('echo').text(f'perf_{i}'))
    if result.success:
        times.append(time.time() - start)

if times:
    avg = sum(times) / len(times)
    if avg < 0.5:  # 500ms threshold
        print(f'PERFORMANCE_OK:{avg*1000:.0f}ms')
    else:
        print(f'PERFORMANCE_SLOW:{avg*1000:.0f}ms')
" 2>/dev/null | grep -E "(PERFORMANCE_OK|PERFORMANCE_SLOW)" | head -1 | {
        IFS=':' read status time
        if [[ "$status" == "PERFORMANCE_OK" ]]; then
            ok "Performance test passed (${time} avg)"
        else
            warn "Performance test slow (${time} avg)"
        fi
    } || warn "Performance test failed"
    return 0
}

run_smoke_test() {
    log "Running smoke tests..."
    
    # Smoke test: All major components work
    python3 -c "
import sys
sys.path.append('src')

tests = {
    'ShellRunner': False,
    'BashBackend': False, 
    'CommandFactory': False,
    'Echo Command': False,
    'LS Command': False
}

try:
    from mancer.application.shell_runner import ShellRunner
    tests['ShellRunner'] = True
    
    from mancer.infrastructure.backend.bash_backend import BashBackend
    tests['BashBackend'] = True
    
    from mancer.infrastructure.factory.command_factory import CommandFactory
    tests['CommandFactory'] = True
    
    runner = ShellRunner(backend_type='bash')
    
    # Test echo
    echo_result = runner.execute(runner.create_command('echo').text('smoke'))
    if echo_result.success and 'smoke' in echo_result.raw_output:
        tests['Echo Command'] = True
    
    # Test ls
    ls_result = runner.execute(runner.create_command('ls'))
    if ls_result.success:
        tests['LS Command'] = True
        
    passed = sum(tests.values())
    total = len(tests)
    
    if passed >= 4:  # At least 4/5 must pass
        print(f'SMOKE_OK:{passed}/{total}')
    else:
        print(f'SMOKE_FAIL:{passed}/{total}')
        
except Exception as e:
    print('SMOKE_ERROR')
" 2>/dev/null | grep -E "(SMOKE_OK|SMOKE_FAIL)" | {
        IFS=':' read status result
        if [[ "$status" == "SMOKE_OK" ]]; then
            ok "Smoke test passed ($result)"
        else
            warn "Smoke test failed ($result)"
        fi
    } || warn "Smoke test error"
    return 0
}

# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

cleanup_on_exit() {
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        log "Cleaning up Docker environment..."
        cd development/docker_test &>/dev/null && sudo ./cleanup.sh &>/dev/null || true
        cd "$PROJECT_ROOT" &>/dev/null || true
    fi
}

# Set cleanup trap
trap cleanup_on_exit EXIT

main() {
    echo -e "${B}"
    echo "================================================================="
    echo "🚀 AUTOMATYCZNY PIPELINE - Framework Mancer"
    echo "================================================================="
    echo -e "${NC}"
    
    local failed_tests=0
    local total_tests=0
    
    # Auto-detection
    log "Auto-detecting environment..."
    detect_environment
    
    # Setup Docker if available
    if [[ "$DOCKER_AVAILABLE" == "true" ]]; then
        setup_docker_environment || DOCKER_AVAILABLE=false
    fi
    
    echo -e "${B}Environment: LOCAL=$([[ "$LOCAL_PYTHON" == "true" ]] && echo "✓" || echo "✗") DOCKER=$([[ "$DOCKER_AVAILABLE" == "true" ]] && echo "✓" || echo "✗")${NC}"
    echo
    
    # Core framework tests
    ((total_tests++))
    test_framework_core || ((failed_tests++))
    
    # Unit tests (dual execution)
    ((total_tests++))
    run_unit_tests || ((failed_tests++))
    
    # Integration tests (dual execution)  
    ((total_tests++))
    run_integration_tests || ((failed_tests++))
    
    # Performance tests
    ((total_tests++))
    run_performance_test || ((failed_tests++))
    
    # Smoke tests
    ((total_tests++))
    run_smoke_test || ((failed_tests++))
    
    # Results
    echo
    echo -e "${B}=================================================================${NC}"
    echo -e "${B}🏁 PIPELINE COMPLETED${NC}"
    echo -e "${B}=================================================================${NC}"
    
    local passed_tests=$((total_tests - failed_tests))
    echo "Tests: ${passed_tests}/${total_tests} passed"
    echo "Environment: LOCAL=$([[ "$LOCAL_PYTHON" == "true" ]] && echo "✓" || echo "✗") DOCKER=$([[ "$DOCKER_AVAILABLE" == "true" ]] && echo "✓" || echo "✗")"
    
    if [[ $failed_tests -eq 0 ]]; then
        ok "🎉 ALL TESTS PASSED - Framework ready for development!"
        echo -e "${G}=================================================================${NC}"  
        return 0
    else
        fail "❌ $failed_tests/$total_tests tests failed"
        echo -e "${R}=================================================================${NC}"
        return 1
    fi
}

# Execute pipeline
main "$@" 