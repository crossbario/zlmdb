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
4. Import zlmdb.flatbuffers and check version
5. Verify flatc binary is available and executable
6. Verify reflection files are present
"""

import os
import sys
import tempfile
from pathlib import Path


def test_import_zlmdb():
    """Test 1: Import zlmdb and check version."""
    print("Test 1: Importing zlmdb and checking version...")
    try:
        import zlmdb
        print(f"  zlmdb version: {zlmdb.__version__}")
        print("  ✓ PASS")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Could not import zlmdb: {e}")
        return False


def test_import_lmdb():
    """Test 2: Import zlmdb.lmdb (CFFI extension) and check version."""
    print("Test 2: Importing zlmdb.lmdb (CFFI extension)...")
    try:
        import zlmdb.lmdb as lmdb
        print(f"  LMDB version: {lmdb.version()}")
        print("  ✓ PASS")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Could not import zlmdb.lmdb: {e}")
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
        print("  ✓ PASS")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: LMDB operations failed: {e}")
        return False


def test_import_flatbuffers():
    """Test 4: Import zlmdb.flatbuffers and check version."""
    print("Test 4: Importing zlmdb.flatbuffers...")
    try:
        import zlmdb.flatbuffers
        print(f"  FlatBuffers version: {zlmdb.flatbuffers.__version__}")
        print("  ✓ PASS")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Could not import zlmdb.flatbuffers: {e}")
        return False


def test_flatc_binary():
    """Test 5: Check flatc binary is available and works.

    Note: flatc may not be available in sdist installs if cmake/grpc was missing.
    This test returns None (skip) if flatc is expected to be missing.
    """
    print("Test 5: Checking flatc binary...")
    try:
        from zlmdb._flatc import get_flatc_path
        import subprocess

        flatc_path = get_flatc_path()
        print(f"  flatc path: {flatc_path}")

        if not os.path.isfile(flatc_path):
            print("  ⚠ SKIP: flatc binary not found (expected for sdist without cmake)")
            return None  # Skip, not fail

        if not os.access(flatc_path, os.X_OK):
            print("  ❌ FAIL: flatc exists but not executable")
            return False

        # Try running flatc --version
        result = subprocess.run(
            [flatc_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        version_output = result.stdout.strip() or result.stderr.strip()
        print(f"  flatc version: {version_output}")

        if "flatc" in version_output.lower():
            print("  ✓ PASS")
            return True
        else:
            print("  ❌ FAIL: flatc --version returned unexpected output")
            return False
    except ImportError:
        print("  ⚠ SKIP: zlmdb._flatc module not available")
        return None  # Skip, not fail
    except Exception as e:
        # Check if this is the expected "not found" error from get_flatc_path
        if "not found" in str(e).lower():
            print(f"  ⚠ SKIP: flatc not available ({e})")
            return None  # Skip, not fail
        print(f"  ❌ FAIL: Unexpected error: {e}")
        return False


def test_reflection_files():
    """Test 6: Verify reflection files are present.

    Note: reflection.bfbs may not be available in sdist installs if flatc wasn't built.
    This test returns None (skip) if reflection files are expected to be missing.
    """
    print("Test 6: Checking FlatBuffers reflection files...")
    try:
        import zlmdb.flatbuffers

        fbs_dir = Path(zlmdb.flatbuffers.__file__).parent
        fbs_file = fbs_dir / "reflection.fbs"
        bfbs_file = fbs_dir / "reflection.bfbs"

        # reflection.fbs should always be present (it's in the source)
        if not fbs_file.exists():
            print(f"  ❌ FAIL: reflection.fbs not found at {fbs_file}")
            return False
        print(f"  reflection.fbs: {fbs_file.stat().st_size} bytes")

        # reflection.bfbs may not be present if flatc wasn't built
        if not bfbs_file.exists():
            print(f"  ⚠ SKIP: reflection.bfbs not found (expected for sdist without flatc)")
            return None  # Skip, not fail

        print(f"  reflection.bfbs: {bfbs_file.stat().st_size} bytes")
        print("  ✓ PASS")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Reflection files check failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 72)
    print("  SMOKE TESTS - Verifying zlmdb installation")
    print("=" * 72)
    print()
    print(f"Python: {sys.version}")
    print()

    # Core tests (must pass)
    core_tests = [
        test_import_zlmdb,
        test_import_lmdb,
        test_lmdb_operations,
        test_import_flatbuffers,
    ]

    # Optional tests (may be skipped for sdist installs without cmake)
    optional_tests = [
        test_flatc_binary,
        test_reflection_files,
    ]

    failures = 0
    skipped = 0
    passed = 0

    # Run core tests (failures are errors)
    for test in core_tests:
        result = test()
        if result is True:
            passed += 1
        elif result is False:
            failures += 1
        else:  # None = skipped (shouldn't happen for core tests)
            skipped += 1
        print()

    # Run optional tests (None = skip is OK)
    for test in optional_tests:
        result = test()
        if result is True:
            passed += 1
        elif result is False:
            failures += 1
        else:  # None = skipped
            skipped += 1
        print()

    total = len(core_tests) + len(optional_tests)
    print("=" * 72)
    if failures == 0:
        if skipped > 0:
            print(f"✅ SMOKE TESTS PASSED ({passed} passed, {skipped} skipped, {failures} failed)")
            print("   Note: Some optional features (flatc) were not available.")
            print("   This is expected for source installs without cmake.")
        else:
            print(f"✅ ALL SMOKE TESTS PASSED ({passed}/{total})")
        print("=" * 72)
        return 0
    else:
        print(f"❌ SMOKE TESTS FAILED ({passed} passed, {skipped} skipped, {failures} failed)")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
