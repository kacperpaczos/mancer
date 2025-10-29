# Release Process - Publishing to PyPI

This document describes the process for releasing a new version of Mancer to PyPI.

## Overview

Mancer uses GitHub Actions for automated publishing to PyPI. When you push a version tag (e.g., `v0.1.6`), the workflow automatically builds and publishes the package.

## Prerequisites

1. Ensure you have push access to the repository
2. Ensure the PyPI trusted publisher is configured in GitHub repository settings (Settings → Environments → pypi)
3. Ensure all tests pass and code is ready for release

## Step-by-Step Release Process

### 1. Update Version Numbers

Update the version in **both** configuration files:

**`pyproject.toml`:**
```toml
[project]
version = "0.1.6"  # Update to new version
```

**`setup.py`:**
```python
setup(
    name="mancer",
    version="0.1.6",  # Update to new version
    # ... rest of config
)
```

### 2. Update CHANGELOG (if you have one)

Document changes in this release. If you don't have a CHANGELOG, consider creating one for future releases.

### 3. Commit Version Changes

```bash
git add pyproject.toml setup.py
git commit -m "Bump version to 0.1.6"
```

### 4. Build and Test Locally (Optional but Recommended)

Before publishing, build and test the package locally:

```bash
# Install build tools
pip install build twine

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the package
python -m build

# Check the package
twine check dist/*

# Test installation locally (optional)
pip install --force-reinstall dist/*.whl
```

You can also use the project's build script:
```bash
./tools/mancer_tools.sh --build
```

### 5. Push to Remote Repository

Ensure your changes are pushed to the remote:

```bash
git push origin <your-branch-name>
```

If you're working on `main` or `develop`, push there:
```bash
git push origin main  # or develop
```

### 6. Create and Push Version Tag

Create an annotated tag with the version number (must start with `v`):

```bash
git tag -a v0.1.6 -m "Release version 0.1.6"
git push origin v0.1.6
```

**Important:** The tag name must match the pattern `v*` (e.g., `v0.1.6`, `v1.0.0`), as configured in `.github/workflows/publish.yml`.

### 7. Monitor the GitHub Actions Workflow

1. Go to the "Actions" tab in your GitHub repository
2. Find the "Publish to PyPI" workflow run
3. Monitor the build and publish process
4. Check for any errors or warnings

### 8. Verify Release on PyPI

After the workflow completes successfully:

1. Visit https://pypi.org/project/mancer/
2. Verify the new version is listed
3. Test installation:
   ```bash
   pip install --upgrade mancer
   pip show mancer  # Check version
   ```

## Troubleshooting

### Build Fails

- Check that `pyproject.toml` and `setup.py` have matching versions
- Ensure all dependencies are correctly specified
- Run `twine check dist/*` locally to catch issues early

### GitHub Actions Fails

- Check the Actions log for specific error messages
- Verify the `pypi` environment exists in repository settings
- Ensure trusted publisher is configured correctly

### Version Already Exists on PyPI

If you push a tag for a version that already exists:
- PyPI will reject the upload
- You need to increment the version number
- Delete the tag: `git tag -d v0.1.6 && git push origin :refs/tags/v0.1.6`
- Create a new tag with incremented version

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.6): Bug fixes, backward compatible

Current version: See `pyproject.toml` and `setup.py`

## Alternative: Manual Publishing

If you need to publish manually (not recommended, but possible):

1. Build the package:
   ```bash
   python -m build
   ```

2. Upload to PyPI (requires API token):
   ```bash
   twine upload dist/*
   ```

You'll need:
- PyPI account
- API token configured: `~/.pypirc` or environment variable `TWINE_USERNAME`/`TWINE_PASSWORD`

## Notes

- The automated workflow uses PyPI trusted publishing (no API tokens needed in GitHub)
- Only push tags when the code is ready for release
- Consider creating a release branch if working with a team
- Document breaking changes clearly in commit messages and release notes

