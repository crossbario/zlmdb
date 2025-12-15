# zLMDB

[![PyPI](https://img.shields.io/pypi/v/zlmdb.svg)](https://pypi.python.org/pypi/zlmdb)
[![Python](https://img.shields.io/pypi/pyversions/zlmdb.svg)](https://pypi.python.org/pypi/zlmdb)
[![CI](https://github.com/crossbario/zlmdb/workflows/main/badge.svg)](https://github.com/crossbario/zlmdb/actions?query=workflow%3Amain)
[![CD (wheels)](https://github.com/crossbario/zlmdb/workflows/wheels/badge.svg)](https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels)
[![CD (wheels-arm64)](https://github.com/crossbario/zlmdb/workflows/wheels-arm64/badge.svg)](https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels-arm64)
[![CD (wheels-docker)](https://github.com/crossbario/zlmdb/workflows/wheels-docker/badge.svg)](https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels-docker)
[![Docs](https://readthedocs.org/projects/zlmdb/badge/?version=latest)](https://zlmdb.readthedocs.io/en/latest/)
[![License](https://img.shields.io/pypi/l/zlmdb.svg)](https://github.com/crossbario/zlmdb/blob/master/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/zlmdb.svg)](https://pypi.python.org/pypi/zlmdb)

---

zlmdb is a complete LMDB solution for Python providing **two APIs in one
package**:

1.  **Low-level py-lmdb compatible API** - Direct LMDB access with full
    control
2.  **High-level object-relational API** - Type-safe ORM with automatic
    serialization

## Key Features

**Low-level LMDB API (py-lmdb compatible):**

-   Drop-in replacement for py-lmdb
-   Direct access to LMDB transactions, cursors, and databases
-   Full LMDB feature set (subdatabases, duplicate keys, etc.)
-   Works with all py-lmdb examples and code

**High-level Object-Relational API:**

-   Type-safe persistent objects with automatic serialization
-   Multiple serializers (JSON, CBOR, Pickle, Flatbuffers)
-   Export/import from/to Apache Arrow
-   Native Numpy arrays and Pandas data frames support
-   Automatic indexes and relationships
-   Schema management

**Implementation:**

-   CFFI-only (no CPyExt) for maximum compatibility
-   Works on both CPython and PyPy
-   Native binary wheels for x86-64 and ARM64
-   Vendored LMDB (no external dependencies)
-   High-performance with zero-copy operations
-   Free software (MIT license)

## Usage Examples

**Low-level API (py-lmdb compatible):**

``` python
import zlmdb.lmdb as lmdb

# Open database
env = lmdb.open('/tmp/mydb', max_dbs=10)
db = env.open_db(b'users')

# Write data
with env.begin(write=True) as txn:
    txn.put(b'alice', b'alice@example.com', db=db)
    txn.put(b'bob', b'bob@example.com', db=db)

# Read data
with env.begin() as txn:
    email = txn.get(b'alice', db=db)
    print(email)  # b'alice@example.com'
```

**High-level API (zlmdb ORM):**

``` python
import zlmdb

# Define schema
class User(object):
    def __init__(self, oid, name, email):
        self.oid = oid
        self.name = name
        self.email = email

schema = zlmdb.Schema()
schema.users = zlmdb.MapUuidCbor(1, marshal=lambda obj: obj.__dict__)

# Use it
db = zlmdb.Database('/tmp/mydb', schema=schema)
with db.begin(write=True) as txn:
    user = User(uuid.uuid4(), 'Alice', 'alice@example.com')
    schema.users[txn, user.oid] = user
```

# Development Workflow

This project uses [just](https://github.com/casey/just) as a modern task
runner and [uv](https://github.com/astral-sh/uv) for fast Python package
management.

## Complete Recipe List

**Virtual Environment Management:**

-   \[x\] `just create [venv]` - Create Python venv (auto-detects system
    Python if no arg)
-   \[x\] `just create-all` - Create all venvs (cpy314, cpy313, cpy312,
    cpy311, pypy311)
-   \[x\] `just version [venv]` - Show Python version
-   \[x\] `just list-all` - List all available Python runtimes

**Installation:**

-   \[x\] `just install [venv]` - Install zlmdb (runtime deps only)
-   \[x\] `just install-dev [venv]` - Install in editable mode
-   \[x\] `just install-tools [venv]` - Install dev tools (pytest,
    sphinx, etc.)
-   \[x\] `just install-all` - Install in all venvs

**Testing - LMDB:** 🧪

-   \[x\] `just test-examples-lmdb` - Test all LMDB examples (in default
    venv)
-   \[x\] `just test-examples-lmdb-addressbook [venv]` - Test example
    LMDB address book
-   \[x\] `just test-examples-lmdb-dirtybench [venv]` - Test example
    LMDB dirtybench
-   \[x\] `just test-examples-lmdb-dirtybench-gdbm [venv]` - Test
    example LMDB dirtybench-gdbm
-   \[x\] `just test-examples-lmdb-nastybench [venv]` - Test example
    LMDB nastybench
-   \[x\] `just test-examples-lmdb-parabench [venv]` - Test example LMDB
    parabench

**Testing - ORM:** 🧪

-   \[ \] `just test [venv]` - Run full test suite (both test
    directories)
-   \[ \] `just test-quick [venv]` - Quick pytest run
-   \[x\] `just test-single [venv]` - Run test_basic.py
-   \[x\] `just test-pmaps [venv]` - Run pmap tests
-   \[x\] `just test-indexes [venv]` - Run index tests
-   \[x\] `just test-select [venv]` - Run select tests
-   \[ \] `just test-zdb-etcd/df/dyn/fbs [venv]` - Individual zdb tests
-   \[ \] `just test-zdb [venv]` - All zdb tests
-   \[ \] `just test-all` - Test in all venvs
-   \[ \] `just coverage [venv]` - Generate HTML coverage report

**Code Quality:** ✨

-   \[x\] `just autoformat [venv]` - Auto-format code with Ruff
    (modifies files!)
-   \[x\] `just check-format [venv]` - Check formatting with Ruff (dry
    run)
-   \[x\] `just check-typing [venv]` - Run static type checking with
    mypy

**Building:** 📦

-   \[x\] `just build [venv]` - Build wheel
-   \[x\] `just build-sourcedist [venv]` - Build sdist
-   \[x\] `just build-all` - Build wheels for all venvs
-   \[!\] `just dist [venv]` - Build both sdist and wheels
-   \[x\] `just verify-wheels [venv]` - Verify all built wheels.

**Publishing:** 🚀

-   \[ \] `just publish [venv]` - Upload to PyPI with twine

**Documentation:** 📚

-   \[x\] `just docs [venv]` - Build HTML docs with Sphinx
-   \[x\] `just docs-view [venv]` - Build and open in browser
-   \[x\] `just docs-clean` - Clean doc build artifacts

**Cleaning:** 🧹

-   \[x\] `just clean` - Clean everything (alias for distclean)
-   \[x\] `just clean-build` - Remove build/ dist/ \*.egg-info
-   \[x\] `just clean-pyc` - Remove \*.pyc \_\_pycache\_\_
-   \[x\] `just clean-test` - Remove .coverage .pytest_cache
-   \[x\] `just distclean` - Nuclear clean (removes venvs too!)

**Utilities:** 🔧

-   \[ \] `just update-flatbuffers` - Update from deps/ submodule
-   \[ \] `just generate-flatbuffers-reflection` - Generate reflection
    code
-   \[ \] `just fix-copyright` - Update copyright headers
-   \[ \] `just setup-completion` - Setup bash tab completion

## Quick Start

``` bash
# Install just and uv (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install in development mode
just create
just install-dev

# Run tests
just test

# Build wheel
just build
```
