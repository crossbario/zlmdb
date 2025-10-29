# Copyright (c) typedef int GmbH, Germany, 2025. All rights reserved.

# -----------------------------------------------------------------------------
# -- just global configuration
# -----------------------------------------------------------------------------

set unstable := true
set positional-arguments := true
set script-interpreter := ['uv', 'run', '--script']

# uv env vars (see: https://docs.astral.sh/uv/reference/environment/)

# Project base directory
PROJECT_DIR := justfile_directory()

# Tell uv to use project-local cache directory
export UV_CACHE_DIR := './.uv-cache'

# Use this common single directory for all uv venvs
VENV_DIR := './.venvs'

# Define supported Python environments
ENVS := 'cpy314 cpy313 cpy312 cpy311 pypy311'

# Default recipe: list all recipes
default:
    @echo ""
    @just --list
    @echo ""

# Internal helper to map Python version short name to full uv version
_get-spec short_name:
    #!/usr/bin/env bash
    set -e
    case {{short_name}} in
        cpy314)  echo "cpython-3.14";;
        cpy313)  echo "cpython-3.13";;
        cpy312)  echo "cpython-3.12";;
        cpy311)  echo "cpython-3.11";;
        pypy311) echo "pypy-3.11";;
        *)       echo "Unknown environment: {{short_name}}" >&2; exit 1;;
    esac

# Internal helper that calculates and prints the system-matching venv name
_get-system-venv-name:
    #!/usr/bin/env bash
    set -e
    SYSTEM_VERSION=$(/usr/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    ENV_NAME="cpy$(echo ${SYSTEM_VERSION} | tr -d '.')"
    if ! echo "{{ ENVS }}" | grep -q -w "${ENV_NAME}"; then
        echo "Error: System Python (${SYSTEM_VERSION}) maps to '${ENV_NAME}', which is not a supported environment." >&2
        exit 1
    fi
    echo "${ENV_NAME}"

# Helper recipe to get the python executable path for a venv
_get-venv-python venv="":
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PATH="{{VENV_DIR}}/${VENV_NAME}"
    if [[ "$OS" == "Windows_NT" ]]; then
        echo "${VENV_PATH}/Scripts/python.exe"
    else
        echo "${VENV_PATH}/bin/python3"
    fi

# -----------------------------------------------------------------------------
# -- General/global helper recipes
# -----------------------------------------------------------------------------

# Setup bash tab completion for the current user (to activate: `source ~/.config/bash_completion`).
setup-completion:
    #!/usr/bin/env bash
    set -e
    COMPLETION_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/bash_completion"
    MARKER="# --- Just completion ---"
    echo "==> Setting up bash tab completion for 'just'..."
    if [ -f "${COMPLETION_FILE}" ] && grep -q "${MARKER}" "${COMPLETION_FILE}"; then
        echo "--> 'just' completion is already configured."
        exit 0
    fi
    echo "--> Configuration not found. Adding it now..."
    mkdir -p "$(dirname "${COMPLETION_FILE}")"
    echo "" >> "${COMPLETION_FILE}"
    echo "${MARKER}" >> "${COMPLETION_FILE}"
    just --completions bash >> "${COMPLETION_FILE}"
    echo "--> Successfully added completion logic to ${COMPLETION_FILE}."
    echo ""
    echo "==> Setup complete. Please restart your shell or run:"
    echo "    source \"${COMPLETION_FILE}\""

# Remove ALL generated files, including venvs, caches, and build artifacts
distclean:
    #!/usr/bin/env bash
    set -e
    echo "==> Performing a deep clean (distclean)..."
    echo "--> Removing venvs, cache, and build/dist directories..."
    rm -rf {{UV_CACHE_DIR}} {{VENV_DIR}} build/ dist/ .pytest_cache/ .ruff_cache/ .mypy_cache/
    rm -rf docs/_build/
    echo "--> Searching for and removing nested Python caches..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo "--> Searching for and removing compiled Python files..."
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    echo "--> Searching for and removing setuptools egg-info directories..."
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    echo "==> Distclean complete. The project is now pristine."

# -----------------------------------------------------------------------------
# -- Python virtual environments
# -----------------------------------------------------------------------------

# List all Python virtual environments
list-all:
    #!/usr/bin/env bash
    set -e
    echo ""
    echo "Available CPython run-times:"
    echo "============================"
    echo ""
    uv python list --all-platforms cpython
    echo ""
    echo "Available PyPy run-times:"
    echo "========================="
    echo ""
    uv python list --all-platforms pypy
    echo ""
    echo "Mapped Python run-time shortname => full version:"
    echo "================================================="
    echo ""
    for env in {{ENVS}}; do
        spec=$(just --quiet _get-spec "$env")
        echo "  - $env => $spec"
    done
    echo ""
    echo "Create a Python venv using: just create <shortname>"

# Create a single Python virtual environment (usage: `just create cpy314` or `just create`)
create venv="":
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        echo "==> No venv name specified. Auto-detecting from system Python..."
        VENV_NAME=$(just --quiet _get-system-venv-name)
        echo "==> Defaulting to venv: '${VENV_NAME}'"
    fi
    VENV_PATH="{{ VENV_DIR }}/${VENV_NAME}"
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    if [ ! -d "${VENV_PATH}" ]; then
        PYTHON_SPEC=$(just --quiet _get-spec "${VENV_NAME}")
        echo "==> Creating Python virtual environment '${VENV_NAME}' using ${PYTHON_SPEC}..."
        mkdir -p "{{ VENV_DIR }}"
        uv venv --seed --python "${PYTHON_SPEC}" "${VENV_PATH}"
        echo "==> Successfully created venv '${VENV_NAME}'."
    else
        echo "==> Python virtual environment '${VENV_NAME}' already exists."
    fi
    ${VENV_PYTHON} -V
    ${VENV_PYTHON} -m pip -V
    echo "==> Activate with: source ${VENV_PATH}/bin/activate"

# Create all Python virtual environments
create-all:
    #!/usr/bin/env bash
    for venv in {{ENVS}}; do
        just create ${venv}
    done

# Get the version of a single virtual environment's Python
version venv="":
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    if [ -d "{{ VENV_DIR }}/${VENV_NAME}" ]; then
        echo "==> Python virtual environment '${VENV_NAME}' exists:"
        "{{VENV_DIR}}/${VENV_NAME}/bin/python" -V
    else
        echo "==> Python virtual environment '${VENV_NAME}' does not exist."
    fi

# Get versions of all Python virtual environments
version-all:
    #!/usr/bin/env bash
    for venv in {{ENVS}}; do
        just version ${venv}
    done

# -----------------------------------------------------------------------------
# -- Installation
# -----------------------------------------------------------------------------

# Install zlmdb with runtime dependencies
install venv="": (create venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Installing zlmdb in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pip install .

# Install zlmdb in development (editable) mode
install-dev venv="": (create venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Installing zlmdb in editable mode in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pip install -e .

# Install all environments
install-all:
    #!/usr/bin/env bash
    for venv in {{ENVS}}; do
        just install ${venv}
    done

# Install development tools (ruff, mypy, sphinx, etc.)
install-tools venv="": (create venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Installing development tools in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pip install -e .[dev]

# Install minimal build tools for building wheels
install-build-tools venv="": (create venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Installing minimal build tools in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pip install build wheel cffi

# -----------------------------------------------------------------------------
# -- Testing
# -----------------------------------------------------------------------------

# Run the test suite (both zlmdb/tests and tests directories)
test venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running test suite in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pytest -v zlmdb/tests/ tests/

# Run tests in all environments
test-all:
    #!/usr/bin/env bash
    for venv in {{ENVS}}; do
        just test ${venv}
    done

# -----------------------------------------------------------------------------
# -- Building
# -----------------------------------------------------------------------------

# Build wheel package
build venv="": (install-build-tools venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Building wheel package with ${VENV_NAME}..."
    ${VENV_PYTHON} -m build --wheel
    ls -lh dist/

# Build source distribution
build-sourcedist venv="": (install-build-tools venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Building source distribution with ${VENV_NAME}..."
    ${VENV_PYTHON} -m build --sdist
    ls -lh dist/

# Build wheels for all environments
build-all:
    #!/usr/bin/env bash
    for venv in {{ENVS}}; do
        just build ${venv}
    done
    ls -lh dist/

# -----------------------------------------------------------------------------
# -- Documentation
# -----------------------------------------------------------------------------

# Build HTML documentation using Sphinx
docs venv="": (install-tools venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PATH="{{ VENV_DIR }}/${VENV_NAME}"
    echo "==> Building documentation with ${VENV_NAME}..."
    "${VENV_PATH}/bin/sphinx-build" -b html docs/ docs/_build/html

# View built documentation
docs-view venv="": (docs venv)
    echo "==> Opening documentation in browser..."
    xdg-open docs/_build/html/index.html 2>/dev/null || open docs/_build/html/index.html 2>/dev/null || echo "Please open docs/_build/html/index.html manually"

# Clean generated documentation
docs-clean:
    echo "==> Cleaning documentation build artifacts..."
    rm -rf docs/_build

# -----------------------------------------------------------------------------
# -- Cleaning (granular targets from Makefile)
# -----------------------------------------------------------------------------

# Clean Python bytecode files
clean-pyc:
    echo "==> Removing Python bytecode files..."
    find . -name '*.pyc' -delete
    find . -name '*.pyo' -delete
    find . -name '*~' -delete
    find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

# Clean build artifacts
clean-build:
    echo "==> Removing build artifacts..."
    rm -rf build/ dist/ .eggs/
    find . -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
    find . -name '*.egg' -delete 2>/dev/null || true

# Clean test and coverage artifacts
clean-test:
    echo "==> Removing test and coverage artifacts..."
    rm -rf .tox/ .coverage .coverage.* htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf .test* 2>/dev/null || true

# Clean all generated files (alias for distclean)
clean: distclean

# -----------------------------------------------------------------------------
# -- Testing (expanded from Makefile)
# -----------------------------------------------------------------------------

# Run quick tests with pytest (no tox)
test-quick venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running quick tests with pytest in ${VENV_NAME}..."
    # Explicitly specify test directories to avoid pytest searching .uv-cache/, .venvs/, etc.
    ${VENV_PYTHON} -m pytest -v tests/ zlmdb/tests/

# Run single test file
test-single venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    clear
    echo "==> Running test_basic.py in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pytest -v -s zlmdb/tests/test_basic.py

# Run pmap tests
test-pmaps venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    clear
    echo "==> Running test_pmaps.py in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pytest -v -s zlmdb/tests/test_pmaps.py

# Run index tests
test-indexes venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    clear
    echo "==> Running test_pmap_indexes.py in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pytest -v -s zlmdb/tests/test_pmap_indexes.py

# Run select tests
test-select venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    clear
    echo "==> Running test_select.py in ${VENV_NAME}..."
    ${VENV_PYTHON} -m pytest -v -s zlmdb/tests/test_select.py

# Run zdb etcd tests
test-zdb-etcd venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running test_zdb_etcd.py in ${VENV_NAME}..."
    ${VENV_PYTHON} tests/zdb/test_zdb_etcd.py

# Run zdb dataframe tests
test-zdb-df venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running test_zdb_df.py in ${VENV_NAME}..."
    ${VENV_PYTHON} tests/zdb/test_zdb_df.py

# Run zdb dynamic tests
test-zdb-dyn venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running test_zdb_dyn.py in ${VENV_NAME}..."
    ${VENV_PYTHON} tests/zdb/test_zdb_dyn.py

# Run zdb flatbuffers tests
test-zdb-fbs venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Running test_zdb_fbs.py in ${VENV_NAME}..."
    ${VENV_PYTHON} tests/zdb/test_zdb_fbs.py

# Run all zdb tests
test-zdb venv="": (test-zdb-etcd venv) (test-zdb-df venv) (test-zdb-dyn venv) (test-zdb-fbs venv)

# Run tests with tox
test-tox:
    echo "==> Running tests with tox..."
    tox -e py39,py310,py311,py312,py313,flake8,coverage,mypy,yapf,sphinx

# Run all tox environments
test-tox-all:
    echo "==> Running all tox environments..."
    tox

# Generate code coverage report
coverage venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Generating coverage report in ${VENV_NAME}..."
    ${VENV_PYTHON} -m coverage run --source zlmdb --omit="zlmdb/flatbuffers/reflection/*,zlmdb/tests/*" -m pytest -v -s zlmdb
    ${VENV_PYTHON} -m coverage report -m
    ${VENV_PYTHON} -m coverage html
    echo "==> Opening coverage report..."
    xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Please open htmlcov/index.html manually"

# -----------------------------------------------------------------------------
# -- Code Quality
# -----------------------------------------------------------------------------

# Auto-format code with Ruff (modifies files in-place!)
autoformat venv="": (install-tools venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PATH="{{ VENV_DIR }}/${VENV_NAME}"
    echo "==> Auto-formatting code with ${VENV_NAME}..."

    # 1. Run the FORMATTER first. This will handle line lengths, quotes, etc.
    "${VENV_PATH}/bin/ruff" format --exclude ./tests ./zlmdb

    # 2. Run the LINTER'S FIXER second. This will handle things like
    #    removing unused imports, sorting __all__, etc.
    "${VENV_PATH}/bin/ruff" check --fix --exclude ./tests ./zlmdb
    echo "--> Formatting complete."

# Check code formatting with Ruff (dry run)
check-format venv="": (install-tools venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PATH="{{ VENV_DIR }}/${VENV_NAME}"
    echo "==> Checking code formatting with ${VENV_NAME}..."
    "${VENV_PATH}/bin/ruff" check --exclude ./deps/flatbuffers .

# Run static type checking with mypy
check-typing venv="": (install-tools venv) (install venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PATH="{{ VENV_DIR }}/${VENV_NAME}"
    echo "==> Running static type checks with ${VENV_NAME}..."
    # Only check core zlmdb package, exclude tests and vendored flatbuffers
    # Note: lmdb module is skipped via mypy.ini [mypy-lmdb.*] configuration
    "${VENV_PATH}/bin/mypy" \
        --exclude '/tests/' \
        --exclude '/flatbuffers/' \
        zlmdb/

# -----------------------------------------------------------------------------
# -- Publishing
# -----------------------------------------------------------------------------

# Build both source distribution and wheel
dist venv="": clean-build (build venv) (build-sourcedist venv)
    #!/usr/bin/env bash
    echo "==> Listing distribution files..."
    ls -lh dist/
    echo ""
    echo "==> Contents of wheel:"
    unzip -l dist/zlmdb-*-py*.whl || echo "Wheel not found"

# Publish to PyPI using twine
publish venv="": (dist venv)
    #!/usr/bin/env bash
    set -e
    VENV_NAME="{{ venv }}"
    if [ -z "${VENV_NAME}" ]; then
        VENV_NAME=$(just --quiet _get-system-venv-name)
    fi
    VENV_PYTHON=$(just --quiet _get-venv-python "${VENV_NAME}")
    echo "==> Publishing to PyPI with twine..."
    ${VENV_PYTHON} -m twine upload dist/*

# -----------------------------------------------------------------------------
# -- Utilities
# -----------------------------------------------------------------------------

# Update flatbuffers from deps/flatbuffers submodule
update-flatbuffers:
    echo "==> Updating flatbuffers from submodule..."
    rm -rf ./flatbuffers
    cp -R deps/flatbuffers/python/flatbuffers .
    echo "✓ Flatbuffers updated"

# Generate flatbuffers reflection Python code
generate-flatbuffers-reflection:
    #!/usr/bin/env bash
    FLATC=/usr/local/bin/flatc
    if [ ! -f "${FLATC}" ]; then
        echo "ERROR: flatc not found at ${FLATC}"
        echo "Install flatbuffers compiler first"
        exit 1
    fi
    echo "==> Generating flatbuffers reflection code..."
    ${FLATC} --python -o zlmdb/flatbuffers/ deps/flatbuffers/reflection/reflection.fbs
    echo "✓ Flatbuffers reflection code generated"

# Fix copyright headers (typedef int GmbH)
fix-copyright:
    echo "==> Fixing copyright headers..."
    find . -type f -exec sed -i 's/Copyright (c) Crossbar.io Technologies GmbH/Copyright (c) typedef int GmbH/g' {} \;
    echo "✓ Copyright headers updated"
