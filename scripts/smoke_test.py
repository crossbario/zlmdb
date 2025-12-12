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

ALL TESTS ARE REQUIRED. Both wheel installs and sdist installs MUST
provide identical functionality including the flatc binary and
reflection.bfbs file.
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

    This is a REQUIRED test - both wheel and sdist installs MUST include flatc.
    """
    print("Test 5: Checking flatc binary...")
    try:
        from zlmdb._flatc import get_flatc_path
        import subprocess

        flatc_path = get_flatc_path()
        print(f"  flatc path: {flatc_path}")

        if not os.path.isfile(flatc_path):
            print("  ❌ FAIL: flatc binary not found")
            print("         This is a packaging bug - flatc MUST be included")
            return False

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
    except ImportError as e:
        print(f"  ❌ FAIL: zlmdb._flatc module not available: {e}")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: Unexpected error: {e}")
        return False


def test_reflection_files():
    """Test 6: Verify reflection files are present.

    This is a REQUIRED test - both wheel and sdist installs MUST include reflection files.
    """
    print("Test 6: Checking FlatBuffers reflection files...")
    try:
        import zlmdb.flatbuffers

        fbs_dir = Path(zlmdb.flatbuffers.__file__).parent
        fbs_file = fbs_dir / "reflection.fbs"
        bfbs_file = fbs_dir / "reflection.bfbs"

        # reflection.fbs MUST be present
        if not fbs_file.exists():
            print(f"  ❌ FAIL: reflection.fbs not found at {fbs_file}")
            return False
        print(f"  reflection.fbs: {fbs_file.stat().st_size} bytes")

        # reflection.bfbs MUST be present (generated by flatc during build)
        if not bfbs_file.exists():
            print(f"  ❌ FAIL: reflection.bfbs not found at {bfbs_file}")
            print("         This is a packaging bug - reflection.bfbs MUST be included")
            return False

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

    # All tests are REQUIRED - sdist MUST provide same functionality as wheels
    tests = [
        test_import_zlmdb,
        test_import_lmdb,
        test_lmdb_operations,
        test_import_flatbuffers,
        test_flatc_binary,
        test_reflection_files,
    ]

    failures = 0
    passed = 0

    for test in tests:
        result = test()
        if result is True:
            passed += 1
        else:
            failures += 1
        print()

    total = len(tests)
    print("=" * 72)
    if failures == 0:
        print(f"✅ ALL SMOKE TESTS PASSED ({passed}/{total})")
        print("=" * 72)
        return 0
    else:
        print(f"❌ SMOKE TESTS FAILED ({passed} passed, {failures} failed)")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
