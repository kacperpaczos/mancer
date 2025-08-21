#!/bin/bash

# Quick CI Script for Mancer
# This script runs fast checks for development

set -e

echo "⚡ Starting quick CI checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Quick syntax check
print_status "Checking Python syntax..."
python -m py_compile src/mancer/__init__.py
find src/ -name "*.py" -exec python -m py_compile {} \;
print_success "Syntax check passed"

# Quick import test
print_status "Testing imports..."
python -c "import mancer; print('Basic imports work')"
print_success "Import test passed"

# Quick formatting check
print_status "Checking code formatting..."
if command -v black &> /dev/null; then
    black --check src/ tests/ --quiet
    print_success "Code formatting check passed"
else
    print_warning "black not found, skipping formatting check"
fi

# Quick linting check
print_status "Running quick linting..."
if command -v ruff &> /dev/null; then
    ruff check src/ --select=E,F --quiet
    print_success "Quick linting passed"
else
    print_warning "ruff not found, skipping linting"
fi

# Quick test run
print_status "Running quick tests..."
python -m pytest tests/unit/ -x --tb=no -q
print_success "Quick tests passed"

print_success "Quick CI checks completed successfully! ⚡"
print_status "Code is ready for development."
