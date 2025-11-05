Introduction to zLMDB
=====================

.. image:: https://img.shields.io/pypi/v/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: PyPI Version

.. image:: https://img.shields.io/github/v/release/crossbario/zlmdb
    :target: https://github.com/crossbario/zlmdb/releases
    :alt: GitHub Release

.. image:: https://img.shields.io/pypi/pyversions/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: Python Versions

.. image:: https://img.shields.io/pypi/l/zlmdb.svg
    :target: https://github.com/crossbario/zlmdb/blob/master/LICENSE
    :alt: License

.. image:: https://readthedocs.org/projects/zlmdb/badge/?version=latest
    :target: https://zlmdb.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/pypi/dm/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: Downloads

.. image:: https://github.com/crossbario/zlmdb/actions/workflows/main.yml/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions/workflows/main.yml
   :alt: Main

.. image:: https://github.com/crossbario/zlmdb/actions/workflows/wheels.yml/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions/workflows/wheels.yml
   :alt: Wheels

.. image:: https://github.com/crossbario/zlmdb/actions/workflows/wheels-docker.yml/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions/workflows/wheels-docker.yml
   :alt: Wheels Linux

.. image:: https://github.com/crossbario/zlmdb/actions/workflows/wheels-arm64.yml/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions/workflows/wheels-arm64.yml
   :alt: Wheels ARM64

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

* [x] ``just create [venv]`` - Create Python venv (auto-detects system Python if no arg)
* [x] ``just create-all`` - Create all venvs (cpy314, cpy313, cpy312, cpy311, pypy311)
* [x] ``just version [venv]`` - Show Python version
* [x] ``just list-all`` - List all available Python runtimes

**Installation:**

* [x] ``just install [venv]`` - Install zlmdb (runtime deps only)
* [x] ``just install-dev [venv]`` - Install in editable mode
* [x] ``just install-tools [venv]`` - Install dev tools (pytest, sphinx, etc.)
* [x] ``just install-all`` - Install in all venvs

**Testing - LMDB:** 🧪

* [x] ``just test-examples-lmdb`` - Test all LMDB examples (in default venv)
* [x] ``just test-examples-lmdb-addressbook [venv]`` - Test example LMDB address book
* [x] ``just test-examples-lmdb-dirtybench [venv]`` - Test example LMDB dirtybench
* [x] ``just test-examples-lmdb-dirtybench-gdbm [venv]`` - Test example LMDB dirtybench-gdbm
* [x] ``just test-examples-lmdb-nastybench [venv]`` - Test example LMDB nastybench
* [x] ``just test-examples-lmdb-parabench [venv]`` - Test example LMDB parabench

**Testing - ORM:** 🧪

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

* [x] ``just build [venv]`` - Build wheel
* [x] ``just build-sourcedist [venv]`` - Build sdist
* [x] ``just build-all`` - Build wheels for all venvs
* [!] ``just dist [venv]`` - Build both sdist and wheels
* [x] ``just verify-wheels [venv]`` - Verify all built wheels.

**Publishing:** 🚀

* [ ] ``just publish [venv]`` - Upload to PyPI with twine

**Documentation:** 📚

* [x] ``just docs [venv]`` - Build HTML docs with Sphinx
* [x] ``just docs-view [venv]`` - Build and open in browser
* [x] ``just docs-clean`` - Clean doc build artifacts

**Cleaning:** 🧹

* [x] ``just clean`` - Clean everything (alias for distclean)
* [x] ``just clean-build`` - Remove build/ dist/ \*.egg-info
* [x] ``just clean-pyc`` - Remove \*.pyc __pycache__
* [x] ``just clean-test`` - Remove .tox .coverage .pytest_cache
* [x] ``just distclean`` - Nuclear clean (removes venvs too!)

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
