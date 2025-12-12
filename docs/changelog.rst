Changelog
=========

This document contains a reverse-chronological list of changes to zLMDB.

.. note::

    For detailed release information including artifacts,
    see :doc:`releases`.

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
