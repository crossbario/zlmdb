Introduction to zLMDB
=====================

.. image:: https://img.shields.io/pypi/v/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: PyPI

.. image:: https://github.com/crossbario/zlmdb/workflows/main/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Amain
   :alt: Build

.. image:: https://readthedocs.org/projects/zlmdb/badge/?version=latest
    :target: https://zlmdb.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation

.. image:: https://github.com/crossbario/zlmdb/workflows/deploy/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Adeploy
   :alt: Deploy

zlmdb is a complete LMDB solution for Python providing **two APIs in one package**:

1. **Low-level py-lmdb compatible API** - Direct LMDB access with full control
2. **High-level object-relational API** - Type-safe ORM with automatic serialization

Key Features
------------

**Low-level LMDB API (py-lmdb compatible):**

* Drop-in replacement for py-lmdb
* Direct access to LMDB transactions, cursors, and databases
* Full LMDB feature set (subdatabases, duplicate keys, etc.)
* Works with all py-lmdb examples and code

**High-level Object-Relational API:**

* Type-safe persistent objects with automatic serialization
* Multiple serializers (JSON, CBOR, Pickle, Flatbuffers)
* Export/import from/to Apache Arrow
* Native Numpy arrays and Pandas data frames support
* Automatic indexes and relationships
* Schema management

**Implementation:**

* CFFI-only (no CPyExt) for maximum compatibility
* Works on both CPython and PyPy
* Native binary wheels for x86-64 and ARM64
* Vendored LMDB (no external dependencies)
* High-performance with zero-copy operations
* Free software (MIT license)

Usage Examples
--------------

**Low-level API (py-lmdb compatible):**

.. code-block:: python

    import lmdb

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

**High-level API (zlmdb ORM):**

.. code-block:: python

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

Development Workflow
====================

This project uses `just <https://github.com/casey/just>`_ as a modern task runner and `uv <https://github.com/astral-sh/uv>`_ for fast Python package management.

Complete Recipe List
--------------------

**Virtual Environment Management:**

* [ ] ``just create [venv]`` - Create Python venv (auto-detects system Python if no arg)
* [ ] ``just create-all`` - Create all venvs (cpy314, cpy313, cpy312, cpy311, pypy311)
* [ ] ``just version [venv]`` - Show Python version
* [ ] ``just list-all`` - List all available Python runtimes

**Installation:**

* [ ] ``just install [venv]`` - Install zlmdb (runtime deps only)
* [ ] ``just install-dev [venv]`` - Install in editable mode
* [ ] ``just install-tools [venv]`` - Install dev tools (pytest, sphinx, etc.)
* [ ] ``just install-all`` - Install in all venvs

**Testing:** 🧪

* [ ] ``just test [venv]`` - Run full test suite (both test directories)
* [ ] ``just test-quick [venv]`` - Quick pytest run (no tox)
* [x] ``just test-single [venv]`` - Run test_basic.py
* [x] ``just test-pmaps [venv]`` - Run pmap tests
* [x] ``just test-indexes [venv]`` - Run index tests
* [x] ``just test-select [venv]`` - Run select tests
* [ ] ``just test-zdb-etcd/df/dyn/fbs [venv]`` - Individual zdb tests
* [ ] ``just test-zdb [venv]`` - All zdb tests
* [ ] ``just test-all`` - Test in all venvs
* [ ] ``just test-tox`` - Run tox (py39-py313, flake8, coverage, mypy, yapf, sphinx)
* [ ] ``just test-tox-all`` - All tox environments
* [ ] ``just coverage [venv]`` - Generate HTML coverage report

**Code Quality:** ✨

* [x] ``just autoformat [venv]`` - Auto-format code with Ruff (modifies files!)
* [x] ``just check-format [venv]`` - Check formatting with Ruff (dry run)
* [x] ``just check-typing [venv]`` - Run static type checking with mypy

**Building:** 📦

* [ ] ``just build [venv]`` - Build wheel
* [ ] ``just build-sourcedist [venv]`` - Build sdist
* [ ] ``just build-all`` - Build wheels for all venvs
* [ ] ``just dist [venv]`` - Build both sdist and wheel

**Publishing:** 🚀

* [ ] ``just publish [venv]`` - Upload to PyPI with twine

**Documentation:** 📚

* [ ] ``just docs [venv]`` - Build HTML docs with Sphinx
* [ ] ``just docs-view [venv]`` - Build and open in browser
* [ ] ``just docs-clean`` - Clean doc build artifacts

**Cleaning:** 🧹

* [ ] ``just clean`` - Clean everything (alias for distclean)
* [ ] ``just clean-build`` - Remove build/ dist/ \*.egg-info
* [ ] ``just clean-pyc`` - Remove \*.pyc __pycache__
* [ ] ``just clean-test`` - Remove .tox .coverage .pytest_cache
* [ ] ``just distclean`` - Nuclear clean (removes venvs too!)

**Utilities:** 🔧

* [ ] ``just update-flatbuffers`` - Update from deps/ submodule
* [ ] ``just generate-flatbuffers-reflection`` - Generate reflection code
* [ ] ``just fix-copyright`` - Update copyright headers
* [ ] ``just setup-completion`` - Setup bash tab completion

Quick Start
-----------

.. code-block:: bash

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
