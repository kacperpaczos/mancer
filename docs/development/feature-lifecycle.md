# Development Lifecycle for Adding New Features

The complete development lifecycle in Mancer follows these steps:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│  1. Planning   │────►│ 2. Development │────►│   3. Testing   │────►│  4. Versioning │
│                │     │                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
        │                                                                     │
        │                                                                     ▼
┌────────────────┐                                                   ┌────────────────┐
│                │                                                   │                │
│ 7. Maintenance │◄────────────────────────────────────────────────►│  5. Building   │
│                │                                                   │                │
└────────────────┘                                                   └────────────────┘
        ▲                                                                     │
        │                                                                     ▼
        │                                                             ┌────────────────┐
        │                                                             │                │
        └─────────────────────────────────────────────────────────────┤  6. Publishing │
                                                                      │                │
                                                                      └────────────────┘
```

## 1. Planning

### Define Requirements
- Document the feature requirements clearly
- Identify user stories and acceptance criteria
- Consider backward compatibility implications
- Plan the implementation approach

### Design Phase
- Create Interfaces in `domain/interface/`
- Design the domain model in `domain/model/`
- Plan the API changes and additions
- Consider testing strategy

### Documentation Planning
- Plan what documentation needs to be updated
- Identify examples that should be created
- Plan user guide updates

## 2. Development

### Implementation Order
1. **Domain Layer First**: Start with models and interfaces
2. **Application Services**: Implement orchestration logic
3. **Infrastructure**: Add concrete implementations
4. **Examples**: Create working examples

### Code Organization
- Implement the domain services in `domain/service/`
- Create concrete command implementations in `infrastructure/command/`
- Implement backend adapters if needed in `infrastructure/backend/`
- Add application services in `application/`
- Create examples in `examples/`

### Development Standards
- Follow the established code patterns
- Use type hints throughout
- Write docstrings for all public methods
- Follow the naming conventions

## 3. Testing

### Test Strategy
- Write unit tests in `tests/unit/`
- Add integration tests in `tests/integration/`
- Include smoke tests for critical paths
- Test both success and failure scenarios

### Test Coverage
- Maintain coverage above 80%
- Test edge cases and error conditions
- Test version compatibility if applicable
- Test backward compatibility

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mancer --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Test Data
- Use realistic test data
- Test with different tool versions if applicable
- Include performance tests for critical paths

## 4. Versioning

### Version Number Updates
- Update version number in `setup.py`
- For minor changes, `install_dev.py` will automatically increment the Z version
- For significant changes, manually update X or Y version
- Document version-specific behaviors if applicable

### Changelog
- Update CHANGELOG.md with new features
- Document breaking changes clearly
- Include migration guides if needed

### Version Compatibility
- Test with supported Python versions
- Test with supported tool versions
- Document any new version requirements

## 5. Building

### Package Building
```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel

# Build both
python setup.py sdist bdist_wheel
```

### Local Testing
```bash
# Test the built package locally
./dev_tools/build_package.py --install

# Verify installation
python -c "import mancer; print(mancer.__version__)"
```

### Quality Checks
- Run all tests on the built package
- Check code quality tools
- Verify documentation builds correctly

## 6. Publishing

### Pre-release Checklist
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] Examples work correctly
- [ ] Version numbers are correct
- [ ] Changelog is updated

### Release Process
- Create a release tag in Git
- Build and upload to PyPI or internal repository
- Update documentation if hosted externally
- Create release notes on GitHub

### Post-release
- Monitor for any immediate issues
- Update any external references
- Announce the release to the community

## 7. Maintenance

### Ongoing Support
- Monitor for bug reports
- Respond to user questions
- Fix any issues that arise

### Version Compatibility
- Implement version-specific adapters for backward compatibility
- Update tool version configurations
- Monitor for breaking changes in dependencies

### Documentation Updates
- Keep documentation current with code changes
- Add new examples as needed
- Update troubleshooting guides based on user feedback

## Best Practices

### Code Quality
- Use pre-commit hooks to maintain code quality
- Run code quality tools before committing
- Keep functions small and focused
- Use meaningful variable and function names

### Testing
- Write tests as you develop features
- Test edge cases and error conditions
- Use descriptive test names
- Maintain high test coverage

### Documentation
- Document as you code
- Include examples in docstrings
- Update user guides for new features
- Keep architecture documentation current

### Collaboration
- Use feature branches for development
- Write clear commit messages
- Review code before merging
- Communicate breaking changes clearly

## Common Pitfalls

### Avoid These Mistakes
1. **Skipping Tests**: Always write tests for new features
2. **Breaking Changes**: Minimize breaking changes, document them clearly
3. **Poor Documentation**: Good code needs good documentation
4. **Version Mismatches**: Keep version numbers consistent across files
5. **Ignoring Feedback**: Listen to user feedback and bug reports

### Success Factors
1. **Incremental Development**: Build features incrementally
2. **Regular Testing**: Test frequently during development
3. **User Feedback**: Get feedback early and often
4. **Documentation**: Keep documentation current
5. **Quality**: Maintain high code quality standards
