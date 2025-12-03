# Integration Tests

This directory contains integration tests for the Mancer framework. These tests run against real LXC containers with actual coreutils and Python execution, validating end-to-end functionality in isolated environments.

## Overview

Integration tests differ from unit tests by:

- **Real Execution**: Actual commands run in LXC containers (no mocks)
- **Environment**: Isolated Debian containers with full system tools
- **Duration**: Moderate execution time (15-30 minutes for full suite)
- **Purpose**: Validate wrapper behavior with real system interactions

## Directory Structure

```
tests/integration/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest configuration for integration tests
├── commands/                # Command-specific integration tests
│   ├── test_ls_integration.py
│   ├── test_grep_integration.py
│   ├── test_cat_integration.py
│   ├── test_file_ops_integration.py
│   └── test_command_chains_integration.py
├── fixtures/                # Test data and scripts
│   ├── sample_data.json
│   ├── test_scripts/
│   │   ├── data_processor.py
│   │   └── file_operations.py
│   └── expected_outputs/
│       ├── ls_output.txt
│       └── df_output.txt
└── lxc/                     # LXC container management
    ├── container_setup.sh   # Container provisioning script
    ├── fixtures.py          # Pytest fixtures for LXC
    └── conftest.py          # LXC-specific configuration
```

## Prerequisites

### System Requirements

1. **LXC installed and configured**
   ```bash
   sudo apt-get update
   sudo apt-get install -y lxc lxc-utils lxc-templates bridge-utils
   ```

2. **LXC network configured**
   ```bash
   sudo systemctl start lxc-net
   sudo usermod -aG lxc $USER
   # Log out and back in for group changes to take effect
   ```

3. **Sudo access** (required for container management)

4. **Python dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-xdist psutil
   ```

### LXC Setup Verification

Verify LXC is properly configured:

```bash
# Check LXC version
lxc-ls --version

# Check network bridge
ip link show lxcbr0

# Test container creation (optional)
sudo lxc-create -n test-container -t debian -- --release bullseye
sudo lxc-destroy -n test-container
```

## Running Integration Tests

### Basic Execution

```bash
# Run all integration tests
pytest tests/integration/ --run-integration

# Run specific test file
pytest tests/integration/commands/test_ls_integration.py --run-integration

# Run with verbose output
pytest tests/integration/ --run-integration -v

# Run specific test method
pytest tests/integration/commands/test_ls_integration.py::TestLsIntegration::test_ls_basic_directory_listing --run-integration
```

### Configuration Options

- `--run-integration`: Required flag to enable integration tests
- `--integration-container`: Specify container name (default: `mancer-integration-test`)
- `--keep-containers`: Keep containers running after tests (for debugging)
- `--integration-timeout`: Timeout for integration tests in seconds (default: 300)

### Example Commands

```bash
# Run with custom container name
pytest tests/integration/ --run-integration --integration-container my-test-container

# Run and keep containers for inspection
pytest tests/integration/ --run-integration --keep-containers

# Run with extended timeout
pytest tests/integration/ --run-integration --integration-timeout 600
```

## Container Management

### Automatic Container Setup

The integration test suite automatically manages LXC containers:

1. **Container Creation**: Uses `container_setup.sh` to provision Debian containers
2. **Service Configuration**: Installs Python, coreutils, and required tools
3. **Workspace Setup**: Creates isolated test workspaces per test
4. **Cleanup**: Automatically cleans up containers after test completion

### Manual Container Setup

If you need to manually set up a container for debugging:

```bash
# Run setup script
cd tests/integration/lxc
sudo ./container_setup.sh

# Or with custom parameters
CONTAINER_NAME=my-test-container sudo ./container_setup.sh
```

### Container Inspection

Access containers for debugging:

```bash
# List containers
sudo lxc-ls -1

# Check container status
sudo lxc-info -n mancer-integration-test

# Access container shell
sudo lxc-attach -n mancer-integration-test -- /bin/bash

# View container logs
sudo journalctl -u lxc@mancer-integration-test
```

## Test Scenarios

### Command Integration Tests

Located in `tests/integration/commands/`:

- **`test_ls_integration.py`**: Directory listing operations
- **`test_grep_integration.py`**: Pattern searching and filtering
- **`test_cat_integration.py`**: File reading and concatenation
- **`test_file_ops_integration.py`**: Multi-file operations
- **`test_command_chains_integration.py`**: Pipeline and command chaining

Each test file contains multiple scenarios:
- Basic command execution
- Command options and flags
- Error handling
- Edge cases
- Multi-file operations

### Test Data

Test fixtures are located in `tests/integration/fixtures/`:

- **`sample_data.json`**: Sample data for processing tests
- **`test_scripts/`**: Python scripts for realistic scenarios
- **`expected_outputs/`**: Reference outputs for validation

## Troubleshooting

### Common Issues

#### 1. Container Creation Fails

**Symptoms**: `lxc-create` fails with permission or template errors

**Solutions**:
```bash
# Check LXC templates are installed
ls /usr/share/lxc/templates/

# Verify network bridge exists
ip link show lxcbr0

# Check disk space
df -h

# Verify user is in lxc group
groups | grep lxc
```

#### 2. Network Connectivity Issues

**Symptoms**: Containers cannot reach external network or each other

**Solutions**:
```bash
# Restart LXC networking
sudo systemctl restart lxc-net

# Check bridge configuration
ip addr show lxcbr0

# Verify NAT rules
sudo iptables -t nat -L -n
```

#### 3. Permission Denied Errors

**Symptoms**: Cannot execute commands in containers

**Solutions**:
```bash
# Ensure sudo access
sudo -v

# Check container permissions
sudo lxc-info -n mancer-integration-test -c lxc.cgroup.devices.allow

# Verify test user exists in container
sudo lxc-attach -n mancer-integration-test -- id mancer
```

#### 4. Container Startup Timeout

**Symptoms**: Tests fail with container startup timeouts

**Solutions**:
```bash
# Increase timeout in test configuration
pytest tests/integration/ --run-integration --integration-timeout 600

# Check container logs
sudo lxc-info -n mancer-integration-test -L

# Verify system resources
free -h
df -h
```

#### 5. Test Isolation Issues

**Symptoms**: Tests interfere with each other

**Solutions**:
- Each test gets an isolated workspace
- Containers are session-scoped (shared across test session)
- Use `--keep-containers` to inspect state between tests

### Debugging Tips

1. **Keep Containers Running**:
   ```bash
   pytest tests/integration/ --run-integration --keep-containers
   ```

2. **Inspect Container State**:
   ```bash
   sudo lxc-attach -n mancer-integration-test -- ls -la /tmp/integration_workspace
   ```

3. **View Test Logs**:
   ```bash
   tail -f e2e_test.log
   ```

4. **Run Single Test in Isolation**:
   ```bash
   pytest tests/integration/commands/test_ls_integration.py::TestLsIntegration::test_ls_basic_directory_listing --run-integration -v -s
   ```

## Best Practices

### Writing Integration Tests

1. **Use Realistic Data**: Use fixtures that represent real-world scenarios
2. **Test Error Cases**: Include negative test cases (missing files, permissions, etc.)
3. **Clean Up**: Tests should clean up after themselves (automatic via fixtures)
4. **Isolation**: Each test should be independent and runnable in isolation
5. **Documentation**: Add docstrings explaining what each test validates

### Performance Considerations

- Integration tests are slower than unit tests
- Use `pytest-xdist` for parallel execution when possible
- Consider test execution time when adding new tests
- Use `@pytest.mark.slow` for tests that take >30 seconds

### Maintenance

- **Update Fixtures**: Keep test data current and representative
- **Container Images**: Periodically update Debian templates
- **Dependencies**: Keep Python and system dependencies up to date
- **Test Coverage**: Ensure new commands have integration tests

## CI/CD Integration

Integration tests run in CI/CD:

- **Manual Trigger**: Via workflow dispatch with `run_integration: true`
- **Release Branches**: Automatically on `release/*` branches
- **Artifacts**: Test logs and container state saved for debugging

See `.github/workflows/ci.yml` for CI configuration.

## Related Documentation

- **Unit Tests**: See `tests/unit/README.md` (if exists)
- **E2E Tests**: See `tests/e2e/README.md`
- **Test Plan**: See `docs/testing/plan.md`
- **LXC Documentation**: https://linuxcontainers.org/lxc/

## Support

For issues or questions:

1. Check this README and troubleshooting section
2. Review test logs in `e2e_test.log`
3. Inspect container state with `lxc-attach`
4. Create an issue using the test failure template: `.github/ISSUE_TEMPLATE/test_failure.md`
