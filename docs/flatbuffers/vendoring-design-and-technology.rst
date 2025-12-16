Vendoring Design and Native Binaries
====================================

.. note::

   This document explains *how* and *why* native artifacts are built,
   bundled, verified, and distributed in zLMDB. It complements the
   higher-level :doc:`wamp-zerocopy-dataplane` architecture documentation.

Overview
--------

Both **zLMDB** and **Autobahn|Python** ship **native code and native
executables** as part of their Python distributions:

* CFFI-based native extensions (LMDB)
* A bundled **FlatBuffers compiler** (``flatc``)
* Native wheels for **x86-64 and ARM64**
* First-class **PyPy** support
* Fully **manylinux-compliant** wheels verified with ``auditwheel``

This is powerful — but also subtle and non-obvious.

What Users Get
--------------

From a user's point of view, installation is intentionally simple:

.. code-block:: bash

   pip install zlmdb
   # or
   pip install autobahn

After installation, users have:

* A working ``flatc`` executable
* A native LMDB backend
* No system-level dependencies required
* Identical behavior on CPython and PyPy

Behind the scenes, careful engineering ensures that:

* Wheels install without compilation
* Binaries work across distributions
* PyPy works just as well as CPython
* ``auditwheel repair`` succeeds
* ISA incompatibilities (e.g. ``x86_64_v2``) are avoided
* Users do not need system FlatBuffers, LMDB, or compilers

Native Components in the Wheel
------------------------------

Each wheel contains:

**CFFI-based LMDB Extension**
   The ``_lmdb_cffi.*.so`` shared library provides high-performance
   access to LMDB without requiring compilation at install time.

**Native flatc Executable**
   The FlatBuffers compiler is shipped as a native executable inside
   the package, invoked via a Python wrapper.

**Vendored FlatBuffers Runtime**
   The FlatBuffers Python runtime library and reflection data
   (``reflection.bfbs``) are included.

All of these are installed transparently into the Python environment.

manylinux and ISA Compatibility
-------------------------------

Key constraints for Linux wheels:

* Wheels must run on a wide range of Linux distributions
* ``auditwheel`` enforces:

  * ABI compatibility
  * Baseline CPU instruction sets

Compiling on a "modern" host can silently introduce:

* ``x86_64_v2`` instructions (SSE4.2, etc.)
* Too-new symbol versions

Therefore:

* Builds are done in **manylinux containers**
* Baseline architecture flags are enforced
* Toolchains are chosen carefully
* Wheels are verified with ``auditwheel repair``

This ensures wheels are installable on older systems, not just CI hosts.

Bundled flatc: Why and How
--------------------------

Why Bundle flatc?
^^^^^^^^^^^^^^^^^

* **Avoid system dependencies** — Users don't need to install FlatBuffers
* **Schema/compiler compatibility** — Schema and compiler versions always match
* **Reproducible builds** — Same compiler everywhere
* **Hermetic CI** — No external dependencies during builds
* **Schema-driven workflows** — Works out of the box

How flatc is Exposed
^^^^^^^^^^^^^^^^^^^^

* ``flatc`` is shipped as a native executable inside the package
* A Python console script (``flatc``) dispatches to it
* Works identically on CPython and PyPy
* No PATH manipulation required

.. code-block:: bash

   # After pip install zlmdb
   flatc --version

This just works — even on PyPy.

PyPy as a First-Class Target
----------------------------

PyPy support is not accidental — it is a design requirement.

Why PyPy Matters
^^^^^^^^^^^^^^^^

Running on PyPy allows "almost C-like" performance, since PyPy is
a *tracing JIT compiler* for Python with a *generational garbage
collector*. Both features are crucial for:

* High throughput and bandwidth
* Consistent low latency
* Memory-efficient operation

How PyPy is Supported
^^^^^^^^^^^^^^^^^^^^^

* LMDB is accessed via **CFFI**, not CPython C-API
* Native wheels are built and published for PyPy
* No fallback-to-sdist compilation required for users

The choice of CFFI over CPython's C-API is deliberate. The CPython
C-API (CPyExt) is implementation-defined and performs poorly on PyPy.
CFFI provides:

* Native performance on both CPython and PyPy
* Clean separation between Python and native code
* Consistent behavior across Python implementations

.. seealso::

   `Inside CPyExt <https://pypy.org/posts/2018/09/inside-cpyext-why-emulating-cpython-c-8083064623681286567.html>`__
   — PyPy blog post explaining why CPyExt emulation is problematic.

Dynamic vs Static Linking
-------------------------

The build process carefully manages linking:

**Dynamically Linked**
   * ``libc`` — Required for manylinux compatibility
   * System libraries that manylinux policy allows

**Statically Linked or Bundled**
   * LMDB library code
   * FlatBuffers runtime

Why This Matters
^^^^^^^^^^^^^^^^

* ``auditwheel`` compatibility is more important than "fully static" binaries
* Symbol versions must match manylinux policy
* ISA levels must be compatible with target platforms

Build Infrastructure
--------------------

Wheels are built using:

* **GitHub Actions** for CI/CD
* **manylinux containers** (``manylinux_2_28``) for Linux builds
* **cibuildwheel** for cross-platform wheel building
* **auditwheel** for verification

The build matrix includes:

* CPython 3.11, 3.12, 3.13, 3.14
* PyPy 3.11
* Linux x86-64 and ARM64

Version Synchronization
-----------------------

FlatBuffers is vendored to ensure version consistency:

* The ``flatc`` binary version matches the Python runtime
* The reflection schema (``.bfbs``) matches both
* zLMDB and Autobahn|Python can verify compatibility at runtime

This prevents subtle bugs from version mismatches between:

* Schema compilation (``flatc``)
* Runtime deserialization (Python library)
* Binary schema files (``.bfbs``)

Related Documentation
---------------------

* :doc:`wamp-zerocopy-dataplane` — Architecture overview of the
  FlatBuffers-based zero-copy data plane
* `FlatBuffers Documentation <https://flatbuffers.dev/>`__
* `LMDB Documentation <http://www.lmdb.tech/doc/>`__
* `PyPy Documentation <https://doc.pypy.org/>`__
* `manylinux Policy <https://github.com/pypa/manylinux>`__
