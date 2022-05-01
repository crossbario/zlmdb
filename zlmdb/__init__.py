###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
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

import uuid

from typing import Dict  # noqa

from ._version import __version__

from ._errors import NullValueConstraint

from ._pmap import PersistentMap, \
                   MapSlotUuidUuid, \
                   MapUuidString, \
                   MapUuidOid, \
                   MapUuidUuid, \
                   MapUuidJson, \
                   MapUuidCbor, \
                   MapUuidPickle, \
                   MapUuidFlatBuffers, \
                   MapUuidTimestampFlatBuffers, \
                   MapUuidBytes20Uint8FlatBuffers, \
                   MapUuidBytes20Uint8UuidFlatBuffers, \
                   MapUuidBytes20Bytes20Uint8UuidFlatBuffers, \
                   MapUuidTimestampCbor, \
                   MapTimestampFlatBuffers, \
                   MapTimestampStringFlatBuffers, \
                   MapTimestampUuidFlatBuffers, \
                   MapTimestampUuidStringFlatBuffers, \
                   MapUuidTimestampUuidFlatBuffers, \
                   MapUint64TimestampUuid, \
                   MapTimestampUuidCbor, \
                   MapUuidTimestampUuid, \
                   MapUuidStringUuid, \
                   MapUuidUuidStringUuid, \
                   MapUuidUuidUuidStringUuid, \
                   MapUuidStringOid, \
                   MapUuidUuidCbor, \
                   MapUuidUuidSet, \
                   MapUuidUuidUuid, \
                   MapUuidUuidUuidUuid, \
                   MapUuidUuidUuidUuidUuid, \
                   MapUuidTimestampBytes32, \
                   MapUuidUuidFlatBuffers, \
                   MapUuidUuidStringFlatBuffers, \
                   MapUuidStringFlatBuffers, \
                   MapStringString, \
                   MapStringOid, \
                   MapStringOidOid, \
                   MapStringUuid, \
                   MapStringStringUuid, \
                   MapStringStringStringUuid, \
                   MapStringJson, \
                   MapStringCbor, \
                   MapStringPickle, \
                   MapStringFlatBuffers, \
                   MapStringTimestampCbor, \
                   MapTimestampStringCbor, \
                   MapOidString, \
                   MapOidOid, \
                   MapOidUuid, \
                   MapOidJson, \
                   MapOidCbor, \
                   MapOidPickle, \
                   MapOidFlatBuffers, \
                   MapOidOidFlatBuffers, \
                   MapOid3FlatBuffers, \
                   MapOidOidSet, \
                   MapOidStringOid, \
                   MapOidOidOid, \
                   MapOidTimestampOid, \
                   MapOidTimestampFlatBuffers, \
                   MapOidTimestampStringOid, \
                   MapUint16UuidTimestampFlatBuffers, \
                   MapBytes32Uuid, \
                   MapBytes32Timestamp, \
                   MapBytes32Bytes32, \
                   MapBytes32FlatBuffers, \
                   MapBytes32UuidFlatBuffers, \
                   MapUuidBytes32FlatBuffers, \
                   MapBytes32Bytes32FlatBuffers, \
                   MapBytes32StringFlatBuffers, \
                   MapTimestampBytes32FlatBuffers, \
                   MapBytes20Uuid, \
                   MapBytes20Bytes16, \
                   MapBytes20Bytes20, \
                   MapBytes20Bytes20Timestamp, \
                   MapBytes20TimestampBytes20, \
                   MapBytes20TimestampUuid, \
                   MapBytes16FlatBuffers, \
                   MapBytes16TimestampUuid, \
                   MapBytes16TimestampUuidFlatBuffers, \
                   MapBytes20FlatBuffers, \
                   MapBytes20Bytes20FlatBuffers, \
                   MapBytes20StringFlatBuffers

from ._transaction import Transaction, TransactionStats, walltime
from ._database import Database
from ._schema import Schema

__all__ = (
    '__version__',
    'Schema',
    'Database',
    'Transaction',
    'TransactionStats',
    'walltime',
    'MapSlotUuidUuid',
    'table',

    #
    # Errors
    #
    'NullValueConstraint',

    #
    # UUID pmaps
    #

    # UUID (uint128) based pmap types for object containers
    'MapUuidString',
    'MapUuidOid',
    'MapUuidJson',
    'MapUuidCbor',
    'MapUuidPickle',
    'MapUuidFlatBuffers',

    # UUID/Timestamp-combined pmap types for flatbuffers values
    'MapUuidTimestampFlatBuffers',
    'MapTimestampUuidFlatBuffers',
    'MapTimestampFlatBuffers',
    'MapTimestampStringFlatBuffers',
    'MapTimestampUuidStringFlatBuffers',
    'MapUuidTimestampUuidFlatBuffers',
    'MapUuidBytes20Uint8FlatBuffers',
    'MapUuidBytes20Uint8UuidFlatBuffers',
    'MapUuidBytes20Bytes20Uint8UuidFlatBuffers',
    'MapUint16UuidTimestampFlatBuffers',

    # UUID (uint128) based pmap types for indexes
    'MapUuidUuid',
    'MapUuidStringUuid',
    'MapUuidUuidStringUuid',
    'MapUuidUuidUuidStringUuid',
    'MapUint64TimestampUuid',

    # more UUID (uint128) based pmap types for indexes
    'MapUuidUuidSet',
    'MapUuidStringOid',

    # UUID-UUID based pmap types
    'MapUuidUuidFlatBuffers',
    'MapUuidStringFlatBuffers',
    'MapUuidUuidCbor',
    'MapUuidUuidUuid',
    'MapUuidUuidUuidUuid',
    'MapUuidUuidUuidUuidUuid',
    'MapUuidTimestampUuid',
    'MapUuidTimestampBytes32',
    'MapUuidTimestampCbor',
    'MapTimestampUuidCbor',

    #
    # String pmaps
    #

    # String (utf8) based pmap types for object containers
    'MapStringUuid',
    'MapStringStringUuid',
    'MapStringStringStringUuid',
    'MapStringOid',
    'MapStringOidOid',
    'MapStringJson',
    'MapStringCbor',
    'MapStringPickle',
    'MapStringFlatBuffers',
    'MapStringTimestampCbor',
    'MapTimestampStringCbor',

    # String (utf8) based pmap types for indexes
    'MapStringString',

    #
    # OID pmaps
    #

    # OID (uint64) based pmap types for object containers
    'MapOidString',
    'MapOidUuid',
    'MapOidJson',
    'MapOidCbor',
    'MapOidPickle',
    'MapOidFlatBuffers',
    'MapOidOidFlatBuffers',
    'MapOidTimestampFlatBuffers',
    'MapOid3FlatBuffers',

    # OID (uint64) based pmap types for indexes
    'MapOidOid',
    'MapOidOidSet',
    'MapOidStringOid',
    'MapOidOidOid',
    'MapOidTimestampOid',
    'MapOidTimestampStringOid',

    #
    # Bytes32 pmaps
    #
    'MapBytes32Uuid',
    'MapBytes32Timestamp',
    'MapBytes32Bytes32',
    'MapBytes32FlatBuffers',
    'MapBytes32UuidFlatBuffers',
    'MapUuidBytes32FlatBuffers',
    'MapBytes32Bytes32FlatBuffers',
    'MapBytes32StringFlatBuffers',
    'MapTimestampBytes32FlatBuffers',
    'MapUuidUuidStringFlatBuffers',

    #
    # Bytes20 pmaps
    #
    'MapBytes20Uuid',
    'MapBytes20Bytes16',
    'MapBytes20Bytes20',
    'MapBytes20Bytes20Timestamp',
    'MapBytes20TimestampBytes20',
    'MapBytes20TimestampUuid',
    'MapBytes20FlatBuffers',
    'MapBytes20Bytes20FlatBuffers',
    'MapBytes20StringFlatBuffers',

    #
    # Bytes16 pmaps
    #
    'MapBytes16FlatBuffers',
    'MapBytes16TimestampUuid',
    'MapBytes16TimestampUuidFlatBuffers',
)

TABLES_BY_UUID = {}  # type: Dict[uuid.UUID, object]
"""
Map of table UUIDs to persistant maps stored in slots in a KV store.
"""


def table(oid, marshal=None, parse=None, build=None, cast=None, compress=None):
    if type(oid) == str:
        oid = uuid.UUID(oid)

    assert isinstance(oid, uuid.UUID)
    assert marshal is None or callable(marshal)
    assert parse is None or callable(parse)
    assert build is None or callable(build)
    assert cast is None or callable(cast)
    assert compress is None or compress in [PersistentMap.COMPRESS_ZLIB, PersistentMap.COMPRESS_SNAPPY]

    def decorate(o):
        if oid in TABLES_BY_UUID:
            assert TABLES_BY_UUID[oid]._zlmdb_oid == oid, "{} != {}".format(TABLES_BY_UUID[oid]._zlmdb_oid, oid)
            assert TABLES_BY_UUID[oid]._zlmdb_marshal == marshal, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_marshal, marshal)
            assert TABLES_BY_UUID[oid]._zlmdb_parse == parse, "{} != {}".format(TABLES_BY_UUID[oid]._zlmdb_parse,
                                                                                parse)
            assert TABLES_BY_UUID[oid]._zlmdb_build == build, "{} != {}".format(TABLES_BY_UUID[oid]._zlmdb_build,
                                                                                build)
            assert TABLES_BY_UUID[oid]._zlmdb_cast == cast, "{} != {}".format(TABLES_BY_UUID[oid]._zlmdb_cast, cast)
            assert TABLES_BY_UUID[oid]._zlmdb_compress == compress, "{} != {}".format(
                TABLES_BY_UUID[oid]._zlmdb_compress, compress)
            return
        assert oid not in TABLES_BY_UUID, "oid {} already in map (pointing to {})".format(oid, TABLES_BY_UUID[oid])

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
