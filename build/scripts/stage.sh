#!/bin/bash

# Staging CI Script for Mancer
# This script runs before deployment to staging environment

set -e

echo "🚀 Starting staging CI pipeline..."

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

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    print_status "Activating virtual environment..."
    source .venv/bin/activate
else
    print_error "Virtual environment not found. Please run local.sh first."
    exit 1
fi

# Run all pre-commit hooks
print_status "Running pre-commit hooks..."
pre-commit run --all-files

# Run comprehensive tests
print_status "Running comprehensive tests..."
python -m pytest tests/ -v --tb=short --cov=src/mancer --cov-report=html --cov-report=term

# Run linting with strict rules
print_status "Running linting..."
ruff check src/ tests/ --strict

# Run type checking
print_status "Running type checking..."
mypy src/ --strict

# Security checks
print_status "Running security checks..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o bandit-report.json
else
    print_warning "bandit not found, skipping security checks..."
fi

# Build and test package
print_status "Building package..."
python -m build

# Test package installation
print_status "Testing package installation..."
pip install dist/*.whl --force-reinstall

# Verify package works
print_status "Verifying package functionality..."
python -c "import mancer; print('Package imported successfully')"

print_success "Staging CI pipeline completed successfully! 🎉"
print_status "Package is ready for staging deployment."
