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

Object-relational in-memory database layer based on LMDB:

* High-performance (see below)
* Supports multiple serializers (JSON, CBOR, Pickle, Flatbuffers)
* Supports export/import from/to Apache Arrow
* Support native Numpy arrays and Pandas data frames
* Automatic indexes
* Free software (MIT license)

Development Workflow
====================

This project uses `just <https://github.com/casey/just>`_ as a modern task runner and `uv <https://github.com/astral-sh/uv>`_ for fast Python package management.

Complete Recipe List
--------------------

**Virtual Environment Management:**

* ``just create [venv]`` - Create Python venv (auto-detects system Python if no arg)
* ``just create-all`` - Create all venvs (cpy314, cpy313, cpy312, cpy311, pypy311)
* ``just version [venv]`` - Show Python version
* ``just list-all`` - List all available Python runtimes

**Installation:**

* ``just install [venv]`` - Install zlmdb (runtime deps only)
* ``just install-dev [venv]`` - Install in editable mode
* ``just install-tools [venv]`` - Install dev tools (pytest, sphinx, etc.)
* ``just install-all`` - Install in all venvs

**Testing:** 🧪

* ``just test [venv]`` - Run full test suite (both test directories)
* ``just test-quick [venv]`` - Quick pytest run (no tox)
* ``just test-single [venv]`` - Run test_basic.py
* ``just test-pmaps [venv]`` - Run pmap tests
* ``just test-indexes [venv]`` - Run index tests
* ``just test-select [venv]`` - Run select tests
* ``just test-zdb-etcd/df/dyn/fbs [venv]`` - Individual zdb tests
* ``just test-zdb [venv]`` - All zdb tests
* ``just test-all`` - Test in all venvs
* ``just test-tox`` - Run tox (py39-py313, flake8, coverage, mypy, yapf, sphinx)
* ``just test-tox-all`` - All tox environments
* ``just coverage [venv]`` - Generate HTML coverage report

**Code Quality:** ✨

* ``just autoformat [venv]`` - Auto-format code with Ruff (modifies files!)
* ``just check-format [venv]`` - Check formatting with Ruff (dry run)
* ``just check-typing [venv]`` - Run static type checking with mypy

**Building:** 📦

* ``just build [venv]`` - Build wheel
* ``just build-sourcedist [venv]`` - Build sdist
* ``just build-all`` - Build wheels for all venvs
* ``just dist [venv]`` - Build both sdist and wheel

**Publishing:** 🚀

* ``just publish [venv]`` - Upload to PyPI with twine

**Documentation:** 📚

* ``just docs [venv]`` - Build HTML docs with Sphinx
* ``just docs-view [venv]`` - Build and open in browser
* ``just docs-clean`` - Clean doc build artifacts

**Cleaning:** 🧹

* ``just clean`` - Clean everything (alias for distclean)
* ``just clean-build`` - Remove build/ dist/ *.egg-info
* ``just clean-pyc`` - Remove *.pyc __pycache__
* ``just clean-test`` - Remove .tox .coverage .pytest_cache
* ``just distclean`` - Nuclear clean (removes venvs too!)

**Utilities:** 🔧

* ``just update-flatbuffers`` - Update from deps/ submodule
* ``just generate-flatbuffers-reflection`` - Generate reflection code
* ``just fix-copyright`` - Update copyright headers
* ``just setup-completion`` - Setup bash tab completion

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
