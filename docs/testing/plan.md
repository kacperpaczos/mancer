# Bash Wrapper Test Strategy

This document captures the agreed structure for testing the Bash wrapper that orchestrates Python scripts and GNU coreutils. It focuses on deterministic unit coverage, faithful integration checks inside Debian LXC containers, and optional end-to-end workflows that mirror real operator flows.

## Test Suite Layout

```
tests/
├─ unit/                    # Unit tests: one file per coreutils command
│   ├─ test_ls.py          # All ls command scenarios
│   ├─ test_grep.py        # All grep command scenarios
│   ├─ test_cat.py         # All cat command scenarios
│   ├─ test_ps.py          # All ps command scenarios
│   ├─ test_df.py          # All df command scenarios
│   ├─ test_hostname.py    # All hostname command scenarios
│   ├─ test_echo.py        # All echo command scenarios
│   ├─ test_wc.py          # All wc command scenarios
│   ├─ test_find.py        # All find command scenarios
│   └─ test_systemctl.py   # All systemctl command scenarios
├─ integration/            # Integration tests in LXC containers
│   ├─ fixtures/           # Test data and scripts
│   ├─ lxc/                # LXC management utilities
│   ├─ commands/           # Command integration tests
│   └─ workflows/          # Workflow integration tests
└─ e2e/                    # End-to-end workflow tests
    ├─ scenarios/          # Categorized E2E scenarios
    ├─ lxc/                # Multi-container setup
    └─ utilities/          # Monitoring and analysis tools
```

Recommended markers:

- `@pytest.mark.unit` (default; fast, isolated mocks)
- `@pytest.mark.integration` + `@pytest.mark.lxc` (real tools/container)
- `@pytest.mark.e2e` (full workflows; run via `pytest -m e2e --run-e2e`)
- `@pytest.mark.slow` (performance-heavy tests)

## 1. Unit Test Baseline

**Structure**: One test file per coreutils command (2025 best practice: focused, maintainable test suites).

```
tests/unit/
├─ test_ls.py          # All ls command scenarios
├─ test_grep.py        # All grep command scenarios
├─ test_cat.py         # All cat command scenarios
├─ test_ps.py          # All ps command scenarios
├─ test_df.py          # All df command scenarios
├─ test_hostname.py    # All hostname command scenarios
├─ test_echo.py        # All echo command scenarios
├─ test_wc.py          # All wc command scenarios
├─ test_find.py        # All find command scenarios
└─ test_systemctl.py   # All systemctl command scenarios
```

**Scope per file**

- Command string construction and argument parsing
- stdout/stderr/codes handling
- Backend interaction (BashBackend execution)
- Version-aware behavior
- Error handling and edge cases

**Technique**

- Use `unittest.mock.patch` to replace `subprocess.run/Popen` and backend methods.
- Provide fixtures for fake stdout/stderr payloads and command contexts.
- No LXC dependencies; run locally and in CI by default.
- Each file contains multiple test functions covering different scenarios.

**Positive Scenarios (examples for ls command)**

1. `ls` without options returns directory listing
2. `ls -l` includes permissions and timestamps
3. `ls -a` shows hidden files
4. `ls /path/to/dir` works with custom paths
5. Version-aware behavior adapts to different ls versions

**Negative Scenarios (examples for ls command)**

1. Non-existent directory → exit code 2, stderr message
2. Permission denied → exit code 2, access error
3. Invalid option → exit code 2, usage message
4. Network path without support → appropriate error
5. Version incompatibility → warning in metadata

**Template Snippet** (ls command example)

```python
import pytest
from unittest.mock import patch
from mancer.infrastructure.command.system.ls_command import LsCommand
from mancer.domain.model.command_context import CommandContext

class TestLsCommand:
    """Unit tests for ls command - all scenarios in one focused file"""

    @pytest.fixture
    def context(self):
        """Test command context fixture"""
        return CommandContext()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_basic_listing(self, mock_execute, context):
        """Test basic ls command without options"""
        mock_execute.return_value = CommandResult(
            raw_output="file1.txt\nfile2.txt\n", success=True, exit_code=0
        )

        cmd = LsCommand()
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        mock_execute.assert_called_once()

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_long_format(self, mock_execute, context):
        """Test ls -l with detailed output"""
        mock_execute.return_value = CommandResult(
            raw_output="-rw-r--r-- 1 user group 1024 Jan 1 12:00 file1.txt",
            success=True, exit_code=0
        )

        cmd = LsCommand().with_option("-l")
        result = cmd.execute(context)

        assert result.success
        assert "file1.txt" in result.raw_output
        assert "1024" in result.raw_output

    @patch("mancer.infrastructure.backend.bash_backend.BashBackend.execute_command")
    def test_ls_nonexistent_directory(self, mock_execute, context):
        """Test ls with non-existent directory"""
        mock_execute.return_value = CommandResult(
            raw_output="", success=False, exit_code=2,
            error_message="ls: cannot access '/nonexistent': No such file or directory"
        )

        cmd = LsCommand("/nonexistent")
        result = cmd.execute(context)

        assert not result.success
        assert result.exit_code == 2
        assert "No such file or directory" in result.error_message
```

## 2. Integration Suite on LXC

**Directory Structure**

```
tests/integration/
├─ __init__.py
├─ fixtures/
│   ├─ sample_data.json          # Test data files
│   ├─ test_scripts/             # Python scripts for testing
│   │   ├─ data_processor.py
│   │   └─ file_operations.py
│   └─ expected_outputs/         # Reference outputs
├─ lxc/
│   ├─ container_setup.sh        # LXC container provisioning
│   ├─ fixtures.py               # Pytest fixtures for LXC
│   └─ conftest.py               # Pytest configuration
├─ commands/
│   ├─ test_ls_integration.py    # Real ls in LXC container
│   ├─ test_grep_integration.py  # Real grep in LXC container
│   ├─ test_cat_integration.py   # Real cat in LXC container
│   ├─ test_file_ops_integration.py # Multi-command file operations
│   └─ test_command_chains_integration.py # Command chaining
├─ workflows/
│   ├─ test_data_processing_workflow.py # End-to-end data processing
│   └─ test_system_monitoring_workflow.py # System monitoring workflow
└─ conftest.py                   # Integration-specific pytest config
```

**Environment Setup**

- Debian LXC container with Python 3.10+, coreutils, sshd enabled.
- Automated provisioning via `tests/integration/lxc/container_setup.sh`
- Container mounts test workspace and fixtures directory
- SSH access enabled for remote command testing

**Test Categories**

**Command Integration Tests** (`tests/integration/commands/`)

- One file per coreutils command (mirrors unit test structure)
- Tests real command execution in isolated LXC environment
- Validates command output matches expected formats
- Tests version-specific behaviors with real tools

**Workflow Integration Tests** (`tests/integration/workflows/`)

- Multi-command workflows (pipelines, sequences)
- File I/O operations across commands
- Temporary file lifecycle management
- Error propagation through command chains

**Fixtures and Configuration**

```python
# tests/integration/lxc/fixtures.py
@pytest.fixture(scope="session")
def lxc_container():
    """Provision and yield LXC container for the test session"""
    container = LXCManager.create_container("test-container")
    container.start()
    container.mount_workspace()
    yield container
    container.stop()
    container.destroy()

@pytest.fixture
def temp_workspace(lxc_container):
    """Create isolated workspace inside container"""
    workspace = lxc_container.create_temp_workspace()
    yield workspace
    lxc_container.cleanup_workspace(workspace)
```

**Positive Scenarios**

1. **Basic Command Execution**: `ls` returns directory listing with correct format
2. **Command Options**: `ls -la` includes hidden files and permissions
3. **File Operations**: `cat file.txt` outputs file content correctly
4. **Command Chaining**: `ls | grep txt` filters output properly
5. **Data Processing**: Python script reads JSON, processes data, writes output
6. **Temporary Files**: Commands create/use/cleanup temp files correctly

**Negative Scenarios**

1. **Missing Files**: Commands handle non-existent files gracefully
2. **Permission Errors**: Access denied scenarios return appropriate errors
3. **Invalid Options**: Commands reject malformed arguments
4. **Resource Limits**: Commands handle disk space/memory constraints
5. **Network Issues**: Remote commands handle connection failures
6. **Container Failures**: Tests handle container restart/crash scenarios

**Data Handling**

- Test fixtures stored in `tests/integration/fixtures/` (<10KB each)
- Version-controlled reference outputs for comparison
- Container state reset via snapshots between test runs
- Isolated workspaces prevent test interference

## 3. Optional End-to-End Flow

**Directory Structure**

```
tests/e2e/
├─ __init__.py
├─ scenarios/
│   ├─ data_pipeline/
│   │   ├─ __init__.py
│   │   ├─ test_data_ingestion_e2e.py      # Complete data processing pipeline
│   │   ├─ test_batch_processing_e2e.py    # Large-scale batch operations
│   │   └─ fixtures/                       # Scenario-specific data
│   ├─ system_monitoring/
│   │   ├─ __init__.py
│   │   ├─ test_system_health_e2e.py       # System monitoring workflow
│   │   ├─ test_log_analysis_e2e.py        # Log processing and analysis
│   │   └─ fixtures/                       # System monitoring data
│   ├─ automation_workflows/
│   │   ├─ __init__.py
│   │   ├─ test_deployment_workflow_e2e.py # Deployment automation
│   │   ├─ test_backup_workflow_e2e.py     # Backup and recovery
│   │   └─ fixtures/                       # Workflow-specific data
│   └─ error_handling/
│       ├─ __init__.py
│       ├─ test_failure_recovery_e2e.py    # Error recovery scenarios
│       ├─ test_graceful_degradation_e2e.py # System degradation handling
│       └─ fixtures/                       # Error scenario data
├─ lxc/
│   ├─ multi_container_setup.sh            # Multi-container environment
│   ├─ network_config.sh                   # Network configuration
│   ├─ fixtures.py                         # E2E-specific LXC fixtures
│   └─ monitoring.py                       # E2E monitoring utilities
├─ utilities/
│   ├─ baseline_collector.py               # Collect baseline metrics
│   ├─ performance_monitor.py              # Performance monitoring
│   ├─ log_analyzer.py                     # Log analysis utilities
│   └─ cleanup_manager.py                  # Resource cleanup
├─ conftest.py                             # E2E pytest configuration
└─ README.md                               # E2E testing documentation
```

**When to run**

- Pre-release validation (full system verification)
- Reproducing customer-reported workflows
- Benchmarking multi-step automation scenarios
- Validating system integration points

**Test Categories**

**Data Pipeline E2E** (`tests/e2e/scenarios/data_pipeline/`)

- Complete data processing workflows from ingestion to output
- Multi-format data handling (JSON, CSV, binary)
- Large dataset processing with memory/disk constraints
- Data validation and transformation chains

**System Monitoring E2E** (`tests/e2e/scenarios/system_monitoring/`)

- Real-time system health monitoring workflows
- Log aggregation and analysis pipelines
- Alert generation and notification systems
- Performance metric collection and analysis

**Automation Workflows E2E** (`tests/e2e/scenarios/automation_workflows/`)

- Deployment and configuration automation
- Backup and recovery procedures
- Maintenance and cleanup workflows
- Multi-system coordination scenarios

**Error Handling E2E** (`tests/e2e/scenarios/error_handling/`)

- Failure recovery and retry mechanisms
- Graceful degradation under resource constraints
- Error propagation through complex workflows
- Recovery from partial system failures

**Scenarios Matrix**

| Scenario | Description | Expected Outcome | Environment |
| --- | --- | --- | --- |
| **Happy Path Data Pipeline** | Ingest → Process → Validate → Export JSON data | Success, validated output, logs archived, exit 0 | Single LXC |
| **Large Batch Processing** | Process 1000+ files through pipeline | Bounded runtime (<5min), no memory leaks, all files processed | Multi-LXC |
| **System Health Monitoring** | Collect metrics → Analyze → Alert on anomalies | Correct alerts generated, metrics stored, clean shutdown | Networked LXC |
| **Deployment Automation** | Configure system → Deploy app → Verify health | App running, health checks pass, rollback possible | Multi-service LXC |
| **Failure Recovery** | Introduce failures → Verify recovery → Restore state | System recovers automatically, data preserved, alerts sent | Fault-injected LXC |
| **Resource Contention** | High load → Monitor degradation → Auto-scale | System adapts, performance maintained, no crashes | Load-tested LXC |

**Environment Setup**

- **Single LXC**: Basic workflows, isolated testing
- **Multi-LXC**: Distributed scenarios, network communication
- **Networked LXC**: Service discovery, load balancing
- **Fault-injected LXC**: Chaos engineering, resilience testing

**Execution Control**

```bash
# Run all E2E tests
pytest tests/e2e/ -m e2e --run-e2e

# Run specific scenario
pytest tests/e2e/scenarios/data_pipeline/ -m e2e

# Run with performance monitoring
pytest tests/e2e/ -m e2e --performance-monitoring --baseline-compare

# Run with fault injection
pytest tests/e2e/scenarios/error_handling/ -m e2e --chaos-mode
```

**Success Criteria**

1. **Functional Correctness**: All workflow steps complete successfully
2. **Performance**: Operations complete within time budgets
3. **Resource Usage**: No memory leaks, bounded disk usage
4. **Error Handling**: Failures trigger appropriate recovery actions
5. **Logging**: Complete audit trail of all operations
6. **Cleanup**: System returns to clean state after test completion

**Monitoring and Metrics**

- Execution time tracking per workflow step
- Resource usage (CPU, memory, disk, network)
- Error rates and failure patterns
- Performance regression detection
- Log completeness and quality analysis

## 4. Orchestration Guidance

1. **Default pipeline**: `pytest -m "unit and not slow"` runs locally on every commit.
2. **Integration gate**: run `pytest -m integration --lxc-config tests/lxc/config.yaml` when verifying real dependencies.
3. **E2E cadence**: nightly or pre-release due to runtime cost.
4. **Data hygiene**: maintain separate fixtures for positive vs negative cases; avoid reusing mutable paths.
5. **Logging**: capture wrapper stdout/stderr alongside container logs for diffing against “traditional” command runs.

## 5. Scenario Checklist

| Layer | Positive Cases | Negative Cases |
| --- | --- | --- |
| Unit | valid args, env injection, success exit | bad args, subprocess failure, encoding issues |
| Integration | file processing, command chaining, cleanup | missing deps, permission denied, container interruption |
| E2E | full workflow, batch processing, metrics capture | failure recovery, rollback validation |

## 6. Next Actions

**Phase 1: Unit Tests Foundation**

1. Create `tests/unit/` directory structure with one file per coreutils command
2. Implement unit test templates for each supported command (ls, grep, cat, ps, df, hostname, echo, wc, find, systemctl)
3. Each test file should contain 5-10 test methods covering positive/negative scenarios
4. Use `@patch` decorators to mock `BashBackend.execute_command` calls
5. Include fixtures for `CommandContext` and mock command results

**Phase 2: Integration Infrastructure**

1. Create `tests/integration/` directory structure as specified
2. Implement `tests/integration/lxc/container_setup.sh` for Debian LXC provisioning
3. Create `tests/integration/lxc/fixtures.py` with LXC container management
4. Set up `tests/integration/fixtures/` with sample data and test scripts
5. Implement command integration tests mirroring unit test structure

**Phase 3: E2E Scenarios**

1. Create `tests/e2e/` directory structure with scenario categories
2. Implement multi-container LXC setup for complex workflows
3. Create baseline performance monitoring utilities
4. Implement representative E2E scenarios from the matrix above
5. Set up automated cleanup and state management

**Phase 4: CI/CD Integration**

1. Update `pytest.ini` with markers: `markers = unit, integration, lxc, e2e, slow`
2. Configure GitHub Actions to run unit tests on every PR
3. Add integration test job triggered manually or on release branches
4. Add E2E test job for nightly runs or pre-release validation
5. Set up artifact collection for test reports and performance metrics

**Phase 5: Documentation & Maintenance**

1. Create `tests/integration/README.md` and `tests/e2e/README.md`
2. Document LXC setup requirements and troubleshooting
3. Establish maintenance procedures for test fixtures and baselines
4. Create runbooks for local development testing

This document should be treated as the canonical reference before adding or extending wrapper tests.

