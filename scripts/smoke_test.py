#!/usr/bin/env python3
# Copyright (c) typedef int GmbH, Germany, 2025. All rights reserved.
#
# Smoke tests for zlmdb package verification.
# Used by CI to verify wheels and sdists actually work after building.

"""
Smoke tests for zlmdb package.

This script verifies that a zlmdb installation is functional by testing:
1. Import zlmdb and check version
2. Import zlmdb.lmdb (CFFI extension) and check version
3. Basic LMDB operations (open/put/get/close)
4. Import zlmdb.flatbuffers and check version (shared test)
5. Verify flatc binary is available and executable (shared test)
6. Verify reflection files are present (shared test)

ALL TESTS ARE REQUIRED. Both wheel installs and sdist installs MUST
provide identical functionality including the flatc binary and
reflection.bfbs file.

Note: FlatBuffers/flatc tests use shared functions from smoke_test_flatc.py
      (source: wamp-cicd/scripts/flatc/smoke_test_flatc.py)
"""

import sys
import tempfile

# Import shared FlatBuffers test functions
from smoke_test_flatc import (
    test_import_flatbuffers,
    test_flatc_binary,
    test_reflection_files,
)

# Package name for shared tests
PACKAGE_NAME = "zlmdb"


def test_import_zlmdb():
    """Test 1: Import zlmdb and check version."""
    print("Test 1: Importing zlmdb and checking version...")
    try:
        import zlmdb
        print(f"  zlmdb version: {zlmdb.__version__}")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: Could not import zlmdb: {e}")
        return False


def test_import_lmdb():
    """Test 2: Import zlmdb.lmdb (CFFI extension) and check version."""
    print("Test 2: Importing zlmdb.lmdb (CFFI extension)...")
    try:
        import zlmdb.lmdb as lmdb
        print(f"  LMDB version: {lmdb.version()}")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: Could not import zlmdb.lmdb: {e}")
        return False


def test_lmdb_operations():
    """Test 3: Basic LMDB operations (open/put/get/close)."""
    print("Test 3: Basic LMDB operations (open/put/get/close)...")
    try:
        import zlmdb.lmdb as lmdb

        with tempfile.TemporaryDirectory() as tmpdir:
            env = lmdb.open(tmpdir, max_dbs=1)
            with env.begin(write=True) as txn:
                txn.put(b"key1", b"value1")
                txn.put(b"key2", b"value2")
            with env.begin() as txn:
                assert txn.get(b"key1") == b"value1", "key1 mismatch"
                assert txn.get(b"key2") == b"value2", "key2 mismatch"
                assert txn.get(b"key3") is None, "key3 should be None"
            env.close()
        print("  LMDB operations: open, put, get, close - all work!")
        print("  PASS")
        return True
    except Exception as e:
        print(f"  FAIL: LMDB operations failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 72)
    print("  SMOKE TESTS - Verifying zlmdb installation")
    print("=" * 72)
    print()
    print(f"Python: {sys.version}")
    print()

    # All tests are REQUIRED - sdist MUST provide same functionality as wheels
    # Tests 4-6 use shared functions from smoke_test_flatc.py
    tests = [
        ("Test 1", test_import_zlmdb),
        ("Test 2", test_import_lmdb),
        ("Test 3", test_lmdb_operations),
        ("Test 4", lambda: test_import_flatbuffers(PACKAGE_NAME)),
        ("Test 5", lambda: test_flatc_binary(PACKAGE_NAME)),
        ("Test 6", lambda: test_reflection_files(PACKAGE_NAME)),
    ]

    failures = 0
    passed = 0

    for name, test in tests:
        result = test()
        if result is True:
            passed += 1
        else:
            failures += 1
        print()

    total = len(tests)
    print("=" * 72)
    if failures == 0:
        print(f"ALL SMOKE TESTS PASSED ({passed}/{total})")
        print("=" * 72)
        return 0
    else:
        print(f"SMOKE TESTS FAILED ({passed} passed, {failures} failed)")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
