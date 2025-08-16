# Testing Overview

A concise guide to testing the Mancer Framework: what to test and how to run it locally.

## Test pyramid
- Unit (≈70%): fast, isolated, mocked I/O
- Integration (≈20%): framework + real bash
- E2E (≈10%): full scenarios (optionally in Docker/SSH)

## What we validate
- Framework logic: CommandFactory, BaseCommand, Backends, ShellRunner orchestration
- Command building and output parsing
- Remote execution via SSH backend
- Result conversion (LIST/JSON/DataFrame/ndarray)

## Local quickstart
```bash
# Unit tests
pytest tests/unit -q

# Selected test
pytest tests/unit/test_commands.py::TestCommandFactory::test_create_ls_command -q
```

## Integration tests (example)
If you have Docker-based tests:
```bash
# Build/start test environment (example location)
cd development/docker_test
./run_automated_tests.sh --integration-only
```

## End-to-end tests (example)
```bash
cd development/docker_test
./run_automated_tests.sh --e2e-only
```

## Tips
- Prefer small, focused tests; parametrize where helpful
- Use mocks for subprocess when not explicitly testing bash/SSH
- Make failure messages actionable (include command strings and exit codes)

