#!/bin/bash
# 🚀 Lokalny Pipeline Testowy dla Frameworka Mancer
# Symuluje CI/CD pipeline na lokalnej maszynie z Dockerem

set -euo pipefail  # Strict error handling

# =============================================================================
# KONFIGURACJA PIPELINE'U
# =============================================================================

PIPELINE_START_TIME=$(date +%s)
PIPELINE_ID="pipeline-$(date +%Y%m%d-%H%M%S)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="${PROJECT_ROOT}/pipeline"
REPORTS_DIR="${PIPELINE_DIR}/reports"
LOGS_DIR="${PIPELINE_DIR}/logs"
ARTIFACTS_DIR="${PIPELINE_DIR}/artifacts"

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Pipeline stages
declare -a PIPELINE_STAGES=(
    "setup"
    "lint"
    "unit_tests"
    "build_docker"
    "integration_tests"
    "e2e_tests"
    "coverage_report"
    "performance_tests"
    "security_scan"
    "generate_artifacts"
    "cleanup"
)

# Stage results
declare -A STAGE_RESULTS=()
declare -A STAGE_TIMES=()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOGS_DIR}/pipeline.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOGS_DIR}/pipeline.log"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOGS_DIR}/pipeline.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOGS_DIR}/pipeline.log"
}

log_stage() {
    echo -e "${PURPLE}[STAGE]${NC} $1" | tee -a "${LOGS_DIR}/pipeline.log"
}

print_banner() {
    echo -e "${CYAN}"
    echo "================================================================="
    echo "🚀 MANCER FRAMEWORK - LOKALNY PIPELINE TESTOWY"
    echo "================================================================="
    echo "Pipeline ID: ${PIPELINE_ID}"
    echo "Start Time: $(date)"
    echo "Project Root: ${PROJECT_ROOT}"
    echo "================================================================="
    echo -e "${NC}"
}

create_directories() {
    mkdir -p "${PIPELINE_DIR}" "${REPORTS_DIR}" "${LOGS_DIR}" "${ARTIFACTS_DIR}"
    log_info "Created pipeline directories"
}

# =============================================================================
# STAGE FUNCTIONS
# =============================================================================

stage_setup() {
    local stage_start=$(date +%s)
    log_stage "🔧 SETUP - Przygotowanie środowiska"
    
    cd "${PROJECT_ROOT}"
    
    # Check requirements
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required"
        return 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required"  
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is required"
        return 1
    fi
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt > "${LOGS_DIR}/pip_install.log" 2>&1
    
    # Verify pytest installation
    if ! command -v pytest &> /dev/null; then
        log_error "pytest installation failed"
        return 1
    fi
    
    # Create Python environment info
    python3 --version > "${REPORTS_DIR}/environment.txt"
    pip list > "${REPORTS_DIR}/dependencies.txt"
    
    local stage_end=$(date +%s)
    STAGE_TIMES["setup"]=$((stage_end - stage_start))
    log_success "Setup completed in ${STAGE_TIMES["setup"]}s"
    return 0
}

stage_lint() {
    local stage_start=$(date +%s)
    log_stage "🔍 LINT - Analiza jakości kodu"
    
    cd "${PROJECT_ROOT}"
    
    # Create lint report
    local lint_report="${REPORTS_DIR}/lint_report.txt"
    
    # Check if we have linting tools, install if needed
    if ! command -v flake8 &> /dev/null; then
        log_info "Installing linting tools..."
        pip install flake8 black isort mypy > "${LOGS_DIR}/lint_install.log" 2>&1
    fi
    
    # Run linting
    log_info "Running flake8..."
    flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__ > "${lint_report}" 2>&1 || true
    
    log_info "Running black (check only)..."
    black --check --diff src/ tests/ >> "${lint_report}" 2>&1 || true
    
    log_info "Running isort (check only)..."
    isort --check-only --diff src/ tests/ >> "${lint_report}" 2>&1 || true
    
    # Check results
    if [ -s "${lint_report}" ]; then
        log_warning "Linting issues found - see ${lint_report}"
        STAGE_RESULTS["lint"]="warning"
    else
        log_success "No linting issues found"
        STAGE_RESULTS["lint"]="success"
    fi
    
    local stage_end=$(date +%s)
    STAGE_TIMES["lint"]=$((stage_end - stage_start))
    log_success "Lint completed in ${STAGE_TIMES["lint"]}s"
    return 0
}

stage_unit_tests() {
    local stage_start=$(date +%s)
    log_stage "🧪 UNIT TESTS - Testy jednostkowe"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Running unit tests..."
    
    # Run unit tests with coverage
    pytest tests/unit/ \
        -v \
        --tb=short \
        --junit-xml="${REPORTS_DIR}/unit_tests.xml" \
        --cov=src/mancer \
        --cov-report=term-missing \
        --cov-report=html:"${REPORTS_DIR}/coverage_unit" \
        --cov-report=xml:"${REPORTS_DIR}/coverage_unit.xml" \
        > "${LOGS_DIR}/unit_tests.log" 2>&1
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "All unit tests passed"
        STAGE_RESULTS["unit_tests"]="success"
    else
        log_error "Unit tests failed with exit code $exit_code"
        STAGE_RESULTS["unit_tests"]="failed"
        return 1
    fi
    
    local stage_end=$(date +%s)
    STAGE_TIMES["unit_tests"]=$((stage_end - stage_start))
    log_success "Unit tests completed in ${STAGE_TIMES["unit_tests"]}s"
    return 0
}

stage_build_docker() {
    local stage_start=$(date +%s)
    log_stage "🐳 BUILD DOCKER - Budowanie środowiska testowego"
    
    cd "${PROJECT_ROOT}/development/docker_test"
    
    log_info "Cleaning up old Docker environment..."
    sudo ./cleanup.sh > "${LOGS_DIR}/docker_cleanup.log" 2>&1 || true
    
    log_info "Preparing environment file..."
    if [ ! -f .env ]; then
        cp env.develop.test .env
    fi
    
    log_info "Building Docker containers..."
    docker-compose build > "${LOGS_DIR}/docker_build.log" 2>&1
    
    log_info "Starting Docker containers..."
    docker-compose up -d > "${LOGS_DIR}/docker_start.log" 2>&1
    
    # Wait for containers to be ready
    log_info "Waiting for containers to be ready..."
    local max_wait=120
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if docker exec mancer-test-1 echo "ready" > /dev/null 2>&1; then
            log_success "Containers are ready"
            break
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        log_info "Waiting... ($wait_time/${max_wait}s)"
    done
    
    if [ $wait_time -ge $max_wait ]; then
        log_error "Containers failed to start within ${max_wait}s"
        return 1
    fi
    
    # Generate container info
    docker ps > "${REPORTS_DIR}/docker_containers.txt"
    docker network ls > "${REPORTS_DIR}/docker_networks.txt"
    
    local stage_end=$(date +%s)
    STAGE_TIMES["build_docker"]=$((stage_end - stage_start))
    log_success "Docker build completed in ${STAGE_TIMES["build_docker"]}s"
    return 0
}

stage_integration_tests() {
    local stage_start=$(date +%s)
    log_stage "🔗 INTEGRATION TESTS - Testy integracyjne"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Running integration tests..."
    
    # Run integration tests
    pytest tests/integration/ \
        -v \
        --tb=short \
        --junit-xml="${REPORTS_DIR}/integration_tests.xml" \
        --docker-compose=development/docker_test/docker-compose.yml \
        --docker-compose-no-build \
        > "${LOGS_DIR}/integration_tests.log" 2>&1
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "All integration tests passed"  
        STAGE_RESULTS["integration_tests"]="success"
    else
        log_error "Integration tests failed with exit code $exit_code"
        STAGE_RESULTS["integration_tests"]="failed"
        return 1
    fi
    
    local stage_end=$(date +%s)
    STAGE_TIMES["integration_tests"]=$((stage_end - stage_start))
    log_success "Integration tests completed in ${STAGE_TIMES["integration_tests"]}s"
    return 0
}

stage_e2e_tests() {
    local stage_start=$(date +%s)
    log_stage "🎯 E2E TESTS - Testy end-to-end"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Running end-to-end tests..."
    
    # Run E2E example
    python3 examples/docker_testing_example.py > "${LOGS_DIR}/e2e_tests.log" 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "E2E tests passed"
        STAGE_RESULTS["e2e_tests"]="success"
    else
        log_error "E2E tests failed with exit code $exit_code"
        STAGE_RESULTS["e2e_tests"]="failed" 
        return 1
    fi
    
    local stage_end=$(date +%s)
    STAGE_TIMES["e2e_tests"]=$((stage_end - stage_start))
    log_success "E2E tests completed in ${STAGE_TIMES["e2e_tests"]}s"
    return 0
}

stage_coverage_report() {
    local stage_start=$(date +%s)
    log_stage "📊 COVERAGE - Raport pokrycia kodu"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Generating combined coverage report..."
    
    # Run all tests with coverage
    pytest tests/ \
        --cov=src/mancer \
        --cov-report=html:"${REPORTS_DIR}/coverage_combined" \
        --cov-report=xml:"${REPORTS_DIR}/coverage_combined.xml" \
        --cov-report=term > "${REPORTS_DIR}/coverage_summary.txt" 2>&1 || true
    
    # Extract coverage percentage
    if [ -f "${REPORTS_DIR}/coverage_combined.xml" ]; then
        local coverage_percent=$(grep -o 'line-rate="[0-9.]*"' "${REPORTS_DIR}/coverage_combined.xml" | head -1 | grep -o '[0-9.]*' | awk '{print int($1*100)}')
        echo "Coverage: ${coverage_percent}%" > "${REPORTS_DIR}/coverage_badge.txt"
        log_info "Code coverage: ${coverage_percent}%"
    fi
    
    local stage_end=$(date +%s)
    STAGE_TIMES["coverage_report"]=$((stage_end - stage_start))
    log_success "Coverage report completed in ${STAGE_TIMES["coverage_report"]}s"
    return 0
}

stage_performance_tests() {
    local stage_start=$(date +%s)
    log_stage "⚡ PERFORMANCE - Testy wydajności"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Running performance benchmarks..."
    
    # Create simple performance test
    cat > "${PIPELINE_DIR}/performance_test.py" << 'EOF'
#!/usr/bin/env python3
import time
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mancer.application.shell_runner import ShellRunner

def benchmark_command_execution():
    """Benchmark basic command execution"""
    runner = ShellRunner(backend_type="bash")
    
    # Warm up
    for _ in range(3):
        runner.execute(runner.create_command("echo").text("warmup"))
    
    # Benchmark
    times = []
    for i in range(10):
        start = time.time()
        result = runner.execute(runner.create_command("echo").text(f"test-{i}"))
        end = time.time()
        
        if result.success:
            times.append(end - start)
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    return {
        "test": "command_execution",
        "iterations": len(times),
        "avg_time_ms": round(avg_time * 1000, 2),
        "max_time_ms": round(max_time * 1000, 2), 
        "min_time_ms": round(min_time * 1000, 2),
        "success": avg_time < 0.1  # Should be under 100ms
    }

if __name__ == "__main__":
    try:
        result = benchmark_command_execution()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "success": False}))
EOF
    
    python3 "${PIPELINE_DIR}/performance_test.py" > "${REPORTS_DIR}/performance_results.json" 2>&1 || true
    
    local stage_end=$(date +%s)
    STAGE_TIMES["performance_tests"]=$((stage_end - stage_start))
    log_success "Performance tests completed in ${STAGE_TIMES["performance_tests"]}s"
    return 0
}

stage_security_scan() {
    local stage_start=$(date +%s)
    log_stage "🔒 SECURITY - Skanowanie bezpieczeństwa"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Running security scans..."
    
    # Install safety if needed
    if ! command -v safety &> /dev/null; then
        pip install safety > "${LOGS_DIR}/safety_install.log" 2>&1
    fi
    
    # Check for known vulnerabilities
    safety check > "${REPORTS_DIR}/security_report.txt" 2>&1 || true
    
    # Simple secrets scan
    log_info "Scanning for potential secrets..."
    grep -r -i -E "(password|secret|key|token)" src/ tests/ --exclude-dir=__pycache__ > "${REPORTS_DIR}/secrets_scan.txt" 2>&1 || true
    
    local stage_end=$(date +%s)
    STAGE_TIMES["security_scan"]=$((stage_end - stage_start))
    log_success "Security scan completed in ${STAGE_TIMES["security_scan"]}s"
    return 0
}

stage_generate_artifacts() {
    local stage_start=$(date +%s)
    log_stage "📦 ARTIFACTS - Generowanie artefaktów"
    
    cd "${PROJECT_ROOT}"
    
    log_info "Generating pipeline artifacts..."
    
    # Create pipeline summary
    cat > "${ARTIFACTS_DIR}/pipeline_summary.json" << EOF
{
    "pipeline_id": "${PIPELINE_ID}",
    "start_time": "${PIPELINE_START_TIME}",
    "end_time": "$(date +%s)",
    "total_duration": "$(($(date +%s) - PIPELINE_START_TIME))",
    "stages": $(printf '%s\n' "${!STAGE_RESULTS[@]}" | jq -R . | jq -s 'map({stage: ., result: "'"$(printf '%s\n' "${STAGE_RESULTS[@]}")"'"}) | from_entries'),
    "stage_times": $(printf '%s\n' "${!STAGE_TIMES[@]}" | jq -R . | jq -s 'map({stage: ., time: "'"$(printf '%s\n' "${STAGE_TIMES[@]}")"'"}) | from_entries')
}
EOF

    # Create HTML report
    cat > "${ARTIFACTS_DIR}/pipeline_report.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Mancer Framework - Pipeline Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .success { color: green; }
        .warning { color: orange; }
        .failed { color: red; }
        .stage { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>🚀 Mancer Framework - Pipeline Report</h1>
    <p><strong>Pipeline ID:</strong> PIPELINE_ID_PLACEHOLDER</p>
    <p><strong>Generated:</strong> TIMESTAMP_PLACEHOLDER</p>
    
    <h2>📊 Stage Results</h2>
    <div id="stages">
        <!-- Stages will be populated -->
    </div>
    
    <h2>📈 Reports</h2>
    <ul>
        <li><a href="../reports/coverage_combined/index.html">Coverage Report</a></li>
        <li><a href="../reports/unit_tests.xml">Unit Test Results</a></li>
        <li><a href="../reports/integration_tests.xml">Integration Test Results</a></li>
        <li><a href="../reports/performance_results.json">Performance Results</a></li>
    </ul>
</body>
</html>
EOF

    # Replace placeholders
    sed -i "s/PIPELINE_ID_PLACEHOLDER/${PIPELINE_ID}/g" "${ARTIFACTS_DIR}/pipeline_report.html"
    sed -i "s/TIMESTAMP_PLACEHOLDER/$(date)/g" "${ARTIFACTS_DIR}/pipeline_report.html"
    
    # Package artifacts
    tar -czf "${ARTIFACTS_DIR}/pipeline_artifacts.tar.gz" -C "${PIPELINE_DIR}" reports logs
    
    local stage_end=$(date +%s)
    STAGE_TIMES["generate_artifacts"]=$((stage_end - stage_start))
    log_success "Artifacts generated in ${STAGE_TIMES["generate_artifacts"]}s"
    return 0
}

stage_cleanup() {
    local stage_start=$(date +%s)
    log_stage "🧹 CLEANUP - Czyszczenie środowiska"
    
    cd "${PROJECT_ROOT}/development/docker_test"
    
    log_info "Cleaning up Docker environment..."
    sudo ./cleanup.sh > "${LOGS_DIR}/cleanup.log" 2>&1 || true
    
    # Clean up temporary files
    rm -f "${PIPELINE_DIR}/performance_test.py"
    
    local stage_end=$(date +%s)
    STAGE_TIMES["cleanup"]=$((stage_end - stage_start))
    log_success "Cleanup completed in ${STAGE_TIMES["cleanup"]}s"
    return 0
}

# =============================================================================
# MAIN PIPELINE EXECUTION
# =============================================================================

run_pipeline() {
    print_banner
    create_directories
    
    local overall_success=true
    
    for stage in "${PIPELINE_STAGES[@]}"; do
        log_info "Starting stage: $stage"
        
        if "stage_$stage"; then
            log_success "✅ Stage '$stage' completed successfully"
            STAGE_RESULTS["$stage"]="success"
        else
            log_error "❌ Stage '$stage' failed"
            STAGE_RESULTS["$stage"]="failed"
            overall_success=false
            
            # Ask if should continue
            if [[ "${CONTINUE_ON_FAILURE:-false}" != "true" ]]; then
                echo -e "${YELLOW}Continue with next stages? [y/N]:${NC}"
                read -r continue_choice
                if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
                    log_error "Pipeline stopped by user"
                    break
                fi
            fi
        fi
    done
    
    # Final summary
    local pipeline_end_time=$(date +%s)
    local total_time=$((pipeline_end_time - PIPELINE_START_TIME))
    
    echo -e "${CYAN}"
    echo "================================================================="
    echo "🏁 PIPELINE COMPLETED"
    echo "================================================================="
    echo "Pipeline ID: ${PIPELINE_ID}"
    echo "Total Time: ${total_time}s"
    echo "================================================================="
    
    # Stage summary
    for stage in "${PIPELINE_STAGES[@]}"; do
        local result="${STAGE_RESULTS[$stage]:-unknown}"
        local time="${STAGE_TIMES[$stage]:-0}"
        
        case $result in
            "success") echo -e "✅ $stage (${time}s)" ;;
            "warning") echo -e "⚠️  $stage (${time}s)" ;;
            "failed")  echo -e "❌ $stage (${time}s)" ;;
            *)         echo -e "❓ $stage (${time}s)" ;;
        esac
    done
    
    echo "================================================================="
    echo "📁 Artifacts: ${ARTIFACTS_DIR}/"
    echo "📊 Reports: ${REPORTS_DIR}/"
    echo "📋 Logs: ${LOGS_DIR}/"
    echo "================================================================="
    echo -e "${NC}"
    
    if $overall_success; then
        log_success "🎉 Pipeline completed successfully!"
        return 0
    else
        log_error "💥 Pipeline completed with failures"
        return 1
    fi
}

# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --continue-on-failure)
            CONTINUE_ON_FAILURE=true
            shift
            ;;
        --skip-stage)
            SKIP_STAGE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --continue-on-failure    Continue pipeline even if stages fail"
            echo "  --skip-stage STAGE       Skip specific stage"
            echo "  --help                   Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run the pipeline
if run_pipeline; then
    exit 0
else
    exit 1
fi 