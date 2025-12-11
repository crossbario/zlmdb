###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) typedef int GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################
"""ZLMDB - Object-relational zero-copy in-memory database layer for LMDB."""

import sys
import uuid

from typing import Dict  # noqa

# =============================================================================
# Vendored library aliasing
# =============================================================================
# Register vendored flatbuffers runtime in sys.modules so that code doing
# `import flatbuffers` resolves to our vendored copy. This ensures:
# 1. No conflicts with separately installed flatbuffers packages
# 2. Generated code in zlmdb.flatbuffers.reflection can import flatbuffers
# 3. Consistent behavior across all zlmdb modules
#
# Note: This aliasing only affects imports that happen AFTER zlmdb is imported.
# =============================================================================
from zlmdb import _flatbuffers_vendor
sys.modules.setdefault('flatbuffers', _flatbuffers_vendor)
# Also register submodules that might be imported directly
sys.modules.setdefault('flatbuffers.compat', _flatbuffers_vendor.compat)
sys.modules.setdefault('flatbuffers.builder', _flatbuffers_vendor.builder)
sys.modules.setdefault('flatbuffers.table', _flatbuffers_vendor.table)
sys.modules.setdefault('flatbuffers.util', _flatbuffers_vendor.util)
sys.modules.setdefault('flatbuffers.number_types', _flatbuffers_vendor.number_types)
sys.modules.setdefault('flatbuffers.packer', _flatbuffers_vendor.packer)
sys.modules.setdefault('flatbuffers.encode', _flatbuffers_vendor.encode)

# Re-export vendored flatbuffers for explicit use by downstream packages
# Users can do: `from zlmdb import flatbuffers` or `import zlmdb.flatbuffers`
flatbuffers = _flatbuffers_vendor  # noqa: F401
sys.modules.setdefault('zlmdb.flatbuffers', _flatbuffers_vendor)

# Re-export vendored LMDB for backwards compatibility
# Users can do: `from zlmdb import lmdb` or `import zlmdb.lmdb as lmdb`
from zlmdb import _lmdb_vendor as lmdb  # noqa: F401
# Also register zlmdb.lmdb in sys.modules for backward compatibility
# This allows `import zlmdb.lmdb as lmdb` to work
sys.modules.setdefault('zlmdb.lmdb', _lmdb_vendor)


def setup_flatbuffers_import():
    """
    Register vendored flatbuffers in sys.modules so `import flatbuffers` works.

    This function should be called by downstream packages (e.g. cfxdb) that have
    generated flatbuffers code which does `import flatbuffers`. By calling this
    function early in their initialization, they ensure that:

    1. `import flatbuffers` resolves to zlmdb's vendored copy
    2. No conflicts with separately installed flatbuffers packages
    3. Consistent behavior across all modules

    Example usage in downstream package __init__.py::

        import zlmdb
        zlmdb.setup_flatbuffers_import()

        # Now generated code can do `import flatbuffers`
        from .gen import MyTable
    """
    sys.modules.setdefault('flatbuffers', _flatbuffers_vendor)
    sys.modules.setdefault('flatbuffers.compat', _flatbuffers_vendor.compat)
    sys.modules.setdefault('flatbuffers.builder', _flatbuffers_vendor.builder)
    sys.modules.setdefault('flatbuffers.table', _flatbuffers_vendor.table)
    sys.modules.setdefault('flatbuffers.util', _flatbuffers_vendor.util)
    sys.modules.setdefault('flatbuffers.number_types', _flatbuffers_vendor.number_types)
    sys.modules.setdefault('flatbuffers.packer', _flatbuffers_vendor.packer)
    sys.modules.setdefault('flatbuffers.encode', _flatbuffers_vendor.encode)


def check_autobahn_flatbuffers_version_in_sync() -> str:
    """
    Check that zlmdb and autobahn have the same vendored flatbuffers version.

    This is important for applications like Crossbar.io that use both zlmdb
    (for data-at-rest) and autobahn (for data-in-transit) with FlatBuffers
    serialization. When sending a FlatBuffers database record as a WAMP
    application payload, both libraries must use compatible FlatBuffers
    runtimes to avoid subtle serialization issues.

    :returns: The flatbuffers git version (e.g. "v25.9.23-2-g95053e6a") if both are in sync.
    :raises RuntimeError: If the versions differ.
    :raises ImportError: If autobahn is not installed.

    Example::

        import zlmdb
        version = zlmdb.check_autobahn_flatbuffers_version_in_sync()
        print(f"FlatBuffers version: {version}")
    """
    import autobahn.flatbuffers

    zlmdb_version = _flatbuffers_vendor.version()
    autobahn_version = autobahn.flatbuffers.version()

    if zlmdb_version != autobahn_version:
        raise RuntimeError(
            f"FlatBuffers version mismatch: zlmdb has {zlmdb_version!r}, "
            f"autobahn has {autobahn_version!r}. Both should be the same for "
            f"reliable data-at-rest/data-in-transit interoperability."
        )

    return zlmdb_version


from ._version import __version__

from ._errors import NullValueConstraint

from ._pmap import (
    PersistentMap,
    MapSlotUuidUuid,
    MapUuidString,
    MapUuidOid,
    MapUuidUuid,
    MapUuidJson,
    MapUuidCbor,
    MapUuidPickle,
    MapUuidFlatBuffers,
    MapUuidTimestampFlatBuffers,
    MapUuidBytes20Uint8FlatBuffers,
    MapUuidBytes20Uint8UuidFlatBuffers,
    MapUuidBytes20Bytes20Uint8UuidFlatBuffers,
    MapUuidTimestampCbor,
    MapTimestampFlatBuffers,
    MapTimestampStringFlatBuffers,
    MapTimestampUuidFlatBuffers,
    MapTimestampUuidStringFlatBuffers,
    MapUuidTimestampUuidFlatBuffers,
    MapUint64TimestampUuid,
    MapTimestampUuidCbor,
    MapUuidTimestampUuid,
    MapUuidStringUuid,
    MapUuidUuidStringUuid,
    MapUuidUuidUuidStringUuid,
    MapUuidStringOid,
    MapUuidUuidCbor,
    MapUuidUuidSet,
    MapUuidUuidUuid,
    MapUuidUuidUuidUuid,
    MapUuidUuidUuidUuidUuid,
    MapUuidTimestampBytes32,
    MapUuidUuidFlatBuffers,
    MapUuidUuidStringFlatBuffers,
    MapUuidStringFlatBuffers,
    MapStringString,
    MapStringOid,
    MapStringOidOid,
    MapStringUuid,
    MapStringStringUuid,
    MapStringStringStringUuid,
    MapStringJson,
    MapStringCbor,
    MapStringPickle,
    MapStringFlatBuffers,
    MapStringTimestampCbor,
    MapTimestampStringCbor,
    MapOidString,
    MapOidOid,
    MapOidUuid,
    MapOidJson,
    MapOidCbor,
    MapOidPickle,
    MapOidFlatBuffers,
    MapOidOidFlatBuffers,
    MapOid3FlatBuffers,
    MapOidOidSet,
    MapOidStringOid,
    MapOidOidOid,
    MapOidTimestampOid,
    MapOidTimestampFlatBuffers,
    MapOidTimestampStringOid,
    MapUint16UuidTimestampFlatBuffers,
    MapBytes32Uuid,
    MapBytes32Timestamp,
    MapBytes32Bytes32,
    MapBytes32FlatBuffers,
    MapBytes32UuidFlatBuffers,
    MapUuidBytes32FlatBuffers,
    MapBytes32Bytes32FlatBuffers,
    MapBytes32StringFlatBuffers,
    MapTimestampBytes32FlatBuffers,
    MapBytes20Uuid,
    MapBytes20Bytes16,
    MapBytes20Bytes20,
    MapBytes20Bytes20Timestamp,
    MapBytes20TimestampBytes20,
    MapBytes20TimestampUuid,
    MapBytes16FlatBuffers,
    MapBytes16TimestampUuid,
    MapBytes16TimestampUuidFlatBuffers,
    MapBytes20FlatBuffers,
    MapBytes20Bytes20FlatBuffers,
    MapBytes20StringFlatBuffers,
)

from ._transaction import Transaction, TransactionStats
from ._database import Database
from ._schema import Schema

__all__ = (
    "__version__",
    "flatbuffers",  # Re-exported vendored flatbuffers (zlmdb._flatbuffers_vendor)
    "setup_flatbuffers_import",  # Helper for downstream packages
    "check_autobahn_flatbuffers_version_in_sync",  # Version sync check with autobahn
    "lmdb",  # Re-exported vendored LMDB (zlmdb._lmdb_vendor)
    "Schema",
    "Database",
    "Transaction",
    "TransactionStats",
    "MapSlotUuidUuid",
    "table",
    #
    # Errors
    #
    "NullValueConstraint",
    #
    # UUID pmaps
    #
    # UUID (uint128) based pmap types for object containers
    "MapUuidString",
    "MapUuidOid",
    "MapUuidJson",
    "MapUuidCbor",
    "MapUuidPickle",
    "MapUuidFlatBuffers",
    # UUID/Timestamp-combined pmap types for flatbuffers values
    "MapUuidTimestampFlatBuffers",
    "MapTimestampUuidFlatBuffers",
    "MapTimestampFlatBuffers",
    "MapTimestampStringFlatBuffers",
    "MapTimestampUuidStringFlatBuffers",
    "MapUuidTimestampUuidFlatBuffers",
    "MapUuidBytes20Uint8FlatBuffers",
    "MapUuidBytes20Uint8UuidFlatBuffers",
    "MapUuidBytes20Bytes20Uint8UuidFlatBuffers",
    "MapUint16UuidTimestampFlatBuffers",
    # UUID (uint128) based pmap types for indexes
    "MapUuidUuid",
    "MapUuidStringUuid",
    "MapUuidUuidStringUuid",
    "MapUuidUuidUuidStringUuid",
    "MapUint64TimestampUuid",
    # more UUID (uint128) based pmap types for indexes
    "MapUuidUuidSet",
    "MapUuidStringOid",
    # UUID-UUID based pmap types
    "MapUuidUuidFlatBuffers",
    "MapUuidStringFlatBuffers",
    "MapUuidUuidCbor",
    "MapUuidUuidUuid",
    "MapUuidUuidUuidUuid",
    "MapUuidUuidUuidUuidUuid",
    "MapUuidTimestampUuid",
    "MapUuidTimestampBytes32",
    "MapUuidTimestampCbor",
    "MapTimestampUuidCbor",
    #
    # String pmaps
    #
    # String (utf8) based pmap types for object containers
    "MapStringUuid",
    "MapStringStringUuid",
    "MapStringStringStringUuid",
    "MapStringOid",
    "MapStringOidOid",
    "MapStringJson",
    "MapStringCbor",
    "MapStringPickle",
    "MapStringFlatBuffers",
    "MapStringTimestampCbor",
    "MapTimestampStringCbor",
    # String (utf8) based pmap types for indexes
    "MapStringString",
    #
    # OID pmaps
    #
    # OID (uint64) based pmap types for object containers
    "MapOidString",
    "MapOidUuid",
    "MapOidJson",
    "MapOidCbor",
    "MapOidPickle",
    "MapOidFlatBuffers",
    "MapOidOidFlatBuffers",
    "MapOidTimestampFlatBuffers",
    "MapOid3FlatBuffers",
    # OID (uint64) based pmap types for indexes
    "MapOidOid",
    "MapOidOidSet",
    "MapOidStringOid",
    "MapOidOidOid",
    "MapOidTimestampOid",
    "MapOidTimestampStringOid",
    #
    # Bytes32 pmaps
    #
    "MapBytes32Uuid",
    "MapBytes32Timestamp",
    "MapBytes32Bytes32",
    "MapBytes32FlatBuffers",
    "MapBytes32UuidFlatBuffers",
    "MapUuidBytes32FlatBuffers",
    "MapBytes32Bytes32FlatBuffers",
    "MapBytes32StringFlatBuffers",
    "MapTimestampBytes32FlatBuffers",
    "MapUuidUuidStringFlatBuffers",
    #
    # Bytes20 pmaps
    #
    "MapBytes20Uuid",
    "MapBytes20Bytes16",
    "MapBytes20Bytes20",
    "MapBytes20Bytes20Timestamp",
    "MapBytes20TimestampBytes20",
    "MapBytes20TimestampUuid",
    "MapBytes20FlatBuffers",
    "MapBytes20Bytes20FlatBuffers",
    "MapBytes20StringFlatBuffers",
    #
    # Bytes16 pmaps
    #
    "MapBytes16FlatBuffers",
    "MapBytes16TimestampUuid",
    "MapBytes16TimestampUuidFlatBuffers",
)

TABLES_BY_UUID: Dict[uuid.UUID, PersistentMap] = {}
"""
Map of table UUIDs to persistent maps stored in slots in a KV store.
"""


def table(oid, marshal=None, parse=None, build=None, cast=None, compress=None):
    if type(oid) == str:
        oid = uuid.UUID(oid)

    assert isinstance(oid, uuid.UUID)
    assert marshal is None or callable(marshal)
    assert parse is None or callable(parse)
    assert build is None or callable(build)
    assert cast is None or callable(cast)
    assert compress is None or compress in [
        PersistentMap.COMPRESS_ZLIB,
        PersistentMap.COMPRESS_SNAPPY,
    ]

    def decorate(o):
        if oid in TABLES_BY_UUID:
            assert TABLES_BY_UUID[oid]._zlmdb_oid == oid, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_oid, oid
            )
            assert TABLES_BY_UUID[oid]._zlmdb_marshal == marshal, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_marshal, marshal
            )
            assert TABLES_BY_UUID[oid]._zlmdb_parse == parse, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_parse, parse
            )
            assert TABLES_BY_UUID[oid]._zlmdb_build == build, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_build, build
            )
            assert TABLES_BY_UUID[oid]._zlmdb_cast == cast, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_cast, cast
            )
            assert TABLES_BY_UUID[oid]._zlmdb_compress == compress, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_compress, compress
            )
            return
        assert oid not in TABLES_BY_UUID, (
            "oid {} already in map (pointing to {})".format(oid, TABLES_BY_UUID[oid])
        )

        # slot UUID that is mapped to a slot index later when attaching to db
        o._zlmdb_oid = oid

        # for CBOR/JSON
        o._zlmdb_marshal = marshal
        o._zlmdb_parse = parse

        # for Flatbuffers
        o._zlmdb_build = build
        o._zlmdb_cast = cast

        # for value compression
        o._zlmdb_compress = compress

        TABLES_BY_UUID[oid] = o
        return o

    return decorate
