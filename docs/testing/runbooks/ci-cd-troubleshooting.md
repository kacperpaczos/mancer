# CI/CD Troubleshooting Runbook

This runbook helps diagnose and fix issues with tests running in CI/CD pipelines.

## Table of Contents

- [Understanding CI/CD Test Jobs](#understanding-cicd-test-jobs)
- [Common CI/CD Issues](#common-cicd-issues)
- [Debugging CI/CD Failures](#debugging-cicd-failures)
- [Artifact Analysis](#artifact-analysis)
- [Performance Issues in CI](#performance-issues-in-ci)

## Understanding CI/CD Test Jobs

### Job Structure

The CI/CD pipeline consists of multiple jobs:

1. **Quality & Unit Tests** (`quality-and-unit`)
   - Runs on every push/PR
   - Fast execution (~5-10 minutes)
   - Lint, format, type check, unit tests

2. **Integration Tests** (`integration-tests`)
   - Manual trigger or release branches
   - Moderate execution (~15-30 minutes)
   - LXC container tests

3. **E2E Tests** (`e2e-tests`)
   - Manual trigger or nightly schedule
   - Long execution (~45-90 minutes)
   - Multi-container scenarios

4. **Test Summary** (`test-summary`)
   - Always runs after other jobs
   - Generates summary report

### Accessing CI/CD Results

1. **GitHub Actions**: Go to repository → Actions tab
2. **Job Logs**: Click on failed job → View logs
3. **Artifacts**: Download artifacts from job summary
4. **Test Reports**: Check uploaded artifacts

## Common CI/CD Issues

### Issue 1: Unit Tests Fail in CI

**Symptoms**: Tests pass locally but fail in CI

**Diagnosis**:
```bash
# Check CI logs for:
# - Python version mismatch
# - Missing dependencies
# - Environment variable issues
# - Path issues
```

**Solutions**:

1. **Python Version**:
   ```yaml
   # Verify .github/workflows/ci.yml uses correct Python version
   python-version: '3.10'
   ```

2. **Dependencies**:
   ```yaml
   # Ensure all dependencies are in requirements.txt
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   ```yaml
   # Check if tests need environment variables
   env:
     PYTHONPATH: src
   ```

4. **Path Issues**:
   ```yaml
   # Verify PYTHONPATH is set correctly
   env:
     PYTHONPATH: src
   ```

### Issue 2: Integration Tests Fail in CI

**Symptoms**: Integration tests fail with LXC errors

**Diagnosis**:
```bash
# Check CI logs for:
# - LXC installation failures
# - Permission errors
# - Network configuration issues
# - Container creation failures
```

**Solutions**:

1. **LXC Installation**:
   ```yaml
   # Verify LXC is installed in CI
   - name: Install system dependencies
     run: |
       sudo apt-get update
       sudo apt-get install -y lxc lxc-utils lxc-templates bridge-utils
   ```

2. **LXC Configuration**:
   ```yaml
   # Ensure LXC is configured
   - name: Configure LXC
     run: |
       sudo systemctl start lxc-net
       sudo usermod -aG lxc $USER
   ```

3. **Sudo Access**:
   ```yaml
   # Tests need sudo for container management
   - name: Run integration tests
     run: |
       sudo -E pytest tests/integration/ --run-integration -v
   ```

4. **Container Timeout**:
   ```yaml
   # Increase timeout if containers are slow to start
   # Check container startup time in logs
   ```

### Issue 3: E2E Tests Timeout in CI

**Symptoms**: E2E tests exceed time limits

**Diagnosis**:
```bash
# Check CI logs for:
# - Container startup delays
# - Network configuration issues
# - Resource constraints
# - Test execution time
```

**Solutions**:

1. **Increase Timeout**:
   ```yaml
   # Add timeout to job
   timeout-minutes: 120
   ```

2. **Optimize Test Execution**:
   ```bash
   # Use pytest-xdist for parallel execution
   pytest tests/e2e/ --run-e2e -n auto
   ```

3. **Reduce Test Scope**:
   ```bash
   # Run only critical tests
   pytest tests/e2e/scenarios/data_pipeline/ --run-e2e -v
   ```

4. **Check Resource Usage**:
   ```bash
   # Review performance reports in artifacts
   # Check for resource bottlenecks
   ```

### Issue 4: Performance Regressions in CI

**Symptoms**: Performance tests fail with regression alerts

**Diagnosis**:
```bash
# Check performance reports in artifacts:
# - Compare current vs baseline metrics
# - Identify which operations are slower
# - Check resource usage patterns
```

**Solutions**:

1. **Review Baseline**:
   ```bash
   # Check if baseline is current
   # Update baseline if change is expected
   ```

2. **Investigate Regression**:
   ```bash
   # Review performance reports
   # Identify slow operations
   # Check for resource constraints
   ```

3. **Update Baseline** (if change is expected):
   ```bash
   # Update baseline via workflow dispatch
   # Or manually update baseline files
   ```

4. **Fix Performance Issue**:
   ```bash
   # Optimize slow operations
   # Reduce resource usage
   # Fix memory leaks
   ```

## Debugging CI/CD Failures

### Step 1: Identify Failing Job

1. Go to GitHub Actions → Failed workflow
2. Identify which job failed
3. Check job dependencies

### Step 2: Review Job Logs

1. Click on failed job
2. Expand failed step
3. Review error messages
4. Check for stack traces

### Step 3: Download Artifacts

1. Go to job summary
2. Download relevant artifacts:
   - Test logs
   - Coverage reports
   - Performance reports
   - Container logs

### Step 4: Reproduce Locally

```bash
# Try to reproduce CI failure locally
# Use same Python version
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run same test command as CI
pytest tests/unit/ -v
```

### Step 5: Compare Environments

```bash
# Check differences between local and CI:
# - Python version
# - Dependencies versions
# - System configuration
# - Environment variables
```

## Artifact Analysis

### Coverage Reports

**Location**: `unit-test-coverage` artifact

**Analysis**:
```bash
# Download and extract artifact
# Open htmlcov/index.html in browser
# Review coverage by file
# Identify uncovered code paths
```

### Performance Reports

**Location**: `e2e-test-artifacts` artifact

**Analysis**:
```bash
# Download performance reports
# Review JSON files for metrics
# Check regression reports
# Compare with baselines
```

### Test Logs

**Location**: `integration-test-logs` or `e2e-test-artifacts`

**Analysis**:
```bash
# Download logs
# Search for errors
grep -i "error\|fail\|exception" *.log

# Review test execution
tail -100 e2e_test.log

# Use log analyzer
python -m tests.e2e.utilities.log_analyzer --log-files e2e_test.log
```

### Container Logs

**Location**: Container-specific logs in artifacts

**Analysis**:
```bash
# Review container startup logs
# Check for configuration errors
# Verify network setup
# Review service status
```

## Performance Issues in CI

### Slow Test Execution

**Symptoms**: Tests take longer than expected

**Diagnosis**:
- Check test execution time in logs
- Review parallel execution settings
- Check for resource constraints

**Solutions**:

1. **Enable Parallel Execution**:
   ```yaml
   - name: Run tests
     run: |
       pytest tests/unit/ -n auto
   ```

2. **Optimize Test Selection**:
   ```yaml
   # Run only relevant tests
   pytest tests/unit/test_specific.py
   ```

3. **Cache Dependencies**:
   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

### Resource Constraints

**Symptoms**: Tests fail due to memory/CPU limits

**Solutions**:

1. **Increase Runner Resources**:
   ```yaml
   # Use larger runner (if available)
   runs-on: ubuntu-latest  # or ubuntu-latest-4-cores
   ```

2. **Limit Parallel Execution**:
   ```yaml
   # Reduce parallel workers
   pytest tests/unit/ -n 2
   ```

3. **Optimize Container Resources**:
   ```bash
   # Set container resource limits
   sudo lxc-cgroup -n container memory.limit_in_bytes 512M
   ```

## Best Practices for CI/CD

### 1. Fast Feedback

- Run unit tests on every commit
- Keep unit tests fast (<10 minutes)
- Use parallel execution

### 2. Comprehensive Validation

- Run integration tests on release branches
- Run E2E tests nightly or before releases
- Validate performance before releases

### 3. Artifact Management

- Keep artifacts for debugging
- Set appropriate retention periods
- Organize artifacts by test type

### 4. Error Reporting

- Use clear error messages
- Include context in failures
- Link to relevant documentation

### 5. Maintenance

- Keep dependencies updated
- Review and update baselines
- Monitor test execution times

## Additional Resources

- **CI/CD Configuration**: `.github/workflows/ci.yml`
- **Local Development**: `docs/testing/runbooks/local-development.md`
- **LXC Setup**: `docs/testing/lxc-setup.md`
- **Test Plan**: `docs/testing/plan.md`
