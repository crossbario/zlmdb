Native Build and Vendored Code
==============================

zLMDB contains native code, but no system library: the C sources of LMDB and
the FlatBuffers compiler are vendored into the source tree, built when the
wheel is built, and shipped inside it. This page describes what is vendored,
how it is built, which CPUs the result runs on, and how to check an installed
copy.

.. contents::
   :local:
   :depth: 2

What zLMDB vendors
------------------

**LMDB, both release lines, patched.** zLMDB bundles two LMDB engines,
compiled from the Git submodules ``lmdb-upstream`` and ``lmdb-upstream-1.0``:

.. list-table::
   :header-rows: 1
   :widths: 15 15 20 25 25

   * - LMDB
     - Data format
     - Patches
     - CFFI module
     - Selected by
   * - 0.9.36
     - v1
     - 25 (``lmdb-patches/``)
     - ``_lmdb_cffi``
     - ``lib_version="0.9"``
   * - 1.0.2
     - v3
     - 23 (``lmdb-patches-1.0/``)
     - ``_lmdb1_cffi``
     - ``lib_version="1.0"``

At build time, ``build_lmdb.py`` copies each engine's sources out of its
submodule and applies its patch series in a fixed order. A patch that does
not apply fails the build. The patch set comes from py-lmdb 3.0.0
(jnwatson/py-lmdb), which zLMDB vendors as its low-level binding
(``zlmdb.lmdb``). It consists of:

* the fixes for the five LMDB CVEs of 2019: CVE-2019-16224 (validate the
  database flags), -16225 (reject dirty pages), -16226 (validate the node
  size on delete), -16227 (guard against a NULL xcursor) and -16228
  (validate the page size);
* 14 ``validate-*`` patches and a further NULL guard, the same on both
  engines. They check the
  bounds and consistency of a ``data.mdb`` read from disk (page and subpage
  bounds, node sizes, overflow pages, tree depth and root, free-list
  records, ...). With these, a corrupted or hostile database file raises an
  error instead of causing out-of-bounds memory access;
* API and bug fixes, e.g. ``env-copy-txn`` (needed by the binding),
  ``fix-large-write`` and ``win32-sparse-file`` (these two only in the LMDB
  0.9 series; on LMDB 1.0, the CVE-2019-16225 fix is a different patch,
  ``validate-mp-txnid``).

Each patch series is listed, with its status, in ``PATCH-STATUS.md`` next to
it. The regression tests for the hardening patches are in
``src/zlmdb/tests/lmdb/cve_test.py``, and run in CI against both engines.
Which engine an existing database needs, and how the two formats relate, is
described in :doc:`lmdb-formats`.

**FlatBuffers.** ``deps/flatbuffers`` is pinned to FlatBuffers v25.12.19.
zLMDB ships from it:

* the FlatBuffers **Python runtime**, as ``zlmdb.flatbuffers``, with the
  compiled reflection schema ``reflection.bfbs``. The ``.bfbs`` file is
  committed, so building a wheel never has to run ``flatc``;
* the FlatBuffers compiler **flatc**, built from source and installed as the
  ``flatc`` command (``zlmdb._flatc``).

Autobahn|Python vendors the same FlatBuffers revision. Crossbar.io uses both
packages together, with FlatBuffers for data in transit (Autobahn) and data at
rest (zLMDB), so the two copies are kept at the same commit:
``autobahn.check_zlmdb_flatbuffers_version_in_sync()`` checks this, and both
projects test it. A FlatBuffers update is always done in both projects at
once. See :doc:`flatbuffers/vendoring-design-and-technology` for the
FlatBuffers side.

How the native code is built
----------------------------

Building a wheel (``hatch_build.py``) runs these steps:

1. ``build_lmdb.py`` prepares both LMDB engines (copy, then patch);
2. ``build_cffi_lmdb.py`` compiles one CFFI module per engine, plus
   ``_lmdb_types``;
3. cmake builds ``flatc`` from ``deps/flatbuffers``.

The LMDB modules are compiled with exactly these extra compiler arguments::

    -UNDEBUG -DHAVE_PATCHED_LMDB=1 -w

zLMDB adds **no architecture flags**: no ``-march``, ``-mtune`` or
``-mcpu``, and no SIMD or other ISA-specific code. All other compiler flags
come from the build environment: the Python installation the build runs with
(``sysconfig``) and ``CC``/``CFLAGS``. This also holds for a cross toolchain:
its own target flags govern code generation unchanged.

Every step is mandatory. If the LMDB extension or ``flatc`` cannot be built,
the build fails. There is no pure-Python fallback, and since #181 no wheel
without ``flatc``.

Requirements for a build from source:

* a C compiler (LMDB, CFFI) and a C++ compiler (``flatc``);
* **cmake**;
* ``patch`` (Linux and macOS; on Windows the build uses ``patch-ng`` instead);
* the Python build dependencies, which pip installs by itself: ``hatchling``,
  ``cffi`` and ``setuptools`` (and ``patch-ng`` on Windows).

**The source distribution is self-contained.** The sdist on PyPI contains the
LMDB sources of both engines, both patch series, the FlatBuffers sources that
``flatc`` needs, and the committed ``reflection.bfbs``. Building from it needs
neither Git nor network access to source repositories. CI checks this for
every commit: it installs the freshly built sdist into a new virtualenv on
Linux x86-64, which compiles everything from source, and runs the smoke tests
against the result.

CPU requirements: no ISA floor
------------------------------

Because zLMDB compiles portable C and C++ with the target's default flags, a
wheel has no CPU feature requirement beyond the baseline of its architecture.
An x86-64 wheel runs on any x86-64 CPU, including ones without SSE4.2 or AVX.

This was checked on the 26.10.1 wheels for CPython 3.14 on x86-64 (manylinux
and musllinux), by disassembling every native file in them (``objdump -d``)
and searching for instructions beyond SSE2 (the x86-64 baseline: SSSE3,
SSE4.x, AVX/AVX2/AVX-512, BMI, POPCNT, ...):

* both LMDB modules, ``_lmdb_types`` and ``flatc``: **none**;
* the C++ runtime libraries the musllinux wheel bundles for ``flatc``: only
  ``tzcnt`` encodings, which are ``rep bsf`` and which CPUs without BMI
  execute as ``bsf``. These are in the toolchain's library code, not in
  zLMDB's.

Autobahn|Python is different here. Its optional NVX extension is compiled for
``x86-64-v2`` (SSE4.2) on x86-64, and its documentation covers that case.

Wheels
------

zLMDB publishes binary wheels for:

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - Platform
     - Architectures
     - Python
   * - Linux, glibc (``manylinux_2_28``)
     - x86-64, ARM64
     - CPython 3.11-3.14, PyPy 3.11
   * - Linux, musl (``musllinux_1_2``, e.g. Alpine)
     - x86-64, ARM64
     - CPython 3.11-3.14
   * - macOS 15+ (``macosx_15_0``)
     - ARM64
     - CPython 3.11-3.14, PyPy 3.11
   * - Windows
     - x86-64
     - CPython 3.11-3.14

Linux wheels are built in the PyPA ``manylinux_2_28`` and ``musllinux_1_2``
containers and repaired with ``auditwheel``. ARM64 Linux wheels are built
natively, on ARM64 runners. The release notes (:doc:`releases`) list the
exact files of every release.

Every wheel is smoke-tested in CI on its own platform: installed into a fresh
virtualenv, both LMDB engines load and write their format, and the bundled
``flatc`` runs.

Checking an installed copy
--------------------------

The installed version, the LMDB engines and ``flatc``:

.. code-block:: console

    $ python -c "import zlmdb; print(zlmdb.__version__)"
    26.10.1
    $ python -c "import zlmdb.lmdb as lmdb; print(lmdb.version())"
    (0, 9, 36)
    $ flatc --version
    flatc version 25.12.19

``zlmdb info DBPATH`` shows which LMDB format and engine a database uses.

That the LMDB engines carry the hardening patches: the regression tests for
them are installed with zLMDB, and can be run against the installed copy, once
per engine (needs ``pytest``):

.. code-block:: console

    $ T=$(python -c "import os, zlmdb; print(os.path.join(os.path.dirname(zlmdb.__file__), 'tests', 'lmdb', 'cve_test.py'))")
    $ LMDB_DEFAULT_LIB_VERSION=0 python -m pytest -q --noconftest "$T"
    42 passed, 3 skipped
    $ LMDB_DEFAULT_LIB_VERSION=1 python -m pytest -q --noconftest "$T"
    37 passed, 8 skipped

(The numbers are those of 26.10.1 on Linux. Tests that do not apply to an
engine are skipped.) The flag ``-DHAVE_PATCHED_LMDB=1`` in
``zlmdb._lmdb_vendor._config.CONFIG['extra_compile_args']``, and
``zlmdb.lmdb.version(subpatch=True)``, only report the build configuration;
they are not a check of the patches themselves.

.. _cross-compilation:

Cross-compilation and embedded targets
--------------------------------------

Build systems for embedded Linux, such as Buildroot and Yocto, build Python
packages from the sdist with a cross toolchain. What zLMDB promises for that
is stated with three status tags, used with the same meaning by
Autobahn|Python, zLMDB and Crossbar.io:

* **Supported**: named targets, gated in CI: Tier 1 per-commit, Tier 2
  nightly.
* **Best-effort**: expected to work, not gated in CI; bug reports welcome.
* **Roadmap**: intended direction, **not yet backed by tests**.

And two test tiers:

* **Tier 1, cross-build ("baking")**: the native extension cross-compiles for
  the target, and the artifact is verified (``readelf -h`` shows the expected
  machine, plus an import and functional smoke test). Fast; every commit.
* **Tier 2, run on target**: boot the target under QEMU system emulation and
  run the project's own test suite there. Slow; nightly.

The reference target for both tiers is **riscv64** (rv64gc / lp64d) via
Buildroot, cross-built on x86-64, glibc first and musl second, booted under
``qemu-system-riscv64``. It is a true cross-build, and there are no riscv64
wheels, so every riscv64 user builds from source.

Status:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Artifact
     - Tier 1 (cross-build)
     - Tier 2 (run on target)
   * - Autobahn|Python
     - **Roadmap** (Supported once the job lands)
     - **Roadmap**
   * - **zLMDB**
     - **Roadmap** (Supported once the job lands)
     - **Roadmap**
   * - Crossbar.io
     - **Roadmap**
     - **Roadmap** (ultimate goal)

Rows move up as tiers land. Nothing claims more than CI demonstrates.

What a cross-build of zLMDB can rely on today:

* **The sdist is self-contained** (see above), which CI checks in a native
  build on every commit.
* **No architecture flags.** zLMDB passes none, so the cross toolchain's own
  ``-march``/``-mtune``/``-mcpu`` govern code generation unchanged.
* **No flatc run at build time.** The reflection schema is committed, so the
  build never executes a ``flatc`` it has just compiled, which a cross-build
  could not do.

What is not tested yet, and belongs to Tier 1:

* that the cross toolchain's ``CC``/``CXX`` reach both the CFFI compilation
  and the cmake build of ``flatc`` (``flatc`` is built for the target, as the
  ``flatc`` command of the target system);
* LMDB on the target: 64-bit file offsets, page size and alignment on
  rv64gc, and that both patch series hold there.
