Getting Started
===============

Choose your starting point based on your needs:

**New to zlmdb?**
   Start with the :doc:`gettingstarted` guide, then:

   - **Want simple key-value storage?** → :doc:`lmdb/quickstart`
   - **Want object persistence with schemas?** → :doc:`orm/quickstart`

**Coming from py-lmdb?**
   zlmdb's low-level API is a drop-in replacement:

   - See :doc:`lmdb/index` for the compatibility layer
   - Your existing py-lmdb code should work unchanged

**Building a production application?**
   Study the ORM patterns from real projects:

   - :doc:`orm/schema-design` - Schema architecture patterns
   - :doc:`orm/indexes` - Efficient lookups and queries
   - :doc:`orm/time-series` - Time-series data modeling
   - :doc:`orm/best-practices` - Production-proven patterns


Installation
-------------

zlmdb provides pre-built binary wheels for all major platforms, making installation simple and dependency-free.

Install zlmdb using pip::

   pip install zlmdb

That's it! The wheel includes:

- LMDB library (vendored, no system dependency)
- FlatBuffers library (vendored)
- CFFI bindings (pre-compiled)

No C compiler or external libraries required.

To make sure `pip` installs the correct **binary wheel** and not the source distribution, please try the following:

.. code-block:: console

    python -m pip install --upgrade pip setuptools wheel
    python -m pip install --only-binary=:all: zlmdb

If that still doesn’t work, please run this to help us see what tags your Python installation supports:

.. code-block:: console

    python -m pip debug --verbose

and then retry with verbose output to confirm what `pip` is doing:

.. code-block:: console

    pip install -v zlmdb


Wheel Compatibility
-------------------

zlmdb provides native binary wheels for the following combinations:

.. list-table:: Supported Platforms
   :header-rows: 1
   :widths: 15 15 25 45

   * - Python
     - OS
     - Architecture
     - Platform Tag
   * - CPython 3.11
     - Linux
     - x86-64
     - ``linux_x86_64``, ``manylinux_2_34_x86_64``
   * - CPython 3.11
     - Linux
     - ARM64
     - ``linux_aarch64``, ``manylinux_2_28_aarch64``
   * - CPython 3.11
     - macOS
     - ARM64 (Apple Silicon)
     - ``macosx_10_9_universal2``
   * - CPython 3.11
     - Windows
     - x86-64
     - ``win_amd64``
   * - CPython 3.12
     - Linux
     - x86-64
     - ``linux_x86_64``, ``manylinux_2_34_x86_64``
   * - CPython 3.12
     - Linux
     - ARM64
     - ``linux_aarch64``, ``manylinux_2_28_aarch64``
   * - CPython 3.12
     - macOS
     - ARM64 (Apple Silicon)
     - ``macosx_10_13_universal2``
   * - CPython 3.12
     - Windows
     - x86-64
     - ``win_amd64``
   * - CPython 3.13
     - Linux
     - x86-64
     - ``linux_x86_64``, ``manylinux_2_34_x86_64``
   * - CPython 3.13
     - Linux
     - ARM64
     - ``linux_aarch64``, ``manylinux_2_28_aarch64``
   * - CPython 3.13
     - macOS
     - ARM64 (Apple Silicon)
     - ``macosx_15_0_arm64``
   * - CPython 3.13
     - Windows
     - x86-64
     - ``win_amd64``
   * - CPython 3.14
     - Linux
     - x86-64
     - ``linux_x86_64``, ``manylinux_2_34_x86_64``
   * - CPython 3.14
     - Linux
     - ARM64 (free-threaded)
     - ``linux_aarch64``, ``manylinux_2_28_aarch64``
   * - CPython 3.14
     - macOS
     - ARM64 (Apple Silicon)
     - ``macosx_15_0_arm64``
   * - CPython 3.14
     - Windows
     - x86-64
     - ``win_amd64``
   * - PyPy 3.11
     - Linux
     - x86-64
     - ``linux_x86_64``, ``manylinux_2_34_x86_64``
   * - PyPy 3.11
     - Linux
     - ARM64
     - ``linux_aarch64``, ``manylinux_2_36_aarch64``
   * - PyPy 3.11
     - macOS
     - ARM64 (Apple Silicon)
     - ``macosx_11_0_arm64``

.. note::
   **manylinux wheels** are portable across Linux distributions:

   - ``manylinux_2_28``: Compatible with glibc 2.28+ (RHEL 8+, Ubuntu 18.04+, Debian 10+)
   - ``manylinux_2_34``: Compatible with glibc 2.34+ (RHEL 9+, Ubuntu 22.04+, Debian 12+)
   - ``manylinux_2_36``: Compatible with glibc 2.36+ (for PyPy ARM64 builds)


Platform-Specific Notes
-----------------------

Linux
~~~~~

**x86-64 (Intel/AMD)**

zlmdb provides two wheel variants:

1. **Native wheel** (``linux_x86_64``):
   - Built directly on the host system
   - For local testing and development

2. **Portable wheel** (``manylinux_2_34_x86_64``):
   - Compatible with most modern Linux distributions
   - Recommended for production deployment
   - Works on RHEL 9+, Ubuntu 22.04+, Debian 12+, etc.

**ARM64 (aarch64)**

zlmdb provides portable wheels built with Docker + QEMU:

- ``manylinux_2_28_aarch64``: For CPython on ARM64 Linux
- ``manylinux_2_36_aarch64``: For PyPy on ARM64 Linux

Tested on:

- Raspberry Pi 4 (Ubuntu Server 22.04)
- AWS Graviton instances
- Oracle Cloud ARM instances
- Apple Silicon via Docker (Linux containers)

macOS
~~~~~

**Apple Silicon (ARM64)**

zlmdb provides universal wheels for macOS on Apple Silicon:

- ``macosx_10_9_universal2``: CPython 3.11 (compatible with macOS 10.9+)
- ``macosx_10_13_universal2``: CPython 3.12 (compatible with macOS 10.13+)
- ``macosx_15_0_arm64``: CPython 3.13/3.14 (requires macOS 15+)
- ``macosx_11_0_arm64``: PyPy 3.11 (requires macOS 11+)

.. note::
   Intel Macs are **not currently supported** with binary wheels. You can build from source if needed.

Windows
~~~~~~~

**x86-64**

zlmdb provides wheels for 64-bit Windows (Windows 10+, Windows Server 2016+):

- Built with Visual Studio 2019/2022
- Includes all required DLLs
- No Visual C++ Runtime installation needed


Verifying Installation
----------------------

After installation, verify that zlmdb works correctly:

**Check version and platform:**

.. code-block:: python

   import zlmdb
   print(zlmdb.__version__)
   print(zlmdb.lmdb.version())  # LMDB library version

Expected output::

   25.10.1
   (0, 9, 33, 'LMDB 0.9.33: (2024-09-20)')

**Quick functionality test:**

.. code-block:: python

   import zlmdb
   import tempfile
   import os

   # Create temporary database
   with tempfile.TemporaryDirectory() as tmpdir:
       dbpath = os.path.join(tmpdir, 'test.db')

       # Test low-level API
       env = zlmdb.lmdb.open(dbpath)
       with env.begin(write=True) as txn:
           txn.put(b'key', b'value')
       with env.begin() as txn:
           assert txn.get(b'key') == b'value'
       env.close()

       # Test ORM API
       db = zlmdb.Database.open(dbpath)
       db.__enter__()
       with db.begin(write=True) as txn:
           # ORM operations here
           pass
       db.__exit__(None, None, None)

   print("✅ zlmdb is working correctly!")


Installing from Source
----------------------

If binary wheels are not available for your platform, you can build from source.

**Prerequisites:**

- C compiler (GCC, Clang, or MSVC)
- Python development headers
- Git (to clone the repository)
- `just <https://github.com/casey/just>`_ (task runner)
- `uv <https://github.com/astral-sh/uv>`_ (fast package manager)

**Build steps:**

.. code-block:: bash

   # Clone repository
   git clone --recursive https://github.com/crossbario/zlmdb.git
   cd zlmdb

   # Install just and uv
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and build
   just create
   just install-dev
   just build

   # Install the built wheel
   pip install dist/zlmdb-*.whl

See the main `README.md <https://github.com/crossbario/zlmdb/blob/master/README.md>`_ for the complete development workflow.


PyPy Installation
-----------------

zlmdb is optimized for PyPy through CFFI-based bindings:

**Install PyPy** (if not already installed):

- Download from `pypy.org <https://www.pypy.org/download.html>`_
- Or use a package manager: ``apt install pypy3`` (Ubuntu/Debian)

**Install zlmdb on PyPy:**

.. code-block:: bash

   pypy3 -m pip install zlmdb

**Why use PyPy with zlmdb?**

- **JIT compilation**: 2-10x faster for computation-heavy workloads
- **CFFI-optimized**: zlmdb uses CFFI (not CPyExt), enabling full JIT optimization
- **Production-proven**: Used by Crossbar.io for high-throughput routing

See :doc:`performance` for PyPy vs CPython benchmarks.


Upgrading
---------

Upgrade to the latest version::

   pip install --upgrade zlmdb

**Check what changed:**

See the `CHANGELOG <https://github.com/crossbario/zlmdb/blob/master/CHANGELOG.md>`_ for release notes.


Uninstalling
------------

Remove zlmdb::

   pip uninstall zlmdb

zlmdb has no global state or system-wide configuration, so uninstallation is clean.


Troubleshooting
---------------

**Import error: "No module named '_cffi_backend'"**

Install CFFI::

   pip install cffi

This should be installed automatically as a dependency, but some environments may need manual installation.

**Import error on ARM64 Linux**

Ensure you're using a compatible glibc version:

.. code-block:: bash

   ldd --version

- For CPython wheels: glibc 2.28 or newer required
- For PyPy wheels: glibc 2.36 or newer required

**Windows DLL load failed**

Ensure you have the Visual C++ Redistributable installed:

- Download from `Microsoft <https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist>`_

**macOS "cannot be opened because the developer cannot be verified"**

This shouldn't happen with pip-installed wheels. If it does::

   xattr -d com.apple.quarantine /path/to/zlmdb/*.so


Getting Help
------------

If you encounter installation issues:

1. Check the `issue tracker <https://github.com/crossbario/zlmdb/issues>`_
2. Include in your report:
   - Operating system and version (``uname -a`` on Linux/macOS, ``ver`` on Windows)
   - Python version (``python --version``)
   - pip version (``pip --version``)
   - Full error traceback

Next Steps
----------

After installation:

- **New to zlmdb?** → Start with :doc:`lmdb/quickstart` or :doc:`orm/quickstart`
- **Exploring features?** → See :doc:`introduction` for an overview
- **Performance testing?** → See :doc:`performance` for benchmarks

.. seealso::

   - `PyPI Package <https://pypi.org/project/zlmdb/>`_
   - `GitHub Releases <https://github.com/crossbario/zlmdb/releases>`_
   - `Wheel Compatibility Tags <https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/>`_
