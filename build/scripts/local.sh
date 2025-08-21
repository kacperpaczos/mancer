#!/bin/bash

# Local CI Script for Mancer
# This script simulates CI pipeline locally

set -e

echo "🚀 Starting local CI pipeline..."

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
    print_warning "No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
fi

# Install dependencies
print_status "Installing dependencies..."
pip install -e .
pip install -r requirements.txt

# Run pre-commit hooks
print_status "Running pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit run --all-files
else
    print_warning "pre-commit not found, skipping..."
fi

# Run tests
print_status "Running tests..."
python -m pytest tests/ -v --tb=short

# Run linting
print_status "Running linting..."
if command -v ruff &> /dev/null; then
    ruff check src/ tests/
else
    print_warning "ruff not found, skipping..."
fi

# Run type checking
print_status "Running type checking..."
if command -v mypy &> /dev/null; then
    mypy src/
else
    print_warning "mypy not found, skipping..."
fi

# Build package
print_status "Building package..."
python -m build

print_success "Local CI pipeline completed successfully! 🎉"
