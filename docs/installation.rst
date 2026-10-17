Installation
============

This guide covers how to install **zLMDB**.

Requirements
------------

zLMDB supports:

* Python 3.11+
* CPython and PyPy
* Linux (glibc and musl), macOS, Windows

Installing from PyPI
--------------------

The recommended way to install zLMDB is from PyPI using pip:

.. code-block:: bash

    pip install zlmdb

zLMDB publishes binary wheels for Linux (glibc and musl, x86-64 and ARM64),
macOS (ARM64) and Windows (x86-64), for CPython 3.11-3.14 and PyPy 3.11 (see
:doc:`native-build` for the exact matrix). With a wheel, nothing is compiled
at install time, and no system library is needed: LMDB and the FlatBuffers
compiler ``flatc`` are inside the wheel.

Where no wheel matches, pip builds zLMDB from the source distribution.

Building from Source
--------------------

zLMDB contains native code: two vendored and patched LMDB engines, compiled
with CFFI, and the FlatBuffers compiler ``flatc``. A build from source
therefore needs:

* a C compiler and a C++ compiler;
* **cmake** (for ``flatc``);
* ``patch`` (Linux and macOS);
* the Python build dependencies, which pip installs by itself: ``hatchling``,
  ``cffi`` and ``setuptools`` (and ``patch-ng`` on Windows).

The build passes no architecture flags of its own (no ``-march``), so the
result runs on any CPU of its architecture, and a cross toolchain's own flags
apply unchanged. Every native part is mandatory: if one cannot be built, the
build fails. There is no pure-Python fallback.

**From the source distribution.** The sdist is self-contained: it includes
the sources of both LMDB engines, their patches and the FlatBuffers sources.
This forces a build from it:

.. code-block:: bash

    pip install --no-binary zlmdb zlmdb

**From Git.** The LMDB and FlatBuffers sources are Git submodules, so clone
with them:

.. code-block:: bash

    git clone --recurse-submodules https://github.com/crossbario/zlmdb.git
    cd zlmdb
    pip install .

For development (editable install, test suites, wheel builds), see
:doc:`development`.

Cross-compilation and embedded targets
--------------------------------------

Building zLMDB with a cross toolchain, e.g. under Buildroot or Yocto for
riscv64, is on the **roadmap**: it is intended to work, but not yet tested in
CI. What already holds, and what is still to be tested, is described in
:ref:`cross-compilation`.

Dependencies
------------

zLMDB vendors LMDB (its own copy of the py-lmdb binding, ``zlmdb.lmdb``) and
FlatBuffers (``zlmdb.flatbuffers``), so neither ``lmdb`` nor ``flatbuffers``
is installed from PyPI. Its Python dependencies include:

* `cffi <https://cffi.readthedocs.io/>`__ - for the LMDB engines
* `cbor2 <https://cbor2.readthedocs.io/>`__ - for CBOR serialization
* `txaio <https://txaio.readthedocs.io/>`__ - for the async framework
  abstraction
* `numpy <https://numpy.org/>`__, `PyNaCl <https://pynacl.readthedocs.io/>`__,
  `PyYAML <https://pyyaml.org/>`__ and `click <https://click.palletsprojects.com/>`__

The complete list is in ``pyproject.toml``.

Verifying Installation
----------------------

To verify zLMDB is installed correctly:

.. code-block:: python

    import zlmdb
    print(zlmdb.__version__)

:doc:`native-build` shows how to check the LMDB engines, their patches and
``flatc`` of an installed copy.
