#!/usr/bin/env python3
# Copyright (c) typedef int GmbH, Germany, 2025. All rights reserved.
#
# Test script for flatbuffers reflection imports.
# Verifies that the vendored reflection module works correctly.
# See: https://github.com/crossbario/zlmdb/issues/102
#
# This test is critical because:
# - cfxdb, wamp-xbr, and crossbar use Schema.GetRootAs() to load .bfbs files
# - The flatc compiler generates absolute imports by default
# - When vendored inside zlmdb, these must be relative imports

"""
Test flatbuffers reflection imports.

Tests:
1. Import Schema class from reflection module
2. Import all 10 reflection classes (what cfxdb/wamp-xbr do)
3. Load and parse reflection.bfbs using Schema.GetRootAs()
"""

import sys
from pathlib import Path


def test_schema_import():
    """Test 1: Import the Schema class from reflection module."""
    print("Test 1: Verifying 'from zlmdb.flatbuffers.reflection.Schema import Schema' works...")
    try:
        from zlmdb.flatbuffers.reflection.Schema import Schema
        print(f"  Schema class: {Schema}")
        print("  ✓ PASS: Schema import works")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Schema import failed: {e}")
        return False


def test_all_reflection_imports():
    """Test 2: Import all reflection classes (what cfxdb/wamp-xbr do)."""
    print("Test 2: Verifying all reflection class imports work...")
    try:
        from zlmdb.flatbuffers.reflection.Schema import Schema
        from zlmdb.flatbuffers.reflection.Object import Object
        from zlmdb.flatbuffers.reflection.Field import Field
        from zlmdb.flatbuffers.reflection.Enum import Enum
        from zlmdb.flatbuffers.reflection.EnumVal import EnumVal
        from zlmdb.flatbuffers.reflection.Type import Type
        from zlmdb.flatbuffers.reflection.Service import Service
        from zlmdb.flatbuffers.reflection.RPCCall import RPCCall
        from zlmdb.flatbuffers.reflection.KeyValue import KeyValue
        from zlmdb.flatbuffers.reflection.SchemaFile import SchemaFile

        print("  All 10 reflection classes imported successfully:")
        print(f"    - Schema: {Schema}")
        print(f"    - Object: {Object}")
        print(f"    - Field: {Field}")
        print(f"    - Enum: {Enum}")
        print(f"    - EnumVal: {EnumVal}")
        print(f"    - Type: {Type}")
        print(f"    - Service: {Service}")
        print(f"    - RPCCall: {RPCCall}")
        print(f"    - KeyValue: {KeyValue}")
        print(f"    - SchemaFile: {SchemaFile}")
        print("  ✓ PASS: All reflection classes import")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Reflection class imports failed: {e}")
        return False


def test_schema_parse():
    """Test 3: Load and parse reflection.bfbs (the real-world use case)."""
    print("Test 3: Verifying Schema.GetRootAs() can parse reflection.bfbs...")
    try:
        import zlmdb.flatbuffers
        from zlmdb.flatbuffers.reflection.Schema import Schema

        # Find reflection.bfbs
        fbs_dir = Path(zlmdb.flatbuffers.__file__).parent
        bfbs_path = fbs_dir / "reflection.bfbs"

        if not bfbs_path.exists():
            print(f"  ❌ FAIL: reflection.bfbs not found at {bfbs_path}")
            return False

        # Load and parse
        with open(bfbs_path, "rb") as f:
            buf = f.read()

        schema = Schema.GetRootAs(buf, 0)
        objects_count = schema.ObjectsLength()
        enums_count = schema.EnumsLength()

        print(f"  Loaded reflection.bfbs ({len(buf)} bytes)")
        print(f"  Schema has {objects_count} objects")
        print(f"  Schema has {enums_count} enums")

        # Sanity check: reflection.bfbs should have some objects/enums
        if objects_count == 0 and enums_count == 0:
            print("  ❌ FAIL: Schema appears empty (0 objects, 0 enums)")
            return False

        print("  ✓ PASS: Schema.GetRootAs() works")
        return True
    except Exception as e:
        print(f"  ❌ FAIL: Schema.GetRootAs() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all reflection tests."""
    print("=" * 72)
    print("  REFLECTION IMPORT TESTS - Verifying vendored reflection module")
    print("=" * 72)
    print()
    print(f"Python: {sys.version}")
    print()

    tests = [
        ("Test 1", test_schema_import),
        ("Test 2", test_all_reflection_imports),
        ("Test 3", test_schema_parse),
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
        print(f"ALL REFLECTION TESTS PASSED ({passed}/{total})")
        print("=" * 72)
        return 0
    else:
        print(f"REFLECTION TESTS FAILED ({passed} passed, {failures} failed)")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
