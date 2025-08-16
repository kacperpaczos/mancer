# Installation

## Requirements
- Python 3.8+
- pip (latest recommended)
- (Optional) Docker (for containerized testing/examples)

## Install from PyPI
```bash
pip install -U mancer
```

Optionally install extras:
```bash
# Development tooling (linters, type-checkers)
pip install "mancer[dev]"

# Test tooling
pip install "mancer[test]"
```

Verify installation:
```bash
python -c "import mancer; print('Mancer version:', mancer.__version__)"
```

## Install from source (editable)
```bash
# Clone the repository
git clone https://github.com/your-org/mancer.git
cd mancer

# Create and activate virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install package in editable mode
pip install -e .
# or with dev extras
pip install -e ".[dev]"
```

Upgrade/downgrade:
```bash
pip install -U mancer        # upgrade to latest
pip install mancer==0.1.3    # install a specific version
```

Uninstall:
```bash
pip uninstall -y mancer
```

## (Optional) Using Docker
See Docker-based workflows in the repository scripts (e.g., scripts/run_tests.sh) and development/docker_test/.

---

Continue to [Quickstart](quickstart.md)
