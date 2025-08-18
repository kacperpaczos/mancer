#!/usr/bin/env bash
set -euo pipefail

# Release automation helper for Mancer
# - Runs unit tests
# - Builds sdist and wheel
# - Validates metadata with twine check
# - Performs smoke install from built wheel in a temp venv
# - Optionally uploads to TestPyPI or PyPI (requires TWINE credentials)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info(){ echo -e "${YELLOW}[INFO]${NC} $*"; }
ok(){ echo -e "${GREEN}[OK]${NC} $*"; }
fail(){ echo -e "${RED}[FAIL]${NC} $*"; }

usage(){
  cat <<EOF
Usage: $0 [options]

Options:
  --unit-only           Run unit tests only and exit
  --build               Build sdist and wheel
  --check               Run twine check on dist/*
  --smoke               Smoke install from built wheel in temp venv
  --upload testpypi     Upload dist/* to TestPyPI
  --upload pypi         Upload dist/* to PyPI
  --all                 Run unit tests, build, check, smoke (no upload)

Environment:
  TWINE_USERNAME, TWINE_PASSWORD for uploads (use __token__ and API token)
EOF
}

ensure_in_repo_root(){
  if [ ! -f "pyproject.toml" ] || [ ! -d "src" ]; then
    fail "Run from repository root"; exit 1; fi
}

run_unit_tests(){
  info "Creating venv for unit tests..."
  python3 -m venv .venv-test
  source .venv-test/bin/activate
  python -m pip install -U pip
  python -m pip install -e .[test]
  info "Running unit tests..."
  pytest tests/unit -v --tb=short
  deactivate
  ok "Unit tests passed"
}

build_dists(){
  info "Cleaning old build artifacts..."
  rm -rf dist build src/*.egg-info src/*/*.egg-info src/*/*/*.egg-info 2>/dev/null || true
  info "Creating venv for build..."
  python3 -m venv .venv-build
  source .venv-build/bin/activate
  python -m pip install -U pip build twine
  info "Building sdist and wheel..."
  python -m build
  ls -lh dist
  deactivate
  ok "Build completed"
}

run_twine_check(){
  info "Validating metadata with twine check..."
  python3 -m venv .venv-buildcheck
  source .venv-buildcheck/bin/activate
  python -m pip install -U pip twine
  twine check dist/*
  deactivate
  ok "Twine check OK"
}

smoke_install(){
  local wheel
  wheel=$(ls dist/mancer-*-py3-none-any.whl | tail -n1)
  if [ -z "${wheel}" ]; then fail "Wheel not found in dist/"; exit 1; fi
  info "Smoke installing ${wheel} into temp venv..."
  python3 -m venv .venv-smoke
  source .venv-smoke/bin/activate
  python -m pip install -U pip
  pip install "${wheel}"
  python - <<'PY'
import mancer
from mancer.application.shell_runner import ShellRunner
print('mancer version:', getattr(mancer, '__version__', 'unknown'))
r = ShellRunner(backend_type='bash')
cmd = r.create_command('echo').text('ok')
print('executable:', cmd.build().executable)
PY
  deactivate
  ok "Smoke test OK"
}

upload(){
  local target=$1
  if [ -z "${TWINE_USERNAME:-}" ] || [ -z "${TWINE_PASSWORD:-}" ]; then
    fail "TWINE_USERNAME/TWINE_PASSWORD not set"; exit 1; fi
  python3 -m venv .venv-upload
  source .venv-upload/bin/activate
  python -m pip install -U pip twine
  if [ "${target}" = "testpypi" ]; then
    info "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
  elif [ "${target}" = "pypi" ]; then
    info "Uploading to PyPI..."
    twine upload dist/*
  else
    fail "Unknown upload target: ${target}"; exit 1
  fi
  deactivate
  ok "Upload to ${target} completed"
}

main(){
  ensure_in_repo_root
  if [ $# -eq 0 ]; then usage; exit 0; fi
  local do_unit=0 do_build=0 do_check=0 do_smoke=0 do_upload=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --unit-only) do_unit=1 ;;
      --build) do_build=1 ;;
      --check) do_check=1 ;;
      --smoke) do_smoke=1 ;;
      --upload) shift; do_upload="$1" ;;
      --all) do_unit=1; do_build=1; do_check=1; do_smoke=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Unknown option: $1"; usage; exit 1 ;;
    esac
    shift
  done
  if [ ${do_unit} -eq 1 ]; then run_unit_tests; [ "$do_unit" = 1 ] && [ $do_build -eq 0 ] && [ -z "$do_upload" ] && exit 0; fi
  if [ ${do_build} -eq 1 ]; then build_dists; fi
  if [ ${do_check} -eq 1 ]; then run_twine_check; fi
  if [ ${do_smoke} -eq 1 ]; then smoke_install; fi
  if [ -n "${do_upload}" ]; then upload "${do_upload}"; fi
}

main "$@"

