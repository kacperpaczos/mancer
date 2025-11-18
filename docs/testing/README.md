# Mancer Testing Documentation

Welcome to the Mancer testing documentation. This directory contains comprehensive documentation for the test suite, including setup guides, runbooks, and maintenance procedures.

## Documentation Index

### Core Documentation

- **[Test Plan](plan.md)** - Comprehensive test strategy and architecture
  - Test structure and organization
  - Unit, integration, and E2E test definitions
  - Implementation phases and roadmap

- **[LXC Setup Guide](lxc-setup.md)** - LXC container setup and configuration
  - Installation and configuration
  - Network setup
  - Troubleshooting guide
  - Advanced configuration

- **[Maintenance Guide](maintenance.md)** - Test maintenance procedures
  - Fixture maintenance
  - Baseline management
  - Dependency updates
  - Regular maintenance schedule

### Runbooks

- **[Local Development Runbook](runbooks/local-development.md)** - Local testing workflows
  - Quick start guide
  - Unit, integration, and E2E test execution
  - Common development workflows
  - Debugging techniques

- **[CI/CD Troubleshooting Runbook](runbooks/ci-cd-troubleshooting.md)** - CI/CD debugging
  - Understanding CI/CD jobs
  - Common issues and solutions
  - Artifact analysis
  - Performance troubleshooting

### Test-Specific Documentation

- **[Integration Tests README](../../tests/integration/README.md)** - Integration test guide
  - Running integration tests
  - Container management
  - Test scenarios
  - Troubleshooting

- **[E2E Tests README](../../tests/e2e/README.md)** - End-to-end test guide
  - E2E test execution
  - Multi-container setup
  - Performance monitoring
  - Scenario documentation

## Quick Links

### Getting Started

1. **New to Testing?** Start with [Test Plan](plan.md)
2. **Setting Up LXC?** See [LXC Setup Guide](lxc-setup.md)
3. **Running Tests Locally?** Check [Local Development Runbook](runbooks/local-development.md)

### Common Tasks

- **Run Unit Tests**: `pytest tests/unit/ -v`
- **Run Integration Tests**: `pytest tests/integration/ --run-integration -v`
- **Run E2E Tests**: `pytest tests/e2e/ --run-e2e -v`
- **Setup LXC**: See [LXC Setup Guide](lxc-setup.md)

### Troubleshooting

- **Tests Failing Locally?** See [Local Development Runbook](runbooks/local-development.md#troubleshooting)
- **CI/CD Issues?** See [CI/CD Troubleshooting Runbook](runbooks/ci-cd-troubleshooting.md)
- **LXC Problems?** See [LXC Setup Guide](lxc-setup.md#troubleshooting)
- **Maintenance Questions?** See [Maintenance Guide](maintenance.md)

## Test Suite Overview

### Test Layers

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Tests                            │
│  Multi-container scenarios, full workflows              │
│  Duration: 45-90 minutes                                │
│  Purpose: Validate complete system behavior             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│              Integration Tests                          │
│  Real LXC containers, actual commands                  │
│  Duration: 15-30 minutes                                │
│  Purpose: Validate wrapper with real system            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Unit Tests                             │
│  Mocked dependencies, isolated logic                    │
│  Duration: 5-10 minutes                                 │
│  Purpose: Validate core functionality                  │
└─────────────────────────────────────────────────────────┘
```

### Test Execution Strategy

- **Unit Tests**: Run on every commit/PR (fast feedback)
- **Integration Tests**: Run manually or on release branches
- **E2E Tests**: Run nightly or before releases

## Documentation Structure

```
docs/testing/
├── README.md                    # This file - documentation index
├── plan.md                      # Test strategy and architecture
├── lxc-setup.md                # LXC installation and configuration
├── maintenance.md               # Maintenance procedures
└── runbooks/
    ├── local-development.md    # Local testing workflows
    └── ci-cd-troubleshooting.md # CI/CD debugging guide
```

## Contributing to Tests

### Adding New Tests

1. **Unit Tests**: Add to `tests/unit/` following existing patterns
2. **Integration Tests**: Add to `tests/integration/commands/`
3. **E2E Tests**: Add to `tests/e2e/scenarios/` by category

### Documentation Updates

When adding new tests or features:

1. Update relevant test README if needed
2. Update [Test Plan](plan.md) if architecture changes
3. Update [Maintenance Guide](maintenance.md) if procedures change
4. Add troubleshooting info if new issues are common

## Support and Resources

### Getting Help

1. **Check Documentation**: Review relevant guides above
2. **Check Test Logs**: Review `e2e_test.log` or CI artifacts
3. **Check Issues**: Search existing issues for similar problems
4. **Create Issue**: Use `.github/ISSUE_TEMPLATE/test_failure.md`

### External Resources

- **LXC Documentation**: https://linuxcontainers.org/lxc/
- **Pytest Documentation**: https://docs.pytest.org/
- **GitHub Actions**: https://docs.github.com/en/actions

## Test Statistics

### Current Test Coverage

- **Unit Tests**: 10 coreutils commands, 50+ test methods
- **Integration Tests**: 5 command categories, 40+ test methods
- **E2E Tests**: 3 scenario categories, 10+ test methods

### Test Execution Times

- **Unit Tests**: ~5-10 minutes
- **Integration Tests**: ~15-30 minutes
- **E2E Tests**: ~45-90 minutes

## Maintenance Schedule

- **Daily**: Monitor CI/CD results, review failures
- **Weekly**: Dependency updates, fixture reviews
- **Monthly**: Coverage review, baseline updates
- **Quarterly**: Comprehensive test suite audit

See [Maintenance Guide](maintenance.md) for detailed procedures.

---

**Last Updated**: 2024-01-15  
**Maintainer**: Mancer Development Team  
**Documentation Version**: 1.0.0
