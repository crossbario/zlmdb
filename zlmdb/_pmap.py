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

import struct
import sys
import zlib

from zlmdb import _types, _errors

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
    """
    Iterator that walks over zLMDB database records.
    """
    def __init__(self,
                 txn,
                 pmap,
                 from_key=None,
                 to_key=None,
                 return_keys=True,
                 return_values=True,
                 reverse=False,
                 limit=None):
        """

        :param txn:
        :param pmap:
        :param from_key:
        :param to_key:
        :param return_keys:
        :param return_values:
        :param reverse:
        :param limit:
        """
        self._txn = txn
        self._pmap = pmap

        if from_key:
            self._from_key = struct.pack('>H', pmap._slot) + pmap._serialize_key(from_key)
        else:
            self._from_key = struct.pack('>H', pmap._slot)

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
                self._found = self._cursor.last()
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
    Holds book-keeping metadata for indexes on tables (pmaps).
    """
    def __init__(self, name, fkey, pmap, nullable=False, unique=True):
        """

        :param name: Index name.
        :type name: str

        :param fkey: Function that extracts the indexed value from the indexed table.
        :type fkey: callable

        :param pmap: Persistent map for index storage.
        :type pmap: :class:`zlmdb._pmap.PersistentMap`

        :param nullable: Whether the indexed table column is allowed to
            take ``None`` values.
        :type nullable: bool

        :param unique: Whether the indexed table column must take unique values.
        :type unique: bool
        """
        self._name = name
        self._fkey = fkey
        self._pmap = pmap
        self._nullable = nullable
        self._unique = unique

    @property
    def name(self):
        """
        Index name property.

        :return: Name of the index (on the indexed table).
        :rtype: str
        """
        return self._name

    @property
    def fkey(self):
        """
        Indexed value extractor property.

        :return: Function to extract indexed value from the indexed table.
        :rtype: callable
        """
        return self._fkey

    @property
    def pmap(self):
        """
        Index table (pmap) property.

        :return: Persistent map for index storage.
        :rtype: :class:`zlmdb._pmap.PersistentMap`
        """
        return self._pmap

    @property
    def nullable(self):
        """
        Index nullable property.

        :return: Whether the indexed table column is allowed to
            take ``None`` values.
        :rtype: bool
        """
        return self._nullable

    @property
    def unique(self):
        """
        Index uniqueness property-

        :return: Whether the indexed table column must take unique values.
        :rtype: bool
        """
        return self._unique


def is_null(value):
    """
    Check if the scalar value or tuple/list value is NULL.

    :param value: Value to check.
    :type value: a scalar or tuple or list

    :return: Returns ``True`` if and only if the value is NULL (scalar value is None
        or _any_ tuple/list elements are None).
    :rtype: bool
    """
    if type(value) in (tuple, list):
        for v in value:
            if v is None:
                return True
        return False
    else:
        return value is None


def qual(obj):
    """
    Return fully qualified name of a class.
    """
    return u'{}.{}'.format(obj.__class__.__module__, obj.__class__.__name__)


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
        assert slot is None or type(slot) == int
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

    def indexes(self):
        """

        :return:
        """
        return sorted(self._indexes.keys())

    def attach_index(self, name, pmap, fkey, nullable=False, unique=True):
        """

        :param name:
        :param pmap:
        :param fkey:
        :param nullable:
        :param unique:
        :return:
        """
        assert type(name) == str
        assert callable(fkey)
        assert isinstance(pmap, PersistentMap)
        assert type(nullable) == bool
        assert type(unique) == bool

        if name in self._indexes:
            raise Exception('index with name "{}" already exists'.format(name))
        self._indexes[name] = Index(name, fkey, pmap, nullable, unique)

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

        # if there are indexes defined, get existing object (if any),
        # so that we can properly maintain the indexes, should indexed
        # columns be set to NULL, in which case we need to delete the
        # respective index record
        _old_value = None
        if self._indexes:
            _old_data = txn.get(_key)
            if _old_data:
                if self._decompress:
                    _old_data = self._decompress(_old_data)
                _old_value = self._deserialize_value(_old_data)

        # insert data record
        txn.put(_key, _data)

        # insert records into indexes
        for index in self._indexes.values():

            # extract indexed column value, which will become the index record key
            _fkey = index.fkey(value)

            if _old_value:
                _fkey_old = index.fkey(_old_value)

                if not is_null(_fkey_old) and _fkey_old != _fkey:
                    _idx_key = struct.pack('>H', index.pmap._slot) + index.pmap._serialize_key(_fkey_old)
                    txn.delete(_idx_key)

            if is_null(_fkey):
                if not index.nullable:
                    raise _errors.NullValueConstraint(
                        'cannot insert NULL value into non-nullable index "{}::{}"'.format(qual(self), index.name))
            else:
                _key = struct.pack('>H', index.pmap._slot) + index.pmap._serialize_key(_fkey)
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

        # delete records from indexes
        if self._indexes:
            value = self.__getitem__(txn_key)
            if value:
                for index in self._indexes.values():
                    _idx_key = struct.pack('>H', index.pmap._slot) + index.pmap._serialize_key(index.fkey(value))
                    txn.delete(_idx_key)

        # delete actual data record
        txn.delete(_key)

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

        return PersistentMapIterator(txn,
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


class MapUuidUuidCbor(_types._UuidUuidKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, UUID) keys and CBOR values.
    """
    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapUuidTimestampBytes32(_types._UuidTimestampKeysMixin, _types._Bytes32ValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, Timestamp) keys and Bytes32 values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidUuidUuid(_types._UuidUuidKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, UUID) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidStringUuid(_types._UuidStringKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, string) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidUuidStringUuid(_types._UuidUuidStringKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, UUID, string) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidUuidUuidStringUuid(_types._UuidUuidUuidStringKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, UUID, UUID string) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapUuidStringOid(_types._UuidStringKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, string) keys and Oid values.
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


class MapUuidTimestampFlatBuffers(_types._UuidTimestampKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, Timestamp) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapTimestampFlatBuffers(_types._TimestampKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with Timestamp keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapTimestampUuidFlatBuffers(_types._TimestampUuidKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Timestamp, UUID) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapUuidBytes20Uint8FlatBuffers(_types._UuidBytes20Uint8KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, bytes[20], uint8) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapUuidBytes20Uint8UuidFlatBuffers(_types._UuidBytes20Uint8UuidKeysMixin, _types._FlatBuffersValuesMixin,
                                         PersistentMap):
    """
    Persistent map with (UUID, bytes[20], uint8, UUID) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapUuidBytes20Bytes20Uint8UuidFlatBuffers(_types._UuidBytes20Bytes20Uint8UuidKeysMixin,
                                                _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, bytes[20], bytes[20], uint8, UUID) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapTimestampUuidStringFlatBuffers(_types._TimestampUuidStringKeysMixin, _types._FlatBuffersValuesMixin,
                                        PersistentMap):
    """
    Persistent map with (Timestamp, UUID, String) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapTimestampBytes32FlatBuffers(_types._TimestampBytes32KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Timestamp, Bytes32) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapTimestampStringFlatBuffers(_types._TimestampStringKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Timestamp, String) keys and FlatBuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapUuidTimestampCbor(_types._UuidTimestampKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, Timestamp) keys and CBOR values.
    """
    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapTimestampUuidCbor(_types._TimestampUuidKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with (Timestamp, UUID) keys and CBOR values.
    """
    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapStringTimestampCbor(_types._StringTimestampKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with (String, Timestamp) keys and CBOR values.
    """
    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapTimestampStringCbor(_types._TimestampStringKeysMixin, _types._CborValuesMixin, PersistentMap):
    """
    Persistent map with (Timestamp, String) keys and CBOR values.
    """
    def __init__(self, slot=None, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


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


class MapStringOidOid(_types._StringOidKeysMixin, _types._OidValuesMixin, PersistentMap):
    """
    Persistent map with (string:utf8, OID:uint64) keys and OID:uint64 values.
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
# Key types: Bytes32, (Bytes32, Bytes32), (Bytes32, String), ...
# Value type: FlatBuffers
#


class MapBytes32Uuid(_types._Bytes32KeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with Bytes32 keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes32Timestamp(_types._Bytes32KeysMixin, _types._TimestampValuesMixin, PersistentMap):
    """
    Persistent map with Bytes32 keys and Timestamp values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes32Bytes32(_types._Bytes32KeysMixin, _types._Bytes32ValuesMixin, PersistentMap):
    """
    Persistent map with Bytes32 keys and Bytes32 values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes32FlatBuffers(_types._Bytes32KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with Bytes32 keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes32UuidFlatBuffers(_types._Bytes32UuidKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes32, UUID) keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapUuidUuidStringFlatBuffers(_types._UuidUuidStringKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (UUID, UUID, String) keys and Flatbuffers values.
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


#
# Key types: Bytes20, (Bytes20, Bytes20), (Bytes20, String)
# Value type: FlatBuffers
#


class MapBytes20Bytes20(_types._Bytes20KeysMixin, _types._Bytes20ValuesMixin, PersistentMap):
    """
    Persistent map with Bytes20 keys and Bytes20 values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20Bytes20Timestamp(_types._Bytes20KeysMixin, _types._Bytes20TimestampValuesMixin, PersistentMap):
    """
    Persistent map with Bytes20 keys and (Bytes20, Timestamp) values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20TimestampBytes20(_types._Bytes20TimestampKeysMixin, _types._Bytes20ValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes20, Timestamp) keys and Bytes20 values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20TimestampUuid(_types._Bytes20TimestampKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes20, Timestamp) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20Uuid(_types._Bytes20KeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with Bytes20 keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20Bytes16(_types._Bytes20KeysMixin, _types._Bytes16ValuesMixin, PersistentMap):
    """
    Persistent map with Bytes20 keys and Bytes16 values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20FlatBuffers(_types._Bytes20KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with Bytes20 keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes16FlatBuffers(_types._Bytes16KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with Bytes16 keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes16TimestampUuid(_types._Bytes16TimestampKeysMixin, _types._UuidValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes20, Timestamp) keys and UUID values.
    """
    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MapBytes20Bytes20FlatBuffers(_types._Bytes20Bytes20KeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes20, Bytes20) keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


class MapBytes20StringFlatBuffers(_types._Bytes20StringKeysMixin, _types._FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with (Bytes20, String) keys and Flatbuffers values.
    """
    def __init__(self, slot=None, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)
        _types._FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)
