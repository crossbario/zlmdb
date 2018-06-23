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
