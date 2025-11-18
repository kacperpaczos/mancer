---
name: Test Failure Report
about: Report a failing test in the test suite
title: "[TEST FAIL] "
labels: ["test-failure", "bug"]
assignees: ["kacperpaczos"]
---

## Test Failure Report

### Test Information
- **Test Type**: 
  - [ ] Unit Test
  - [ ] Integration Test
  - [ ] E2E Test
- **Test File**: `tests/...`
- **Test Function**: `test_...`
- **Test Markers**: (e.g., `@pytest.mark.e2e`, `@pytest.mark.integration`)

### Environment
- **OS**: 
- **Python Version**: 
- **LXC Version** (for integration/E2E): 
- **Git Commit**: 
- **Branch**: 

### Failure Details
**Error Message**:
```
# Paste the full error message here
```

**Stack Trace**:
```
# Paste the full stack trace here
```

**Expected Behavior**:
<!-- What should happen -->

**Actual Behavior**:
<!-- What actually happened -->

### Steps to Reproduce
1. 
2. 
3. 
4. 

### Test Command Used
```bash
# Command that reproduces the failure
pytest tests/... -v
```

### Logs and Artifacts
<!-- Attach any relevant logs, screenshots, or test artifacts -->

### Additional Context
<!-- Any additional information that might help debug this issue -->

### Checklist
- [ ] This failure is reproducible locally
- [ ] This failure occurs in CI/CD
- [ ] This is a new failure (not pre-existing)
- [ ] I have checked the test logs for additional context
- [ ] I have verified the test environment setup is correct
