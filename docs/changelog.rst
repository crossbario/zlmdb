Changelog
=========

This document contains a reverse-chronological list of changes to zLMDB.

.. note::

    For detailed release information including artifacts,
    see :doc:`releases`.

26.7.1
------

**Fix**

* Fix ``check_autobahn_flatbuffers_version_in_sync()`` comparing the build-time ``version()`` (which is ``(0, 0, 0, None, None)`` on installed wheels) — it now compares the reliably-stamped ``__version__``. Added a ``test_flatbuffers_version.py`` regression suite (#122)
* Make ``zlmdb.flatbuffers.version()`` reliable on installed wheels: fall back to the static vendored ``__version__`` when ``__git_version__`` is a bare commit hash or ``"unknown"`` (shallow clone / submodule absent from the sdist), returning ``(major, minor, patch, None, None)`` instead of ``(0, 0, 0, None, None)``. Also hardened ``hatch_build.py`` so it never stamps a non-parseable ``__git_version__``. Return shape unchanged (5-tuple) (#122)
* Guard wheel builds against a wrong ABI tag: ``just build`` now asserts (via ``_check-venv-abi``) that the building interpreter's GIL / free-threaded status matches the target env, so a free-threaded ``cp314t`` wheel can never be published in the GIL ``cp314`` slot — the aarch64 mis-tag shipped in 26.6.1 (``zlmdb-26.6.1-cp314-cp314t-...aarch64.whl``). Root cause was an older ``uv`` resolving ``cpython-3.14`` to the free-threaded interpreter on aarch64; current ``uv`` resolves to GIL (verified under QEMU aarch64). A reserved ``cpy314t`` spec (``cpython-3.14t``) is added for a future free-threaded variant (#124)
* Bump the ``.cicd`` (wamp-cicd) submodule to include exact CPython ABI-tag matching in the shared ``check-release-fileset`` release-gate action, so a wrong-ABI wheel (e.g. ``cp314t`` in the ``cp314`` slot) is also rejected at release-fileset validation, not only by the build-time guard above (wamp-cicd #11, completes #124)

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
