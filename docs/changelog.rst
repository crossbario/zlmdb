Changelog
=========

This document contains a reverse-chronological list of changes to zLMDB.

.. note::

    For detailed release information including artifacts,
    see :doc:`releases`.

26.10.1
-------

**Fix**

* Re-sync the vendored py-lmdb fork from 2.2.1 to **py-lmdb 3.0.0**, on **LMDB 0.9.36** (was 0.9.35). The LMDB 0.9 patch set is byte-identical to py-lmdb 3.0.0's, with five new hardening and fix patches: ``fix-large-write``, ``fix-overflow-page-size-mul``, ``validate-md-pad``, ``validate-ovpage-free`` and ``validate-freedb-record``. This fixes valid writes being rejected: an ``MDB_DUPFIXED`` database with 1-byte values failed from the fifth duplicate on with ``MDB_CORRUPTED`` (upstream jnwatson/py-lmdb#481; zLMDB 26.7.1 is affected). New in the binding: the offline verifier (``verify.py``) (#169)
* Wheels could ship without the bundled ``flatc`` when its build failed: 3 of the 27 zLMDB 26.7.1 wheels on PyPI lack it. A failed ``flatc`` build now fails the wheel build. **cmake is therefore required to build zLMDB from source** (sdist installs) (#181)
* A failed ``lmdb.open()`` (and so ``zlmdb.Database``) no longer prints an unraisable ``AttributeError: 'Environment' object has no attribute '_pid'`` from ``Transaction.__del__`` next to the real error, e.g. ``ReadersFullError``. The bug is inherited from py-lmdb 3.0.0's CFFI backend and reported upstream as jnwatson/py-lmdb#512 (#197)
* The ReadTheDocs build installs zLMDB with all its sources again (the LMDB and flatc submodules, and cmake), so the API reference is generated instead of left empty (#144)

**New**

* zLMDB bundles **both LMDB release lines**: LMDB 0.9.36 (data format v1) and LMDB 1.0.2 (data format v3), as py-lmdb 3.0.0 does, CFFI-only, in every wheel. An existing database is opened with the engine matching its format; the low-level ``zlmdb.lmdb`` API selects the engine for new environments with ``lib_version=`` or ``LMDB_DEFAULT_LIB_VERSION`` (#170)
* On PyPy, zLMDB depends on ``cbor2==5.9.0`` (pure Python), on CPython on ``cbor2>=6.1.0`` (the Rust extension), the same split as Autobahn|Python. Installing zLMDB on PyPy no longer needs a Rust toolchain. Data at rest is byte-identical between the two lines: a new test checks the CBOR encoding against golden vectors on every interpreter (#177)
* ``zlmdb.Database(..., lib_version=...)`` chooses the LMDB format of a database: ``"1.0"`` (LMDB 1.0.x, data format v3) or ``"0.9"`` (LMDB 0.9.x, data format v1). An existing database opens in its own format when ``lib_version`` is not given; an explicit ``lib_version`` that does not match it raises ``ValueError``. ``db.lib_version`` and ``Database.stats()`` (``"lib_version"``, ``"lmdb_version"``) report the format and the LMDB library in use. The new command ``zlmdb info DBPATH [--lib-version 1.0|0.9]`` shows them, and exits with 1 on a format mismatch. See :doc:`lmdb-formats` (#171)
* **Behaviour change:** new databases are created in **LMDB 1.0 format**. Such a file cannot be read by zLMDB before 26.10.1 or by LMDB 0.9 tools; pass ``lib_version="0.9"`` where that matters. Existing databases are not affected and are never converted; :doc:`lmdb-formats` shows how to convert one (#171)
* When ``zlmdb.Database`` cannot open a database because a process with the same PID in another PID namespace has it open (e.g. PID 1 in two containers sharing a volume), the ``RuntimeError`` now names this cause and the remedy, a shared PID namespace, instead of only "giving up after 3 retries". The exception type is unchanged (#196)
* New documentation page :doc:`deployment`: the supported storage and concurrency topologies (one kernel; containers with a shared PID namespace; local filesystems, including on network block devices) and the unsupported ones (several kernels or hosts, NFS), with the requirements, including that all processes sharing a database use the same C library family: a glibc and a musl process were found to hang on each other's lock file (#196)
* New documentation page :doc:`native-build`: what zLMDB vendors (both LMDB engines with their patch series, FlatBuffers) and why, how the native code is built, the requirements for a build from source, the wheel matrix, and how to check an installed copy, including running the bundled CVE regression tests against it. The wheels have no CPU-ISA floor: their native files contain no instructions beyond the x86-64 baseline (checked with ``objdump``) (#147)
* The cross-compilation promise is written down, in ``README.md``, :doc:`installation` and :doc:`native-build`: building zLMDB with a cross toolchain (Buildroot/Yocto, riscv64) is **roadmap**, with the support-status tags and test tiers shared with Autobahn|Python and Crossbar.io. What holds today is stated with its evidence: the sdist is self-contained (CI builds it from source on every commit), and zLMDB passes no architecture flags. :doc:`installation` is updated: Python 3.11+, musl, the source-build requirements (cmake), and LMDB and FlatBuffers are vendored, not dependencies (#145)

**Other**

* The ORM test suite and the LMDB examples run on both LMDB formats (#171)
* ARM64 Linux wheels are built natively on GitHub's ``ubuntu-24.04-arm`` runners instead of under QEMU emulation: build time per wheel went from 16-31 minutes to 3-5 minutes, and the intermittent compiler segfaults under QEMU are gone (#183)
* Every built wheel is smoke-tested in CI on every platform: installed into a fresh venv, both LMDB engines load and write their format, and the bundled ``flatc`` runs. ARM64 wheels are smoke-tested natively (#176, #180)
* The LMDB test suite runs once per bundled engine, each test in its own forked process with a time limit (#169, #170)
* Apply the ``zlmdb-py-lmdb-fork`` aspect, which checks the fork against a pinned upstream baseline (#178)
* Apply the ``python-package`` and ``way-a`` aspects: ``aspects.toml`` records the aspects zLMDB is a member of, the ``.autobahn-crossbar-ai`` submodule is added, ``.cicd`` and ``.ai`` are bumped, and ruff skips the vendored and submodule trees (#156, #160, #162, #164, #166)
* The release workflow can create the ``ci-cd`` release discussion (``discussions: write``), and a failure to create the discussion no longer aborts the job before the PyPI upload. This fixes what aborted the 26.7.1 release (#136)
* PyPy is pinned to **PyPy 3.11.15** (PyPy 7.3.23, the last release with the ``pp73`` ABI; PyPy 8.0 brings the new ``pp80`` ABI). ARM64 PyPy wheel builds install ``patchelf`` via pip instead of apt (#149)
* Add the missing SPDX / license headers to four source files (#152, #154)
* Adopt the contribution workflow shared by all WAMP projects: ``CONTRIBUTING.md``, the pull request template and ``.audit/README.md`` are deployed byte-identically from wamp-cicd (GitHub issue first, red → green tests, AI-assistance disclosure) and kept in sync by a CI drift check; project-specific notes moved to a new ``DEVELOPMENT.md``. ``.cicd`` and ``.ai`` are pinned to the same commits across the WAMP fleet, and the shared workflow recipes (``just where``, ``new-branch``, ``publish``, ``land``) are imported; the release meta-recipe ``publish`` is renamed ``publish-release`` (#149)
* The bundled ``flatc`` is built on all cores (``cmake --build --parallel``; ``CMAKE_BUILD_PARALLEL_LEVEL`` still wins): 237 s serial, 25 s with 16 jobs (#174)
* A multi-writer stress test (8 processes, 6,000 write transactions on one database) runs in CI, contributed by @p-r-a-v-i-n (#194, #53)
* The test matrix allows unprivileged user namespaces (Ubuntu 24.04 restricts them), so the PID-namespace tests run in CI instead of skipping (#196)

26.7.1
------

**Fix**

* Fix ``check_autobahn_flatbuffers_version_in_sync()`` comparing the build-time ``version()`` (which is ``(0, 0, 0, None, None)`` on installed wheels) — it now compares the reliably-stamped ``__version__``. Added a ``test_flatbuffers_version.py`` regression suite (#122)
* Make ``zlmdb.flatbuffers.version()`` reliable on installed wheels: fall back to the static vendored ``__version__`` when ``__git_version__`` is a bare commit hash or ``"unknown"`` (shallow clone / submodule absent from the sdist), returning ``(major, minor, patch, None, None)`` instead of ``(0, 0, 0, None, None)``. Also hardened ``hatch_build.py`` so it never stamps a non-parseable ``__git_version__``. Return shape unchanged (5-tuple) (#122)
* Fix the aarch64 CPython 3.14 wheel shipping the free-threaded ABI (``cp314t``) in the GIL ``cp314`` slot (``zlmdb-26.6.1-cp314-cp314t-...aarch64.whl``). Root cause: manylinux images pre-install both the GIL and free-threaded 3.14 under ``/opt/python`` and prepend them to ``PATH``, and ``uv`` resolved ``cpython-3.14`` to the free-threaded interpreter (first on ``PATH``). The ``create`` recipe now drops free-threaded ``…t/bin`` dirs from ``PATH`` for GIL envs so ``uv`` selects the GIL build. As defence-in-depth, ``just build`` also asserts (via ``_check-venv-abi``) that the interpreter's GIL/free-threaded status matches the env and aborts on mismatch, so a wrong-ABI wheel can never be published. A reserved ``cpy314t`` spec (``cpython-3.14t``) is added for a future free-threaded variant (#124)
* Bump the ``.cicd`` (wamp-cicd) submodule to include exact CPython ABI-tag matching in the shared ``check-release-fileset`` release-gate action, so a wrong-ABI wheel (e.g. ``cp314t`` in the ``cp314`` slot) is also rejected at release-fileset validation, not only by the build-time guard above (wamp-cicd #11, completes #124)

**New**

* Build and publish **musllinux** (Alpine / musl-libc) binary wheels for **CPython 3.11–3.14** on **x86-64 and ARM64** (``musllinux_1_2_{x86_64,aarch64}``). Previously ``pip``/``uv install zlmdb`` on Alpine fell back to a failing source build (the clang-built python-build-standalone interpreter's ``--rtlib=compiler-rt`` CFLAG is rejected by Alpine's gcc); building the LMDB CFFI extension inside the pypa musllinux container fixes this. PyPy-on-musl is tracked separately (#128) (#126)

**Other**

* Add CalVer / PEP 440 version-management ``just`` recipes (``file-version``, ``bump-dev``, ``bump-next``, ``prep-release``) mirroring Crossbar.io, and document the versioning policy in ``CONTRIBUTING.md`` (#123)

26.6.1
------

**Security**

* Vendor py-lmdb's full LMDB corruption-hardening patch set into the CFFI build:
  the five ``CVE-2019-1622x`` fixes plus the additional ``validate-*`` /
  ``guard-*`` page/node/overflow validation patches that upstream LMDB does not
  carry. Add ``cve_test.py`` (vendored from py-lmdb) as a regression suite.
  Against the previous build, 12 of 25 crafted-corruption tests crashed
  (SIGSEGV/SIGABRT/SIGBUS/SIGFPE) and 8 silently accepted corruption; all 25
  now pass. (#111)

**New**

* Bump vendored LMDB ``0.9.33`` → ``0.9.35`` (picks up upstream fixes; the
  former ``its-10346.patch`` is now incorporated upstream). (#111)
* Re-fork the vendored py-lmdb wrapper at **py-lmdb 2.2.1** (previously ~1.4.x).
  The fork stays **CFFI-only** (no CPython C-extension / CPyExt is ever shipped
  or imported), preserving first-class PyPy support and modern x86-64/ARM64
  binary wheels. Also vendors the new ``aio`` asyncio API and type stubs. (#111)
* Bump vendored FlatBuffers ``v25.9.23`` → ``v25.12.19`` (Python runtime and
  reflection regenerated). (#108)

**Fix**

* Fail wheel builds hard when the mandatory LMDB CFFI extension does not
  compile, instead of silently degrading to a pure-Python (``py3-none-any``)
  wheel. A transient compile crash (e.g. a ``gcc`` SIGSEGV under QEMU ARM64
  emulation) now aborts the build with a non-zero exit so CI can retry it,
  rather than uploading a structurally valid but non-functional artifact. (#116)
* Make wheel builds cross-compilation friendly (e.g. Buildroot/aarch64):
  ``flatc`` is still built and bundled into the wheel, but is no longer
  *executed* during the build. ``reflection.bfbs`` is now committed and shipped
  as package data, so packaging never runs a target-architecture ``flatc`` on
  the build host. (#107)

**Other**

* Add ``setuptools`` to the build-tools install (required by CFFI on
  Python ≥ 3.12).
* Follow upstream ``ty`` releases: declare ``ty>=0.0.44`` as a dev dependency
  and adapt the ``check-typing`` recipe to current ``ty`` rule names.
* ``generate-flatbuffers-reflection`` now builds a version-matched host
  ``flatc`` from the vendored ``deps/flatbuffers`` and generates both
  ``reflection.bfbs`` and the ``reflection/*.py`` wrappers. (#107)
* Sync the ``.cicd`` and ``.ai`` shared submodules to canonical. (#113)

25.12.3
-------

**Fix**

* Fix FlatBuffers reflection imports: convert 18 absolute imports to relative imports
  for proper package-relative resolution (#104)
* Fix release.yml: add 'nightly' check to release-development job condition
  to match other repos (cfxdb, wamp-xbr, txaio, crossbar)

**New**

* Add ``test-reflection`` recipe and ``scripts/test_reflection.py`` for CI validation
  of FlatBuffers reflection module imports
* Add FlatBuffers documentation:

  - ``docs/flatbuffers/index.rst`` - Overview of FlatBuffers integration
  - ``docs/flatbuffers/wamp-zerocopy-dataplane.rst`` - Zero-copy data plane architecture (#98)
  - ``docs/flatbuffers/vendoring-design-and-technology.rst`` - Vendoring and native binaries (#99)

**Other**

* Synchronize CI/CD, FlatBuffers vendoring and wamp-ai/wamp-cicd submodules
  between autobahn-python and zlmdb (#101)
* Add ``fix-flatbuffers-reflection-imports`` recipe for automated import fixes

25.12.2
-------

**Fix**

* Fix sdist packaging to include flatbuffers grpc/ source files (#92, #93)
* Fix release.yml targets to match actual wheel manylinux tags
* Make smoke tests required for sdist validation (sdist must provide same functionality as wheels)

**Other**

* Improve CI workflow ordering with 5-phase execution and filesystem sync points
* Add artifact verification smoke tests to CI workflows
* Update .github/workflows/README.md with correct manylinux tags and wheel details

25.12.1
-------

**New**

* Add vendored Flatbuffers (v25.9.23) (#1761)
* Add WAMP serdes functional and benchmark testing; WAMP-Flatbuffers; WAMP Serializer Composition (transport/payload) (#1765)

**Fix**

* Fix 1757 (#1758)
* Fix 1767 (#1769)
* Fix 1771 complete (#1774)

**Other**

* Rel v25.10.2 (#1734)
* Rel v25.10.2 part2 (#1741)
* WAMP Flatbuffers serialization test coverage; WAMP message classes refactoring (#1773)
* Modernization phase 1.1 (#1785)
*  Phase 1.2: Build Tooling Modernization (#1788)
* Phase 1.3: CI/CD Modernization (#1791)
* Rel25 12 1 (#1794)
* Modernization phase 1.4 (#1797)
* Add Sphinx label to changelog for cross-references
* add changelog/release-notes for 25.12.1 - first draft
* Refactor release recipes to use external scripts
* Add automated release docs generation recipes
* Add changelog and release notes for 25.12.1
* Bump .cicd submodule: fix recursive copy for directories
* Bump .cicd submodule: fix download retry wiping other artifacts
* Bump .cicd submodule: prefix matching for artifact download
* Bump .cicd submodule: include-hidden-files fix
* Remove workaround for hidden files, use .audit/ directly
* Workaround: copy .audit to non-hidden dir for artifact upload
* Fix container jobs: use relative paths for artifact upload
* Fix container job: capture workspace path via pwd at runtime
* Debug container workspace paths and retry github.workspace
* Fix container job: get workspace path at runtime via pwd
* Use env.GITHUB_WORKSPACE for container job artifact paths
* Use absolute paths for all download-artifact-verified calls
* Use absolute paths for all upload-artifact-verified calls
* Fix summary upload: use relative path for .audit directory
* Fix summary upload: use directory path instead of file path
* Pass artifact names via job outputs for verified downloads
* Add verbose permission logging to debug wstest artifact uploads
* Use sudo chown to fix wstest directory permissions
* Fix permissions on wstest directories before artifact upload
* Fix multi-path artifact upload for verified action
* Replace actions/*-artifact@v4 with verified actions
* Fix GitHub Discussions category for CI-CD notifications
* Add automatic GitHub Discussions post for stable releases
* Add check-release-fileset action to release workflows
* Fix release-stable job: use dynamic artifact names with meta-checksums
* Add tag triggers to all workflows
* Update wamp-cicd submodule for CRLF line ending fixes
* Fix wheels-docker workflow: remove source dist copy
* Separate wheel and source distribution builds
* Add self-verification to catch GitHub artifact serving bugs
* Use unique artifact names with meta-checksum for reliable downloads
* Replace pattern-based downloads with individual verified downloads
* Update .cicd submodule: add overwrite parameter to download-artifact-verified
* Update .cicd submodule: fix unzip to force overwrite without prompting
* Update .cicd submodule: fix download-artifact-verified to use gh api
* fix: Output Sphinx docs to RTD-required directory
* fix RTD project name
