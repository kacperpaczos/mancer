#!/bin/bash
# 🎯 Pipeline Stage Runner - Uruchamia konkretne stage'y pipeline'u
# Pozwala na selektywne testowanie i debugging poszczególnych etapów

set -euo pipefail

# Kolory
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Available stages
AVAILABLE_STAGES=(
    "setup"
    "lint"
    "unit_tests"
    "build_docker"
    "integration_tests"
    "e2e_tests"
    "coverage_report"
    "performance_tests"
    "security_scan"
    "cleanup"
)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_stage() {
    echo -e "${PURPLE}[STAGE]${NC} $1"
}

show_help() {
    echo "Pipeline Stage Runner - Run specific pipeline stages"
    echo ""
    echo "Usage: $0 STAGE [OPTIONS]"
    echo ""
    echo "Available Stages:"
    for stage in "${AVAILABLE_STAGES[@]}"; do
        echo "  • $stage"
    done
    echo ""
    echo "Options:"
    echo "  --list        List all available stages"
    echo "  --help        Show this help"
    echo "  --verbose     Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 unit_tests                    # Run only unit tests"
    echo "  $0 build_docker --verbose       # Build Docker with verbose output"
    echo "  $0 lint                         # Run only linting"
    echo "  $0 --list                       # Show available stages"
}

list_stages() {
    echo "Available Pipeline Stages:"
    echo ""
    
    local descriptions=(
        "setup:Setup environment and install dependencies"
        "lint:Code quality analysis (flake8, black, isort)"
        "unit_tests:Run unit tests with coverage"
        "build_docker:Build and start Docker test environment"
        "integration_tests:Run integration tests in Docker"
        "e2e_tests:Run end-to-end tests"
        "coverage_report:Generate combined coverage report"
        "performance_tests:Run performance benchmarks"
        "security_scan:Security vulnerability scanning"
        "cleanup:Clean up Docker environment and temp files"
    )
    
    for desc in "${descriptions[@]}"; do
        local stage=${desc%%:*}
        local description=${desc#*:}
        printf "%-20s %s\n" "$stage" "$description"
    done
}

validate_stage() {
    local stage="$1"
    for valid_stage in "${AVAILABLE_STAGES[@]}"; do
        if [[ "$stage" == "$valid_stage" ]]; then
            return 0
        fi
    done
    return 1
}

run_stage() {
    local stage="$1"
    local verbose="${VERBOSE:-false}"
    
    if ! validate_stage "$stage"; then
        log_error "Invalid stage: $stage"
        echo "Use --list to see available stages"
        return 1
    fi
    
    log_stage "🚀 Running stage: $stage"
    
    case "$stage" in
        "setup")
            run_setup_stage "$verbose"
            ;;
        "lint")
            run_lint_stage "$verbose"
            ;;
        "unit_tests")
            run_unit_tests_stage "$verbose"
            ;;
        "build_docker")
            run_build_docker_stage "$verbose"
            ;;
        "integration_tests")
            run_integration_tests_stage "$verbose"
            ;;
        "e2e_tests")
            run_e2e_tests_stage "$verbose"
            ;;
        "coverage_report")
            run_coverage_report_stage "$verbose"
            ;;
        "performance_tests")
            run_performance_tests_stage "$verbose"
            ;;
        "security_scan")
            run_security_scan_stage "$verbose"
            ;;
        "cleanup")
            run_cleanup_stage "$verbose"
            ;;
        *)
            log_error "Stage implementation not found: $stage"
            return 1
            ;;
    esac
}

run_setup_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Installing Python dependencies..."
    if [[ "$verbose" == "true" ]]; then
        pip install -r requirements.txt
    else
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    log_success "Setup completed"
}

run_lint_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    # Install linting tools if needed
    if ! command -v flake8 &> /dev/null; then
        log_info "Installing linting tools..."
        pip install flake8 black isort mypy
    fi
    
    log_info "Running flake8..."
    if [[ "$verbose" == "true" ]]; then
        flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__
    else
        flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__ --quiet
    fi
    
    log_info "Running black (check only)..."
    if [[ "$verbose" == "true" ]]; then
        black --check --diff src/ tests/
    else
        black --check src/ tests/ > /dev/null 2>&1
    fi
    
    log_success "Linting completed"
}

run_unit_tests_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Running unit tests..."
    if [[ "$verbose" == "true" ]]; then
        pytest tests/unit/ -v --tb=short --cov=src/mancer --cov-report=term-missing
    else
        pytest tests/unit/ -q --tb=short
    fi
    
    log_success "Unit tests completed"
}

run_build_docker_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}/development/docker_test"
    
    log_info "Cleaning up old Docker environment..."
    sudo ./cleanup.sh > /dev/null 2>&1 || true
    
    if [ ! -f .env ]; then
        log_info "Creating .env file..."
        cp env.develop.test .env
    fi
    
    log_info "Building Docker containers..."
    if [[ "$verbose" == "true" ]]; then
        docker-compose build
        docker-compose up -d
    else
        docker-compose build > /dev/null 2>&1
        docker-compose up -d > /dev/null 2>&1
    fi
    
    # Wait for containers
    log_info "Waiting for containers to be ready..."
    local max_wait=60
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if docker exec mancer-test-1 echo "ready" > /dev/null 2>&1; then
            break
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        if [[ "$verbose" == "true" ]]; then
            log_info "Waiting... ($wait_time/${max_wait}s)"
        fi
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_error "Containers failed to start within ${max_wait}s"
        return 1
    fi
    
    log_success "Docker environment ready"
}

run_integration_tests_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Running integration tests..."
    if [[ "$verbose" == "true" ]]; then
        pytest tests/integration/ -v --tb=short \
            --docker-compose=development/docker_test/docker-compose.yml \
            --docker-compose-no-build
    else
        pytest tests/integration/ -q --tb=short \
            --docker-compose=development/docker_test/docker-compose.yml \
            --docker-compose-no-build
    fi
    
    log_success "Integration tests completed"
}

run_e2e_tests_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Running E2E tests..."
    if [[ "$verbose" == "true" ]]; then
        python3 examples/docker_testing_example.py
    else
        python3 examples/docker_testing_example.py > /dev/null 2>&1
    fi
    
    log_success "E2E tests completed"
}

run_coverage_report_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Generating coverage report..."
    pytest tests/ --cov=src/mancer --cov-report=html:htmlcov --cov-report=term
    
    log_info "Coverage report generated in htmlcov/"
    log_success "Coverage report completed"
}

run_performance_tests_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Running performance tests..."
    
    # Simple performance test
    python3 -c "
import time
import sys
sys.path.append('src')
from mancer.application.shell_runner import ShellRunner

runner = ShellRunner(backend_type='bash')
times = []

for i in range(5):
    start = time.time()
    result = runner.execute(runner.create_command('echo').text(f'perf-test-{i}'))
    end = time.time()
    if result.success:
        times.append(end - start)

if times:
    avg_time = sum(times) / len(times)
    print(f'Average execution time: {avg_time*1000:.2f}ms')
    if avg_time < 0.1:
        print('✅ Performance test passed')
    else:
        print('⚠️ Performance slower than expected')
else:
    print('❌ Performance test failed')
"
    
    log_success "Performance tests completed"
}

run_security_scan_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}"
    
    log_info "Running security scan..."
    
    # Install safety if needed
    if ! command -v safety &> /dev/null; then
        pip install safety > /dev/null 2>&1
    fi
    
    # Check for vulnerabilities
    log_info "Checking for known vulnerabilities..."
    if [[ "$verbose" == "true" ]]; then
        safety check
    else
        safety check > /dev/null 2>&1 || log_warning "Some security issues found"
    fi
    
    log_success "Security scan completed"
}

run_cleanup_stage() {
    local verbose="$1"
    cd "${PROJECT_ROOT}/development/docker_test"
    
    log_info "Cleaning up Docker environment..."
    if [[ "$verbose" == "true" ]]; then
        sudo ./cleanup.sh
    else
        sudo ./cleanup.sh > /dev/null 2>&1
    fi
    
    log_success "Cleanup completed"
}

# Parse arguments
STAGE=""
VERBOSE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            list_stages
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        --verbose|-v)
            VERBOSE="true"
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$STAGE" ]]; then
                STAGE="$1"
            else
                log_error "Multiple stages not supported in single run"
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
if [[ -z "$STAGE" ]]; then
    log_error "No stage specified"
    show_help
    exit 1
fi

echo -e "${BLUE}"
echo "=========================================="
echo "🎯 PIPELINE STAGE RUNNER"
echo "=========================================="
echo "Stage: $STAGE"
echo "Verbose: $VERBOSE"
echo "=========================================="
echo -e "${NC}"

start_time=$(date +%s)

if run_stage "$STAGE"; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo -e "${GREEN}"
    echo "=========================================="
    echo "✅ STAGE COMPLETED SUCCESSFULLY"
    echo "=========================================="
    echo "Stage: $STAGE"
    echo "Duration: ${duration}s"
    echo "=========================================="
    echo -e "${NC}"
    exit 0
else
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo -e "${RED}"
    echo "=========================================="
    echo "❌ STAGE FAILED"
    echo "=========================================="
    echo "Stage: $STAGE"
    echo "Duration: ${duration}s"
    echo "=========================================="
    echo -e "${NC}"
    exit 1
fi 