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
"""Persistent mappings."""

from __future__ import absolute_import

import struct
import sys
import zlib

import six

from zlmdb import _types

try:
    import snappy
except ImportError:
    HAS_SNAPPY = False
else:
    HAS_SNAPPY = True

if sys.version_info < (3, ):
    from UserDict import DictMixin as MutableMapping
    _NATIVE_PICKLE_PROTOCOL = 2
else:
    from collections.abc import MutableMapping
    _NATIVE_PICKLE_PROTOCOL = 4


class PersistentMapIterator(object):
    def __init__(self,
                 txn,
                 pmap,
                 from_key=None,
                 to_key=None,
                 return_keys=True,
                 return_values=True,
                 reverse=False,
                 limit=None):
        self._txn = txn
        self._pmap = pmap

        self._from_key = struct.pack('>H', pmap._slot)
        if from_key:
            self._from_key += pmap._serialize_key(from_key)

        if to_key:
            self._to_key = struct.pack('>H', pmap._slot) + pmap._serialize_key(to_key)
        else:
            self._to_key = struct.pack('>H', pmap._slot + 1)

        self._reverse = reverse

        self._return_keys = return_keys
        self._return_values = return_values

        self._limit = limit
        self._read = 0

        self._cursor = None
        self._found = None

    def __iter__(self):
        self._cursor = self._txn._txn.cursor()

        # https://lmdb.readthedocs.io/en/release/#lmdb.Cursor.set_range
        if self._reverse:
            # seek to the first record starting from to_key (and going reverse)
            self._found = self._cursor.set_range(self._to_key)
            if self._found:
                # to_key is _not_ inclusive, so we move on one record
                self._found = self._cursor.prev()
        else:
            # seek to the first record starting from from_key
            self._found = self._cursor.set_range(self._from_key)

        return self

    def __next__(self):
        # stop criteria: no more records or limit reached
        if not self._found or (self._limit and self._read >= self._limit):
            raise StopIteration
        self._read += 1

        # stop criteria: end of key-range reached
        _key = self._cursor.key()
        if self._reverse:
            if _key < self._from_key:
                raise StopIteration
        else:
            if _key >= self._to_key:
                raise StopIteration

        # read actual app key-value (before moving cursor)
        _key = self._pmap._deserialize_key(_key[2:])

        if self._return_values:
            _data = self._cursor.value()
            if _data:
                if self._pmap._decompress:
                    _data = self._pmap._decompress(_data)
                _data = self._pmap._deserialize_value(_data)
        else:
            _data = None

        # move the cursor
        if self._reverse:
            self._found = self._cursor.prev()
        else:
            self._found = self._cursor.next()

        # return app key-value
        if self._return_keys and self._return_values:
            return _key, _data
        elif self._return_values:
            return _data
        elif self._return_keys:
            return _key
        else:
            return None

    next = __next__  # Python 2


class Index(object):
    """
    Holds book keeping info for indexes on tables (pmaps).
    """

    def __init__(self, name, fkey, pmap):
        """

        :param name:
        :param fkey:
        :param pmap:
        """
        self._name = name
        self._fkey = fkey
        self._pmap = pmap

    @property
    def name(self):
        """

        :return:
        """
        return self._name

    @property
    def fkey(self):
        """

        :return:
        """
        return self._fkey

    @property
    def pmap(self):
        """

        :return:
        """
        return self._pmap


class PersistentMap(MutableMapping):
    """
    Abstract base class for persistent maps stored in LMDB.
    """
    COMPRESS_ZLIB = 1
    COMPRESS_SNAPPY = 2

    def __init__(self, slot, compress=None):
        """

        :param slot:
        :param compress:
        """
        assert slot is None or type(slot) in six.integer_types
        assert compress is None or compress in [PersistentMap.COMPRESS_ZLIB, PersistentMap.COMPRESS_SNAPPY]

        self._slot = slot

        if compress:
            if compress not in [PersistentMap.COMPRESS_ZLIB, PersistentMap.COMPRESS_SNAPPY]:
                raise Exception('invalid compression mode')
            if compress == PersistentMap.COMPRESS_SNAPPY and not HAS_SNAPPY:
                raise Exception('snappy compression requested, but snappy is not installed')
            if compress == PersistentMap.COMPRESS_ZLIB:
                self._compress = zlib.compress
                self._decompress = zlib.decompress
            elif compress == PersistentMap.COMPRESS_SNAPPY:
                self._compress = snappy.compress
                self._decompress = snappy.uncompress
            else:
                raise Exception('logic error')
        else:
            self._compress = lambda data: data
            self._decompress = lambda data: data

        self._indexes = {}

    def attach_index(self, name, fkey, pmap):
        """

        :param name:
        :param fkey:
        :param pmap:
        :return:
        """
        assert type(name) == str
        assert callable(fkey)
        assert isinstance(pmap, PersistentMap)
        if name in self._indexes:
            raise Exception('index with name "{}" already exists'.format(name))
        self._indexes[name] = Index(name, fkey, pmap)

    def detach_index(self, name):
        """

        :param name:
        :return:
        """
        assert type(name) == str
        if name in self._indexes:
            del self._indexes[name]

    def _serialize_key(self, key):
        raise Exception('must be implemented in derived class')

    def _deserialize_key(self, data):
        raise Exception('must be implemented in derived class')

    def _serialize_value(self, value):
        raise Exception('must be implemented in derived class')

    def _deserialize_value(self, data):
        raise Exception('must be implemented in derived class')

    def __contains__(self, txn_key):
        """

        :param txn_key:
        :return:
        """
        assert type(txn_key) == tuple and len(txn_key) == 2
        txn, key = txn_key

        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        _data = txn.get(_key)

        return _data is not None

    def __getitem__(self, txn_key):
        """

        :param txn_key:
        :return:
        """
        assert type(txn_key) == tuple and len(txn_key) == 2
        txn, key = txn_key

        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        _data = txn.get(_key)

        if _data:
            if self._decompress:
                _data = self._decompress(_data)
            return self._deserialize_value(_data)
        else:
            return None

    def __setitem__(self, txn_key, value):
        """

        :param txn_key:
        :param value:
        :return:
        """
        assert type(txn_key) == tuple and len(txn_key) == 2

        txn, key = txn_key

        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        _data = self._serialize_value(value)

        if self._compress:
            _data = self._compress(_data)

        txn.put(_key, _data)

        for index in self._indexes.values():
            _key = struct.pack('>H', index.pmap._slot) + index.pmap._serialize_key(index.fkey(value))
            _data = index.pmap._serialize_value(key)
            txn.put(_key, _data)

    def __delitem__(self, txn_key):
        """

        :param txn_key:
        :return:
        """
        assert type(txn_key) == tuple and len(txn_key) == 2

        txn, key = txn_key

        _key = struct.pack('>H', self._slot) + self._serialize_key(key)

        txn.delete(_key)

        # FIXME: delete entries from indexes

    def __len__(self):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def select(self, txn, from_key=None, to_key=None, return_keys=True, return_values=True, reverse=False, limit=None):
        """
        Select all records (key-value pairs) in table, optionally within a given key range.

        :param txn: The transaction in which to run.
        :type txn: :class:`zlmdb.Transaction`

        :param from_key: Return records starting from (and including) this key.
        :type from_key: object

        :param to_key: Return records up to (but not including) this key.
        :type to_key: object

        :param return_keys: If ``True`` (default), return keys of records.
        :type return_keys: bool

        :param return_values: If ``True`` (default), return values of records.
        :type return_values: bool

        :param limit: Limit number of records returned.
        :type limit: int

        :return:
        """
        assert type(return_keys) == bool
        assert type(return_values) == bool
        assert type(reverse) == bool
        assert limit is None or (type(limit) == int and limit > 0 and limit < 10000000)

        return PersistentMapIterator(
            txn,
            self,
            from_key=from_key,
            to_key=to_key,
            return_keys=return_keys,
            return_values=return_values,
            reverse=reverse,
            limit=limit)

    def count(self, txn, prefix=None):
        """
        Count number of records in the persistent map. When no prefix
        is given, the total number of records is returned. When a prefix
        is given, only the number of records with keys that have this
        prefix are counted.

        :param txn: The transaction in which to run.
        :type txn: :class:`zlmdb.Transaction`

        :param prefix: The key prefix of records to count.
        :type prefix: object

        :returns: The number of records.
        :rtype: int
        """
        key_from = struct.pack('>H', self._slot)
        if prefix:
            key_from += self._serialize_key(prefix)
        kfl = len(key_from)

        cnt = 0
        cursor = txn._txn.cursor()
        has_more = cursor.set_range(key_from)
        while has_more:
            _key = cursor.key()
            _prefix = _key[:kfl]
            if _prefix != key_from:
                break
            cnt += 1
            has_more = cursor.next()

        return cnt

    def count_range(self, txn, from_key, to_key):
        """
        Counter number of records in the perstistent map with keys
        within the given range.

        :param txn: The transaction in which to run.
        :type txn: :class:`zlmdb.Transaction`

        :param from_key: Count records starting and including from this key.
        :type from_key: object

        :param to_key: End counting records before this key.
        :type to_key: object

        :returns: The number of records.
        :rtype: int
        """
        key_from = struct.pack('>H', self._slot) + self._serialize_key(from_key)
        to_key = struct.pack('>H', self._slot) + self._serialize_key(to_key)

        cnt = 0
        cursor = txn._txn.cursor()
        has_more = cursor.set_range(key_from)
        while has_more:
            if cursor.key() >= to_key:
                break
            cnt += 1
            has_more = cursor.next()

        return cnt

    def truncate(self, txn, rebuild_indexes=True):
        """

        :param txn:
        :param rebuild_indexes:
        :return:
        """
        key_from = struct.pack('>H', self._slot)
        key_to = struct.pack('>H', self._slot + 1)
        cursor = txn._txn.cursor()
        cnt = 0
        if cursor.set_range(key_from):
            key = cursor.key()
            while key < key_to:
                if not cursor.delete(dupdata=True):
                    break
                cnt += 1
                if txn._stats:
                    txn._stats.dels += 1
        if rebuild_indexes:
            deleted, _ = self.rebuild_indexes(txn)
            cnt += deleted
        return cnt

    def rebuild_indexes(self, txn):
        """

        :param txn:
        :return:
        """
        total_deleted = 0
        total_inserted = 0
        for name in sorted(self._indexes.keys()):
            deleted, inserted = self.rebuild_index(txn, name)
            total_deleted += deleted
            total_inserted += inserted
        return total_deleted, total_inserted

    def rebuild_index(self, txn, name):
        """

        :param txn:
        :param name:
        :return:
        """
        if name in self._indexes:
            index = self._indexes[name]

            deleted = index.pmap.truncate(txn)

            key_from = struct.pack('>H', self._slot)
            key_to = struct.pack('>H', self._slot + 1)
            cursor = txn._txn.cursor()
            inserted = 0
            if cursor.set_range(key_from):
                while cursor.key() < key_to:
                    data = cursor.value()
                    if data:
                        value = self._deserialize_value(data)

                        _key = struct.pack('>H', index.pmap._slot) + index.pmap._serialize_key(index.fkey(value))
                        _data = index.pmap._serialize_value(value.oid)

                        txn.put(_key, _data)
                        inserted += 1
                    if not cursor.next():
                        break
            return deleted, inserted
        else:
            raise Exception('no index "{}" attached'.format(name))


#
# Key: UUID -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapSlotUuidUuid(_types._SlotUuidKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (slot, UUID) and UUID values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidString(_types._UuidKeysMixin, _types._StringValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and string (utf8) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidOid(_types._UuidKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and OID (uint64) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidUuid(_types._UuidKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidStringUuid(_types._UuidStringKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, string) keys and UUID values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidUuidSet(_types._UuidKeysMixin, _types._UuidSetValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, string) keys and UUID values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidJson(_types._UuidKeysMixin, _types._JsonValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and JSON values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapUuidCbor(_types._UuidKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and CBOR values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapUuidPickle(_types._UuidKeysMixin, _types._PickleValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and Python Pickle values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidFlatBuffers(_types._UuidKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and FlatBuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


#
# Key: String -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapStringString(_types._StringKeysMixin, _types._StringValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and string (utf8) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapStringOid(_types._StringKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and OID (uint64) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapStringUuid(_types._StringKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapStringJson(_types._StringKeysMixin, _types._JsonValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and JSON values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapStringCbor(_types._StringKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and CBOR values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapStringPickle(_types._StringKeysMixin, _types._PickleValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and Python pickle values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapStringFlatBuffers(_types._StringKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and FlatBuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


#
# Key: OID -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapOidString(_types._OidKeysMixin, _types._StringValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and string (utf8) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidOid(_types._OidKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and OID (uint64) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidUuid(_types._OidKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidJson(_types._OidKeysMixin, _types._JsonValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and JSON values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapOidCbor(_types._OidKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and CBOR values.
    """

    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapOidPickle(_types._OidKeysMixin, _types._PickleValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and Python pickle values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidFlatBuffers(_types._OidKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and FlatBuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapOidOidFlatBuffers(_types._OidOidKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (OID, OID) / (uint64, uint64) keys and FlatBuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapOid3FlatBuffers(_types._Oid3KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (OID, OID, OID) / (uint64, uint64, uint64) keys and FlatBuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapOidOidSet(_types._OidKeysMixin, _types._OidSetValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and OID-set (set of unique uint64) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidStringOid(_types._OidStringKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (OID, string) keys and OID values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidOidOid(_types._OidOidKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (OID, OID) keys and OID values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidTimestampOid(_types._OidTimestampKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (OID, Timestamp) keys and OID values, where Timestamp is a np.datetime64[ns].
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapOidTimestampFlatBuffers(_types._OidTimestampKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (OID, Timestamp) keys and Flatbuffers values, where Timestamp is a np.datetime64[ns].
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapOidTimestampStringOid(_types._OidTimestampStringKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (OID, Timestamp, String) keys and OID values, where Timestamp is a np.datetime64[ns].
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


#
# Key types: Bytes32, (Bytes32, Bytes32), (Bytes32, String)
# Value type: FlatBuffers
#


class MapBytes32FlatBuffers(_types._Bytes32KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with Bytes32 keys and Flatbuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes32Bytes32FlatBuffers(_types._Bytes32Bytes32KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes32, Bytes32) keys and Flatbuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes32StringFlatBuffers(_types._Bytes32StringKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes32, String) keys and Flatbuffers values.
    """

    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)
