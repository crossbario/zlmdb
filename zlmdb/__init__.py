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

from __future__ import absolute_import

import uuid

import six

from typing import Dict  # noqa

from ._version import __version__

from ._pmap import PersistentMap, \
                   MapSlotUuidUuid, \
                   MapUuidString, \
                   MapUuidOid, \
                   MapUuidUuid, \
                   MapUuidJson, \
                   MapUuidCbor, \
                   MapUuidPickle, \
                   MapUuidFlatBuffers, \
                   MapUuidStringUuid, \
                   MapUuidUuidSet, \
                   MapStringString, \
                   MapStringOid, \
                   MapStringUuid, \
                   MapStringJson, \
                   MapStringCbor, \
                   MapStringPickle, \
                   MapStringFlatBuffers, \
                   MapOidString, \
                   MapOidOid, \
                   MapOidUuid, \
                   MapOidJson, \
                   MapOidCbor, \
                   MapOidPickle, \
                   MapOidFlatBuffers, \
                   MapOidOidSet, \
                   MapOidStringOid, \
                   MapOidOidOid, \
                   MapOidTimestampOid, \
                   MapOidTimestampStringOid

from ._transaction import Transaction, TransactionStats, walltime
from ._database import Database
from ._schema import Schema
from ._types import perf_counter_ns, time_ns

__all__ = (
    '__version__',
    'perf_counter_ns',
    'time_ns',
    'Schema',
    'Database',
    'Transaction',
    'TransactionStats',
    'walltime',
    'MapSlotUuidUuid',

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

    # UUID (uint128) based pmap types for indexes
    'MapUuidUuid',
    'MapUuidUuidSet',
    'MapUuidStringUuid',

    #
    # String pmaps
    #

    # String (utf8) based pmap types for object containers
    'MapStringUuid',
    'MapStringOid',
    'MapStringJson',
    'MapStringCbor',
    'MapStringPickle',
    'MapStringFlatBuffers',

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

    # OID (uint64) based pmap types for indexes
    'MapOidOid',
    'MapOidOidSet',
    'MapOidStringOid',
    'MapOidOidOid',
    'MapOidTimestampOid',
    'MapOidTimestampStringOid',
)

TABLES_BY_UUID = {}  # type: Dict[uuid.UUID, object]
"""
Map of table UUIDs to persistant maps stored in slots in a KV store.
"""


def table(oid, marshal=None, parse=None, build=None, cast=None, compress=None):
    if type(oid) == six.text_type:
        oid = uuid.UUID(oid)

    assert isinstance(oid, uuid.UUID)
    assert marshal is None or callable(marshal)
    assert parse is None or callable(parse)
    assert build is None or callable(build)
    assert cast is None or callable(cast)
    assert compress is None or compress in [PersistentMap.COMPRESS_ZLIB, PersistentMap.COMPRESS_SNAPPY]

    def decorate(o):
        assert oid not in TABLES_BY_UUID

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
