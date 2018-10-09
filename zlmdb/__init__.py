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

from typing import Dict  # noqa

from ._version import __version__

from ._pmap import MapSlotUuidUuid, \
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
                   MapOidFlatBuffers

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
    'MapUuidString',
    'MapUuidOid',
    'MapUuidUuid',
    'MapUuidJson',
    'MapUuidCbor',
    'MapUuidPickle',
    'MapUuidFlatBuffers',
    'MapUuidStringUuid',
    'MapUuidUuidSet',
    'MapStringString',
    'MapStringOid',
    'MapStringUuid',
    'MapStringJson',
    'MapStringCbor',
    'MapStringPickle',
    'MapStringFlatBuffers',
    'MapOidString',
    'MapOidOid',
    'MapOidUuid',
    'MapOidJson',
    'MapOidCbor',
    'MapOidPickle',
    'MapOidFlatBuffers',
)

_SLOTS = {}  # type: Dict[int, object]
_META_DOC_OTYPE_TO_SLOT = {}  # type: Dict[str, object]


def slot(slot_no, marshal=None, unmarshal=None, build=None, cast=None, compress=False, enable_meta=False):
    def decorate(o):
        o._zlmdb_slot = slot_no
        o._zlmdb_marshal = marshal
        o._zlmdb_unmarshal = unmarshal
        o._zlmdb_build = build
        o._zlmdb_cast = cast
        o._zlmdb_compress = compress
        o._zlmdb_enable_meta = enable_meta
        # assert slot_no not in _SLOTS
        _SLOTS[slot_no] = o
        if enable_meta:
            # assert o.__name__ not in _META_DOC_OTYPE_TO_SLOT
            _META_DOC_OTYPE_TO_SLOT[o.__name__] = slot_no
        return o

    return decorate
