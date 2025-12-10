Release Notes
=============

This page provides links to release artifacts for each version of zLMDB.

For detailed changelog entries, see :doc:`changelog`.

25.12.1 (2025-12-10)
--------------------

**Release Type:** Stable release

**Source Build:** `master-202512092131 <https://github.com/crossbario/autobahn-python/releases/tag/master-202512092131>`__

WebSocket Conformance
^^^^^^^^^^^^^^^^^^^^^

Autobahn|Python passes 100% of the WebSocket conformance tests from the
`Autobahn|Testsuite <https://github.com/crossbario/autobahn-testsuite>`_.

Configuration: with-nvx (NVX acceleration)
""""""""""""""""""""""""""""""""""""""""""

**Client Conformance**

.. list-table::
   :header-rows: 1
   :widths: 60 20 10

   * - Testee
     - Cases
     - Status
   * - ``Autobahn/25.12.1-NVXCFFI/1.18.0.dev0-Twisted/25.5.0-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/1.18.0.dev0-asyncio-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-Twisted/25.5.0-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-Twisted/25.5.0-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-asyncio-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-asyncio-CPython/3.14.2``
     - 246 / 246
     - ✅

**Server Conformance**

.. list-table::
   :header-rows: 1
   :widths: 60 20 10

   * - Testee
     - Cases
     - Status
   * - ``Autobahn/25.12.1-NVXCFFI/1.18.0.dev0-Twisted/25.5.0-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/1.18.0.dev0-asyncio-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-Twisted/25.5.0-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-Twisted/25.5.0-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-asyncio-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-NVXCFFI/2.0.0-asyncio-CPython/3.14.2``
     - 246 / 246
     - ✅

Configuration: without-nvx (pure Python)
""""""""""""""""""""""""""""""""""""""""""

**Client Conformance**

.. list-table::
   :header-rows: 1
   :widths: 60 20 10

   * - Testee
     - Cases
     - Status
   * - ``Autobahn/25.12.1-Twisted/25.5.0-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-Twisted/25.5.0-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-Twisted/25.5.0-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-PyPy/3.11.13``
     - 246 / 246
     - ✅

**Server Conformance**

.. list-table::
   :header-rows: 1
   :widths: 60 20 10

   * - Testee
     - Cases
     - Status
   * - ``Autobahn/25.12.1-Twisted/25.5.0-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-Twisted/25.5.0-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-Twisted/25.5.0-PyPy/3.11.13``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-CPython/3.11.14``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-CPython/3.14.2``
     - 246 / 246
     - ✅
   * - ``Autobahn/25.12.1-asyncio-PyPy/3.11.13``
     - 246 / 246
     - ✅

Release Artifacts
^^^^^^^^^^^^^^^^^

Binary wheels are available for the following platforms:

.. list-table:: Platform Support Matrix
   :header-rows: 1
   :widths: 20 15 15 50

   * - Platform
     - Python
     - Arch
     - Wheel
   * - Linux
     - CPython 3.11
     - x86_64
     - ``autobahn-25.12.1-cp311-cp311-manylinux1_x86_64.manylinux_2_34_x86_64.manylinux_2_5_x86_64.whl``
   * - Linux
     - CPython 3.11
     - ARM64
     - ``autobahn-25.12.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl``
   * - Linux
     - CPython 3.12
     - x86_64
     - ``autobahn-25.12.1-cp312-cp312-manylinux1_x86_64.manylinux_2_34_x86_64.manylinux_2_5_x86_64.whl``
   * - Linux
     - CPython 3.13
     - x86_64
     - ``autobahn-25.12.1-cp313-cp313-manylinux1_x86_64.manylinux_2_34_x86_64.manylinux_2_5_x86_64.whl``
   * - Linux
     - CPython 3.13
     - ARM64
     - ``autobahn-25.12.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl``
   * - Linux
     - CPython 3.14
     - x86_64
     - ``autobahn-25.12.1-cp314-cp314-manylinux1_x86_64.manylinux_2_34_x86_64.manylinux_2_5_x86_64.whl``
   * - Linux
     - PyPy 3.11
     - x86_64
     - ``autobahn-25.12.1-pp311-pypy311_pp73-manylinux1_x86_64.manylinux_2_34_x86_64.manylinux_2_5_x86_64.whl``
   * - Linux
     - PyPy 3.11
     - ARM64
     - ``autobahn-25.12.1-pp311-pypy311_pp73-manylinux2014_aarch64.manylinux_2_17_aarch64.whl``
   * - macOS
     - CPython 3.13
     - ARM64
     - ``autobahn-25.12.1-cp313-cp313-macosx_15_0_arm64.whl``
   * - macOS
     - CPython 3.14
     - ARM64
     - ``autobahn-25.12.1-cp314-cp314-macosx_15_0_arm64.whl``
   * - macOS
     - PyPy 3.11
     - ARM64
     - ``autobahn-25.12.1-pp311-pypy311_pp73-macosx_15_0_arm64.whl``
   * - Windows
     - CPython 3.11
     - x86_64
     - ``autobahn-25.12.1-cp311-cp311-win_amd64.whl``
   * - Windows
     - CPython 3.12
     - x86_64
     - ``autobahn-25.12.1-cp312-cp312-win_amd64.whl``
   * - Windows
     - CPython 3.13
     - x86_64
     - ``autobahn-25.12.1-cp313-cp313-win_amd64.whl``
   * - Windows
     - CPython 3.14
     - x86_64
     - ``autobahn-25.12.1-cp314-cp314-win_amd64.whl``
   * - Windows
     - PyPy 3.11
     - x86_64
     - ``autobahn-25.12.1-pp311-pypy311_pp73-win_amd64.whl``

Source distribution: ``autobahn-25.12.1.tar.gz``

Artifact Verification
^^^^^^^^^^^^^^^^^^^^^

All release artifacts include SHA256 checksums for integrity verification.

* `CHECKSUMS.sha256 <https://github.com/crossbario/autobahn-python/releases/download/master-202512092131/CHECKSUMS.sha256>`__

To verify a downloaded artifact:

.. code-block:: bash

   # Download checksum file
   curl -LO https://github.com/crossbario/autobahn-python/releases/download/master-202512092131/CHECKSUMS.sha256

   # Verify a wheel (example)
   openssl sha256 autobahn-25.12.1-cp311-cp311-manylinux_2_28_x86_64.whl
   # Compare output with corresponding line in CHECKSUMS.sha256

Release Links
^^^^^^^^^^^^^

* `GitHub Release <https://github.com/crossbario/autobahn-python/releases/tag/v25.12.1>`__
* `PyPI Package <https://pypi.org/project/autobahn/25.12.1/>`__
* `Documentation <https://autobahn.readthedocs.io/en/v25.12.1/>`__

**Detailed Changes:** See :ref:`changelog` (25.12.1 section)


25.10.2
-------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v25.10.2>`__
* `PyPI Package <https://pypi.org/project/zlmdb/25.10.2/>`__
* `Documentation <https://zlmdb.readthedocs.io/en/v25.10.2/>`__

25.10.1
-------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v25.10.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/25.10.1/>`__
* `Documentation <https://zlmdb.readthedocs.io/en/v25.10.1/>`__

23.1.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v23.1.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/23.1.1/>`__
* `Documentation <https://zlmdb.readthedocs.io/en/v23.1.1/>`__

22.6.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.6.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.6.1/>`__

22.5.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.5.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.5.1/>`__

22.4.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.4.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.4.1/>`__

22.3.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.3.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.3.1/>`__

22.2.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.2.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.2.1/>`__

22.1.2
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.1.2>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.1.2/>`__

22.1.1
------

* `GitHub Release <https://github.com/crossbario/zlmdb/releases/tag/v22.1.1>`__
* `PyPI Package <https://pypi.org/project/zlmdb/22.1.1/>`__

--------------

.. _release-workflow:

Release Workflow (for Maintainers)
----------------------------------

This section documents the release process for maintainers.

Prerequisites
^^^^^^^^^^^^^

Before releasing, ensure you have:

* Push access to the repository
* PyPI credentials configured (or trusted publishing via GitHub Actions)
* ``just`` and ``uv`` installed

Step 1: Draft the Release
^^^^^^^^^^^^^^^^^^^^^^^^^

Generate changelog and release note templates:

.. code-block:: bash

   # Generate changelog entry from git history (for catching up)
   just prepare-changelog <version>

   # Generate release draft with templates for both files
   just draft-release <version>

This will:

* Add a changelog entry template to ``docs/changelog.rst``
* Add a release entry template to ``docs/releases.rst``
* Update the version in ``pyproject.toml``

Step 2: Edit Changelog
^^^^^^^^^^^^^^^^^^^^^^

Edit ``docs/changelog.rst`` and fill in the changelog details:

* **New**: New features and capabilities
* **Fix**: Bug fixes
* **Other**: Breaking changes, deprecations, other notes

Step 3: Validate the Release
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure everything is in place:

.. code-block:: bash

   just prepare-release <version>

This validates:

* Changelog entry exists for this version
* Release entry exists for this version
* Version in ``pyproject.toml`` matches
* All tests pass
* Documentation builds successfully

Step 4: Disable Git Hooks (if needed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git config core.hooksPath /dev/null
   git config core.hooksPath

Step 5: Commit and Tag
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git add docs/changelog.rst docs/releases.rst pyproject.toml
   git commit -m "Release <version>"
   git tag v<version>
   git push && git push --tags

Step 6: Enable Git Hooks (if previously disabled)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git config core.hooksPath .ai/.githooks
   git config core.hooksPath

Step 7: Automated Release
^^^^^^^^^^^^^^^^^^^^^^^^^

After pushing the tag:

1. GitHub Actions builds and tests the release
2. Wheels and source distributions are uploaded to GitHub Releases
3. PyPI publishing is triggered via trusted publishing (OIDC)
4. Read the Docs builds documentation for the tagged version

Manual PyPI Upload (if needed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If automated publishing fails:

.. code-block:: bash

   just download-github-release v<version>
   just publish-pypi "" v<version>
