#!/bin/bash
# 🚀 Quick Pipeline - Szybki pipeline dla development workflow
# Uruchamia tylko najważniejsze testy bez pełnego środowiska Docker

set -euo pipefail

# Kolory
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_TIME=$(date +%s)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_banner() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "⚡ MANCER QUICK PIPELINE - Development Mode"
    echo "=============================================="
    echo -e "${NC}"
}

quick_lint() {
    log_info "🔍 Running quick lint check..."
    cd "${PROJECT_ROOT}"
    
    # Check if linting tools exist
    if command -v flake8 &> /dev/null; then
        log_info "Running flake8..."
        if flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__ --quiet; then
            log_success "✅ No linting issues found"
        else
            log_warning "⚠️ Linting issues found"
            return 1
        fi
    else
        log_warning "flake8 not installed, skipping lint"
    fi
}

quick_unit_tests() {
    log_info "🧪 Running unit tests..."
    cd "${PROJECT_ROOT}"
    
    if ! command -v pytest &> /dev/null; then
        log_error "pytest not installed. Run: pip install -r requirements.txt"
        return 1
    fi
    
    # Run unit tests only
    if pytest tests/unit/ -v --tb=short -q; then
        log_success "✅ All unit tests passed"
        return 0
    else
        log_error "❌ Unit tests failed"
        return 1
    fi
}

quick_smoke_test() {
    log_info "💨 Running smoke test..."
    cd "${PROJECT_ROOT}"
    
    # Quick import test
    python3 -c "
import sys
sys.path.append('src')
try:
    from mancer.application.shell_runner import ShellRunner
    from mancer.infrastructure.backend.bash_backend import BashBackend
    from mancer.infrastructure.factory.command_factory import CommandFactory
    print('Framework imports: OK')
    
    # Quick functionality test
    runner = ShellRunner(backend_type='bash')
    echo_cmd = runner.create_command('echo').text('smoke_test')
    result = runner.execute(echo_cmd)
    
    if result.success and 'smoke_test' in result.raw_output:
        print('Basic functionality: OK')
    else:
        print('Basic functionality: FAILED')
        exit(1)
        
except Exception as e:
    print(f'Framework test failed: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log_success "✅ Smoke test passed"
        return 0
    else
        log_error "❌ Smoke test failed"
        return 1
    fi
}

quick_security_check() {
    log_info "🔒 Running quick security check..."
    cd "${PROJECT_ROOT}"
    
    # Check for common security issues
    local issues=0
    
    # Check for hardcoded passwords/secrets
    if grep -r -i "password.*=" src/ tests/ 2>/dev/null | grep -v "password_field\|test_password" | head -1; then
        log_warning "⚠️ Potential hardcoded passwords found"
        ((issues++))
    fi
    
    # Check for SQL injection patterns
    if grep -r "SELECT.*%" src/ 2>/dev/null | head -1; then
        log_warning "⚠️ Potential SQL injection patterns found"
        ((issues++))
    fi
    
    # Check for shell injection patterns
    if grep -r "os\.system\|subprocess.*shell=True" src/ 2>/dev/null | head -1; then
        log_warning "⚠️ Potential shell injection patterns found"
        ((issues++))
    fi
    
    if [ $issues -eq 0 ]; then
        log_success "✅ No obvious security issues found"
        return 0
    else
        log_warning "⚠️ Found $issues potential security issues"
        return 1
    fi
}

# Main execution
main() {
    print_banner
    
    local failed_stages=0
    local total_stages=4
    
    # Run quick checks
    if ! quick_lint; then
        ((failed_stages++))
    fi
    
    if ! quick_unit_tests; then
        ((failed_stages++))
    fi
    
    if ! quick_smoke_test; then
        ((failed_stages++))
    fi
    
    if ! quick_security_check; then
        ((failed_stages++))
    fi
    
    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo -e "${BLUE}"
    echo "=============================================="
    echo "🏁 QUICK PIPELINE COMPLETED"
    echo "=============================================="
    echo "Duration: ${duration}s"
    echo "Stages: $((total_stages - failed_stages))/${total_stages} passed"
    
    if [ $failed_stages -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed! Ready for development.${NC}"
        echo "💡 For full testing run: ./scripts/local_pipeline.sh"
        return 0
    else
        echo -e "${RED}❌ $failed_stages checks failed.${NC}"
        echo "🔧 Fix issues and try again, or run full pipeline for details."
        return 1
    fi
}

# Help function
show_help() {
    echo "Quick Pipeline - Fast development checks"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Stages:"
    echo "  • Lint check (flake8)"
    echo "  • Unit tests"
    echo "  • Smoke test (basic functionality)"
    echo "  • Security check (basic patterns)"
    echo ""
    echo "Options:"
    echo "  --help    Show this help"
    echo ""
    echo "Example:"
    echo "  $0                    # Run all quick checks"
    echo "  $0 --help           # Show help"
}

# Parse arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 