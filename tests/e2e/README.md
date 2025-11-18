# End-to-End Tests

This directory contains End-to-End (E2E) tests for the Mancer framework. These tests validate complete workflows and system integration in production-like environments using multiple LXC containers.

## Overview

E2E tests differ from unit and integration tests by:

- **Scope**: Complete user workflows from start to finish
- **Environment**: Multi-container LXC setups simulating production
- **Duration**: Longer execution time (minutes vs seconds)
- **Purpose**: Validate system behavior under realistic conditions

## Directory Structure

```
tests/e2e/
├── scenarios/                 # Test scenarios by category
│   ├── data_pipeline/         # Data processing workflows
│   ├── automation_workflows/  # System automation scenarios
│   └── error_handling/        # Failure and recovery tests
├── lxc/                       # Multi-container LXC management
├── utilities/                 # E2E testing utilities
├── conftest.py               # Pytest configuration
└── README.md                 # This file
```

## Running E2E Tests

### Prerequisites

1. **LXC installed and configured**
2. **Sudo access for container management**
3. **At least 4GB RAM available**
4. **Python dependencies installed**

### Basic Execution

```bash
# Run all E2E tests
pytest tests/e2e/ --run-e2e

# Run specific scenario
pytest tests/e2e/scenarios/data_pipeline/ --run-e2e

# Run with performance monitoring
pytest tests/e2e/ --run-e2e --performance-monitoring

# Run with fault injection
pytest tests/e2e/scenarios/error_handling/ --run-e2e --chaos-mode
```

### Configuration Options

- `--run-e2e`: Enable E2E test execution
- `--e2e-containers`: Specify container names (default: mancer-e2e-app,mancer-e2e-db)
- `--performance-monitoring`: Enable detailed performance tracking
- `--baseline-compare`: Compare against baseline metrics
- `--chaos-mode`: Enable fault injection for resilience testing

## Test Scenarios

### Data Pipeline Scenarios

Located in `scenarios/data_pipeline/`:

- **Data Ingestion**: Complete data processing pipeline from source to output
- **Batch Processing**: Large-scale data operations and validation
- **Data Quality**: Validation of processed data integrity

### Automation Workflows

Located in `scenarios/automation_workflows/`:

- **Deployment**: Automated deployment and configuration
- **Backup**: Backup creation, verification, and restoration
- **Monitoring**: System health monitoring and alerting

### Error Handling

Located in `scenarios/error_handling/`:

- **Failure Recovery**: System behavior during component failures
- **Graceful Degradation**: Continued operation with reduced functionality
- **Data Recovery**: Loss and recovery of critical data

## Performance Monitoring

When `--performance-monitoring` is enabled:

- **Execution Time**: Per-operation timing
- **Resource Usage**: CPU, memory, disk, and network metrics
- **Baseline Comparison**: Regression detection against stored baselines
- **Performance Reports**: Generated in test artifacts

## Multi-Container Setup

E2E tests use multiple LXC containers to simulate distributed systems:

- **App Container**: Main application environment
- **DB Container**: Database and data storage
- **Worker Container**: Background processing (when needed)

Containers are automatically provisioned, configured, and networked for each test scenario.

## Test Data Management

- **Fixtures**: Version-controlled test data in scenario directories
- **Isolation**: Each test gets clean container state
- **Cleanup**: Automatic resource cleanup after test completion
- **Artifacts**: Test outputs saved for debugging and analysis

## Debugging E2E Tests

### Logs and Artifacts

- **Container Logs**: Available in `/var/log/lxc/<container>/`
- **Test Logs**: `e2e_test.log` in working directory
- **Performance Data**: JSON files with detailed metrics
- **Screenshots**: UI automation captures (when applicable)

### Keeping Containers for Debugging

```bash
# Keep containers running after test failure
pytest tests/e2e/ --run-e2e --keep-containers

# Manual container inspection
sudo lxc-attach -n mancer-e2e-app -- /bin/bash
```

### Common Issues

1. **Container Creation Failures**: Check LXC configuration and disk space
2. **Network Issues**: Verify LXC bridge setup
3. **Permission Errors**: Ensure sudo access for LXC commands
4. **Resource Exhaustion**: Monitor memory and CPU usage

## Development Guidelines

### Adding New Scenarios

1. Create scenario directory under `scenarios/`
2. Implement test files with descriptive names
3. Add scenario-specific fixtures and data
4. Update this README with scenario description
5. Add appropriate pytest markers

### Performance Baselines

- Baselines stored in `utilities/baselines/`
- Updated via automated jobs or manual runs
- Compared during CI/CD for regression detection

## CI/CD Integration

E2E tests are typically run:

- **Nightly**: Full suite on main branch
- **Pre-release**: Complete validation before releases
- **On-demand**: Manual trigger for specific scenarios

See `.github/workflows/` for CI configuration.