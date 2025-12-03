# Test Maintenance Guide

This document outlines maintenance procedures for test fixtures, baselines, and the overall test infrastructure.

## Table of Contents

- [Test Fixtures Maintenance](#test-fixtures-maintenance)
- [Performance Baselines](#performance-baselines)
- [Test Data Management](#test-data-management)
- [Container Maintenance](#container-maintenance)
- [Dependency Updates](#dependency-updates)
- [Test Coverage Monitoring](#test-coverage-monitoring)
- [Regular Maintenance Schedule](#regular-maintenance-schedule)

## Test Fixtures Maintenance

### Unit Test Fixtures

Location: `tests/unit/`

**Maintenance Tasks**:

1. **Update Mock Data**: Keep mock return values current with actual command outputs
   ```bash
   # Review actual command outputs
   ls -la /tmp
   grep "pattern" file.txt
   
   # Update mocks in test files to match
   ```

2. **Verify Mock Accuracy**: Ensure mocks represent real-world scenarios
   - Test with actual commands periodically
   - Update mocks when command behavior changes
   - Document any assumptions in mock data

3. **Clean Up Unused Fixtures**: Remove fixtures for deprecated commands

### Integration Test Fixtures

Location: `tests/integration/fixtures/`

**Maintenance Tasks**:

1. **Update Sample Data** (`sample_data.json`):
   ```bash
   # Review and update test data
   cat tests/integration/fixtures/sample_data.json
   
   # Ensure data represents current use cases
   # Update when data structures change
   ```

2. **Maintain Test Scripts** (`test_scripts/`):
   ```bash
   # Test scripts should be executable and current
   chmod +x tests/integration/fixtures/test_scripts/*.py
   
   # Update Python scripts for Python version compatibility
   # Test scripts with: python3 tests/integration/fixtures/test_scripts/data_processor.py
   ```

3. **Update Expected Outputs** (`expected_outputs/`):
   ```bash
   # Regenerate expected outputs when command behavior changes
   # Run actual commands and capture outputs
   ls -l /tmp > tests/integration/fixtures/expected_outputs/ls_output.txt
   ```

4. **Version Control**: Keep fixtures in version control, document changes

### E2E Test Fixtures

Location: `tests/e2e/scenarios/*/fixtures/`

**Maintenance Tasks**:

1. **Scenario-Specific Data**: Update data for each scenario category
2. **Real-World Scenarios**: Ensure fixtures represent production-like data
3. **Data Volume**: Maintain appropriate data sizes for performance testing

## Performance Baselines

### Baseline Collection

Location: `performance_baselines/` or `tests/e2e/baselines/`

**Maintenance Tasks**:

1. **Regular Baseline Updates**:
   ```bash
   # Collect new baselines after significant changes
   python -m tests.e2e.utilities.baseline_collector --scenario data_pipeline --duration 60
   python -m tests.e2e.utilities.baseline_collector --scenario automation_workflows --duration 60
   python -m tests.e2e.utilities.baseline_collector --scenario error_handling --duration 60
   ```

2. **Baseline Review**:
   ```bash
   # List available baselines
   python -m tests.e2e.utilities.baseline_collector --list
   
   # Review baseline metrics
   cat performance_baselines/*_baseline.json
   ```

3. **Baseline Cleanup**:
   ```bash
   # Remove old baselines (older than 30 days)
   python -m tests.e2e.utilities.baseline_collector --cleanup 30
   ```

### Baseline Comparison

**When to Update Baselines**:

- After performance optimizations (intentional changes)
- After major feature additions
- When performance characteristics legitimately change
- Quarterly review of baseline relevance

**When NOT to Update Baselines**:

- Performance regressions (fix the regression instead)
- Temporary performance issues
- Test environment changes (update environment instead)

### Baseline Documentation

Document baseline changes:

```markdown
# Baseline Update Log

## 2024-01-15 - Data Pipeline Baseline Update
- Reason: Optimized data processing algorithm
- Expected improvement: 20% faster processing
- New baseline: 45.2s (was 56.8s)
- Validated: Yes
```

## Test Data Management

### Data Lifecycle

1. **Creation**: Create test data with realistic, representative values
2. **Versioning**: Keep test data in version control
3. **Updates**: Update data when requirements change
4. **Cleanup**: Remove obsolete test data

### Data Size Management

- **Unit Tests**: Minimal data (fast execution)
- **Integration Tests**: Moderate data (10KB-1MB per fixture)
- **E2E Tests**: Realistic data volumes (1MB-100MB)

### Data Privacy and Security

- **No Real User Data**: Never use production user data in tests
- **Sanitized Data**: Use anonymized or synthetic data
- **Credentials**: Never commit real credentials or secrets
- **Sensitive Information**: Remove or mask sensitive data

### Data Refresh Schedule

- **Quarterly**: Review and update all test data
- **After Major Changes**: Update data when system behavior changes
- **As Needed**: Update when tests fail due to outdated data

## Container Maintenance

### Container Image Updates

**Update Debian Templates**:

```bash
# Update LXC templates
sudo apt-get update
sudo apt-get upgrade lxc-templates

# Recreate containers with updated templates
# (Containers are recreated automatically during tests)
```

### Container Cleanup

**Regular Cleanup**:

```bash
# List all containers
sudo lxc-ls -1

# Stop and remove old test containers
sudo lxc-stop -n <old-container> 2>/dev/null || true
sudo lxc-destroy -n <old-container>

# Clean up container storage
sudo du -sh /var/lib/lxc/*
```

**Automated Cleanup**:

```bash
# Use cleanup manager
python -m tests.e2e.utilities.cleanup_manager --comprehensive

# Or cleanup specific resources
python -m tests.e2e.utilities.cleanup_manager --containers --container-pattern "mancer-*"
```

### Container Configuration Updates

When updating container configurations:

1. **Document Changes**: Update `tests/integration/lxc/container_setup.sh`
2. **Test Changes**: Verify new configuration works
3. **Update Documentation**: Update `docs/testing/lxc-setup.md` if needed

## Dependency Updates

### Python Dependencies

**Update Schedule**: Weekly (via Dependabot)

**Manual Updates**:

```bash
# Update requirements
pip install --upgrade -r requirements.txt

# Test with updated dependencies
pytest tests/unit/ -v

# Update requirements.txt if tests pass
pip freeze > requirements.txt
```

**Testing After Updates**:

1. Run unit tests: `pytest tests/unit/`
2. Run integration tests: `pytest tests/integration/ --run-integration`
3. Run E2E tests: `pytest tests/e2e/ --run-e2e`
4. Check for breaking changes

### System Dependencies

**LXC Updates**:

```bash
# Update LXC packages
sudo apt-get update
sudo apt-get upgrade lxc lxc-utils lxc-templates

# Verify compatibility
lxc-ls --version
pytest tests/integration/ --run-integration
```

**Other System Tools**:

- Keep coreutils, Python, and other system tools updated
- Test compatibility after system updates

## Test Coverage Monitoring

### Coverage Goals

- **Unit Tests**: 85%+ coverage for core functionality
- **Integration Tests**: Cover all supported commands
- **E2E Tests**: Cover critical workflows

### Coverage Reports

**Generate Reports**:

```bash
# Unit test coverage
pytest tests/unit/ --cov=src/mancer --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Review Coverage**:

1. Identify untested code paths
2. Add tests for critical untested areas
3. Document why certain areas are not tested (if intentional)

### Coverage Maintenance

- **Monthly Review**: Review coverage reports monthly
- **Gap Analysis**: Identify and fill coverage gaps
- **Documentation**: Document coverage goals and exceptions

## Regular Maintenance Schedule

### Daily

- Monitor CI/CD test results
- Review test failures and fix issues
- Check for dependency security updates

### Weekly

- Review and merge Dependabot PRs
- Update test fixtures if needed
- Clean up old test artifacts

### Monthly

- Review test coverage reports
- Update test data if outdated
- Review and update performance baselines
- Clean up old containers and artifacts

### Quarterly

- Comprehensive test suite review
- Update all test fixtures
- Review and update documentation
- Performance baseline refresh
- Dependency audit

### As Needed

- Update fixtures when system behavior changes
- Update baselines after performance optimizations
- Fix test failures immediately
- Update documentation when adding new tests

## Maintenance Tools

### Automated Tools

1. **Dependabot**: Automated dependency updates (`.github/dependabot.yml`)
2. **CI/CD**: Automated test execution and reporting
3. **Cleanup Manager**: `tests/e2e/utilities/cleanup_manager.py`
4. **Baseline Collector**: `tests/e2e/utilities/baseline_collector.py`

### Manual Tools

1. **Test Execution**: `pytest` with various flags
2. **Container Management**: LXC command-line tools
3. **Log Analysis**: `tests/e2e/utilities/log_analyzer.py`
4. **Performance Monitoring**: `tests/e2e/utilities/performance_monitor.py`

## Maintenance Checklist

### Before Release

- [ ] All tests passing
- [ ] Test coverage meets goals
- [ ] Performance baselines updated
- [ ] Test fixtures reviewed and updated
- [ ] Documentation up to date
- [ ] Dependencies updated and tested
- [ ] Container configurations verified

### Monthly Review

- [ ] Review test coverage reports
- [ ] Update outdated test fixtures
- [ ] Clean up old containers and artifacts
- [ ] Review performance baselines
- [ ] Update test documentation
- [ ] Audit test dependencies

### Quarterly Review

- [ ] Comprehensive test suite audit
- [ ] Update all test fixtures
- [ ] Refresh performance baselines
- [ ] Review and update all documentation
- [ ] Dependency security audit
- [ ] Test infrastructure optimization

## Troubleshooting Maintenance Issues

### Test Fixtures Out of Date

**Symptoms**: Tests fail with data format errors

**Solution**:
```bash
# Update fixtures to match current data structures
# Test with actual commands to verify formats
# Update fixture files
```

### Baselines Too Old

**Symptoms**: False regression alerts

**Solution**:
```bash
# Collect new baselines
python -m tests.e2e.utilities.baseline_collector --scenario <scenario> --duration 60
```

### Container Issues

**Symptoms**: Container creation failures

**Solution**:
```bash
# Clean up old containers
python -m tests.e2e.utilities.cleanup_manager --containers

# Update LXC templates
sudo apt-get update && sudo apt-get upgrade lxc-templates
```

## Additional Resources

- **Test Plan**: `docs/testing/plan.md`
- **LXC Setup**: `docs/testing/lxc-setup.md`
- **Integration Tests**: `tests/integration/README.md`
- **E2E Tests**: `tests/e2e/README.md`
- **CI/CD Configuration**: `.github/workflows/ci.yml`
