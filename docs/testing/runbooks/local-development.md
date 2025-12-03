# Local Development Testing Runbook

This runbook provides step-by-step instructions for running tests locally during development.

## Table of Contents

- [Quick Start](#quick-start)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [E2E Tests](#e2e-tests)
- [Common Workflows](#common-workflows)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites Check

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check LXC installation (for integration/E2E)
lxc-ls --version

# Check pytest installation
pytest --version

# Verify project setup
cd /path/to/mancer
python3 -m pip install -r requirements.txt
```

### Fastest Test Run

```bash
# Run only unit tests (fastest, no dependencies)
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src/mancer --cov-report=term
```

## Unit Tests

### Basic Execution

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_ls.py -v

# Run specific test method
pytest tests/unit/test_ls.py::TestLsCommand::test_ls_basic_listing -v

# Run with coverage
pytest tests/unit/ --cov=src/mancer --cov-report=html
```

### Development Workflow

**1. Write/Modify Code**

```bash
# Make changes to source code
vim src/mancer/infrastructure/command/system/ls_command.py
```

**2. Run Relevant Tests**

```bash
# Run tests for the command you're working on
pytest tests/unit/test_ls.py -v

# Run with stop on first failure
pytest tests/unit/test_ls.py -x

# Run with verbose output and print statements
pytest tests/unit/test_ls.py -v -s
```

**3. Check Coverage**

```bash
# Generate coverage report
pytest tests/unit/ --cov=src/mancer --cov-report=term-missing

# View HTML coverage report
pytest tests/unit/ --cov=src/mancer --cov-report=html
open htmlcov/index.html
```

### Tips for Unit Test Development

- **Fast Iteration**: Unit tests run in seconds, use them for rapid feedback
- **Isolation**: Each test should be independent
- **Mocking**: Use `@patch` to mock external dependencies
- **Fixtures**: Use pytest fixtures for common setup

## Integration Tests

### Prerequisites

```bash
# Ensure LXC is installed and configured
sudo apt-get install -y lxc lxc-utils lxc-templates bridge-utils

# Start LXC networking
sudo systemctl start lxc-net

# Add user to lxc group (if not already)
sudo usermod -aG lxc $USER
# Log out and back in, or: newgrp lxc
```

### Basic Execution

```bash
# Run all integration tests
pytest tests/integration/ --run-integration -v

# Run specific test file
pytest tests/integration/commands/test_ls_integration.py --run-integration -v

# Run with container kept for debugging
pytest tests/integration/ --run-integration --keep-containers
```

### Development Workflow

**1. Setup Container (First Time)**

```bash
# Run container setup script
cd tests/integration/lxc
sudo ./container_setup.sh

# Or let tests create containers automatically
```

**2. Develop Integration Test**

```bash
# Write test in appropriate file
vim tests/integration/commands/test_ls_integration.py
```

**3. Run Test**

```bash
# Run your new test
pytest tests/integration/commands/test_ls_integration.py::TestLsIntegration::test_your_new_test --run-integration -v -s

# Keep container for inspection
pytest tests/integration/commands/test_ls_integration.py --run-integration --keep-containers
```

**4. Debug in Container**

```bash
# Access container shell
sudo lxc-attach -n mancer-integration-test -- /bin/bash

# Check test workspace
ls -la /tmp/integration_workspace

# Test commands manually
ls -la /tmp
grep "pattern" /tmp/test.txt
```

**5. Cleanup**

```bash
# Containers are cleaned up automatically
# Or manually:
sudo lxc-stop -n mancer-integration-test
sudo lxc-destroy -n mancer-integration-test
```

### Tips for Integration Test Development

- **Real Commands**: Test with actual system commands
- **Isolation**: Each test gets its own workspace
- **Cleanup**: Tests should clean up after themselves
- **Debugging**: Use `--keep-containers` to inspect state

## E2E Tests

### Prerequisites

```bash
# All integration test prerequisites, plus:
sudo apt-get install -y postgresql redis-server supervisor

# Setup multi-container environment
cd tests/e2e/lxc
sudo ./multi_container_setup.sh
```

### Basic Execution

```bash
# Run all E2E tests (takes 45-90 minutes)
pytest tests/e2e/ --run-e2e -v

# Run specific scenario
pytest tests/e2e/scenarios/data_pipeline/ --run-e2e -v

# Run with performance monitoring
pytest tests/e2e/ --run-e2e --performance-monitoring -v

# Run with fault injection
pytest tests/e2e/scenarios/error_handling/ --run-e2e --chaos-mode -v
```

### Development Workflow

**1. Setup Multi-Container Environment**

```bash
# Run multi-container setup
cd tests/e2e/lxc
sudo ./multi_container_setup.sh

# Verify containers are running
sudo lxc-ls -1
```

**2. Develop E2E Test**

```bash
# Write test in appropriate scenario directory
vim tests/e2e/scenarios/data_pipeline/test_data_ingestion_e2e.py
```

**3. Run Test**

```bash
# Run your new E2E test
pytest tests/e2e/scenarios/data_pipeline/test_data_ingestion_e2e.py::TestDataIngestionE2E::test_your_new_test --run-e2e -v -s

# Run with performance monitoring
pytest tests/e2e/scenarios/data_pipeline/test_data_ingestion_e2e.py --run-e2e --performance-monitoring -v
```

**4. Debug Multi-Container Setup**

```bash
# Access application container
sudo lxc-attach -n mancer-e2e-app -- /bin/bash

# Access database container
sudo lxc-attach -n mancer-e2e-db -- /bin/bash

# Check inter-container connectivity
sudo lxc-attach -n mancer-e2e-app -- ping -c 3 10.0.3.11
```

**5. Review Performance Reports**

```bash
# Check performance reports
ls -la performance_reports/

# View regression reports
cat performance_reports/*_regressions.txt

# Analyze logs
python -m tests.e2e.utilities.log_analyzer --log-files e2e_test.log --output log_analysis.json
```

### Tips for E2E Test Development

- **Full Workflows**: Test complete user workflows
- **Performance**: Monitor performance during development
- **Fault Injection**: Use chaos mode to test resilience
- **Multi-Container**: Test interactions between containers

## Common Workflows

### Workflow 1: Quick Validation Before Commit

```bash
# Run fast unit tests
pytest tests/unit/ -v

# Check code quality
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
```

### Workflow 2: Full Local Test Suite

```bash
# 1. Unit tests
pytest tests/unit/ --cov=src/mancer --cov-report=term

# 2. Integration tests
pytest tests/integration/ --run-integration -v

# 3. E2E tests (optional, time-consuming)
pytest tests/e2e/ --run-e2e -v
```

### Workflow 3: Test-Driven Development

```bash
# 1. Write failing test
pytest tests/unit/test_new_feature.py -v  # Should fail

# 2. Implement feature
vim src/mancer/...

# 3. Run test until it passes
pytest tests/unit/test_new_feature.py -v  # Should pass

# 4. Refactor and ensure tests still pass
pytest tests/unit/test_new_feature.py -v
```

### Workflow 4: Debugging Failing Test

```bash
# Run with verbose output and print statements
pytest tests/unit/test_failing.py -v -s

# Run with debugger
pytest tests/unit/test_failing.py --pdb

# Run with detailed traceback
pytest tests/unit/test_failing.py -vv --tb=long

# For integration tests, keep container
pytest tests/integration/commands/test_failing.py --run-integration --keep-containers -v -s
```

### Workflow 5: Performance Testing

```bash
# Collect baseline
python -m tests.e2e.utilities.baseline_collector --test-name test_performance --duration 60

# Run test with monitoring
pytest tests/e2e/ --run-e2e --performance-monitoring -v

# Compare with baseline
python -m tests.e2e.utilities.performance_monitor --test-name test_performance --baseline-dir performance_baselines
```

## Debugging

### Unit Test Debugging

```bash
# Use Python debugger
pytest tests/unit/test_debug.py --pdb

# Print debug output
pytest tests/unit/test_debug.py -v -s

# Set breakpoints in code
import pdb; pdb.set_trace()
```

### Integration Test Debugging

```bash
# Keep container for inspection
pytest tests/integration/ --run-integration --keep-containers

# Access container
sudo lxc-attach -n mancer-integration-test -- /bin/bash

# Check test workspace
sudo lxc-attach -n mancer-integration-test -- ls -la /tmp/integration_workspace

# View container logs
sudo journalctl -u lxc@mancer-integration-test
```

### E2E Test Debugging

```bash
# Run with verbose output
pytest tests/e2e/ --run-e2e -v -s

# Check performance reports
cat performance_reports/*_performance.json

# Analyze logs
python -m tests.e2e.utilities.log_analyzer --log-files e2e_test.log --output debug_analysis.json

# Access containers
sudo lxc-attach -n mancer-e2e-app -- /bin/bash
sudo lxc-attach -n mancer-e2e-db -- /bin/bash
```

## Troubleshooting

### Issue: Tests Fail Locally But Pass in CI

**Check**:
- Python version matches CI
- Dependencies are up to date
- Environment variables are set correctly
- LXC is properly configured (for integration/E2E)

**Solution**:
```bash
# Sync with CI environment
pip install -r requirements.txt
python --version  # Should match CI

# For integration/E2E, verify LXC
sudo systemctl status lxc-net
```

### Issue: Integration Tests Fail

**Check**:
- LXC is installed and running
- User is in lxc group
- Network bridge exists
- Containers can be created

**Solution**:
```bash
# Verify LXC setup
sudo systemctl start lxc-net
groups | grep lxc

# Test container creation
sudo lxc-create -n test -t debian -- --release bullseye
sudo lxc-destroy -n test
```

### Issue: E2E Tests Timeout

**Check**:
- System resources (CPU, RAM, disk)
- Container startup time
- Network connectivity

**Solution**:
```bash
# Check resources
free -h
df -h

# Increase timeout
pytest tests/e2e/ --run-e2e --integration-timeout 600

# Check container status
sudo lxc-ls -1
sudo lxc-info -n mancer-e2e-app
```

### Issue: Performance Regressions

**Check**:
- Baseline is current
- System load is normal
- No other processes interfering

**Solution**:
```bash
# Update baseline if change is expected
python -m tests.e2e.utilities.baseline_collector --test-name test_name --duration 60

# Check system load
top
iostat 1
```

## Additional Resources

- **Test Plan**: `docs/testing/plan.md`
- **LXC Setup**: `docs/testing/lxc-setup.md`
- **Maintenance Guide**: `docs/testing/maintenance.md`
- **Integration Tests**: `tests/integration/README.md`
- **E2E Tests**: `tests/e2e/README.md`
