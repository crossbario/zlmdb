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
import random
import pickle
import sys
import os
import uuid
import json
import zlib

import six
import cbor2
import flatbuffers

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
    def __init__(self, txn, pmap, from_key=None, to_key=None, return_keys=True, return_values=True):
        self._txn = txn
        self._pmap = pmap

        self._from_key = struct.pack('>H', pmap._slot)
        if from_key:
            self._from_key += pmap._serialize_key(from_key)

        if to_key:
            self._to_key = struct.pack('>H', pmap._slot) + pmap._serialize_key(to_key)
        else:
            self._to_key = struct.pack('>H', pmap._slot + 1)

        self._return_keys = return_keys
        self._return_values = return_values

        self._cursor = None
        self._found = None

    def __iter__(self):
        self._cursor = self._txn._txn.cursor()
        self._found = self._cursor.set_range(self._from_key)
        return self

    def __next__(self):
        if not self._found:
            raise StopIteration

        _key = self._cursor.key()
        if _key >= self._to_key:
            raise StopIteration

        _key = self._pmap._deserialize_key(_key[2:])

        if self._return_values:
            _data = self._cursor.value()
            if _data:
                if self._pmap._decompress:
                    _data = self._pmap._decompress(_data)
                _data = self._pmap._deserialize_value(_data)
        else:
            _data = None

        self._found = self._cursor.next()

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
    def __init__(self, name, fkey, pmap):
        self._name = name
        self._fkey = fkey
        self._pmap = pmap

    @property
    def name(self):
        return self._name

    @property
    def fkey(self):
        return self._fkey

    @property
    def pmap(self):
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
        assert type(slot) in six.integer_types
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
        assert type(name) == six.text_type
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
        assert type(name) == six.text_type
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

    def __len__(self):
        raise Exception('not implemented')

    def __iter__(self):
        raise Exception('not implemented')

    def select(self, txn, from_key=None, to_key=None, return_keys=True, return_values=True):
        """

        :param txn:
        :param from_key:
        :param to_key:
        :param return_keys:
        :param return_values:
        :return:
        """
        return PersistentMapIterator(
            txn, self, from_key=from_key, to_key=to_key, return_keys=return_keys, return_values=return_values)

    def count(self, txn, prefix=None):
        """

        :param txn:
        :param prefix:
        :return:
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


# LMDB Key-Value types
#
# Key sizes must be between 1 and mdb_env_get_maxkeysize() inclusive. The same applies to data sizes
# in databases with the MDB_DUPSORT flag. Other data items can in theory be from 0 to 0xffffffff bytes long.
#
# see: http://www.lmdb.tech/doc/group__mdb.html#structMDB__val

#
# Key Type: OID, String, UUID
#


class _OidKeysMixin(object):

    MAX_OID = 9007199254740992
    """
    Valid OID are from the integer range [0, MAX_OID].

    The upper bound 2**53 is chosen since it is the maximum integer that can be
    represented as a IEEE double such that all smaller integers are representable as well.

    Hence, IDs can be safely used with languages that use IEEE double as their
    main (or only) number type (JavaScript, Lua, etc).
    """

    @staticmethod
    def new_key(secure=False):
        if secure:
            while True:
                data = os.urandom(8)
                key = struct.unpack('>Q', data)[0]
                if key <= _OidKeysMixin.MAX_OID:
                    return key
        else:
            random.randint(0, _OidKeysMixin.MAX_OID)

    def _serialize_key(self, key):
        assert type(key) in six.integer_types
        assert key >= 0 and key <= _OidKeysMixin.MAX_OID
        return struct.pack('>Q', key)

    def _deserialize_key(self, data):
        return struct.unpack('>Q', data)[0]


class _StringKeysMixin(object):

    CHARSET = u'345679ACEFGHJKLMNPQRSTUVWXY'
    """
    Charset from which to generate random key IDs.

    .. note::

        We take out the following 9 chars (leaving 27), because there is visual ambiguity: 0/O/D, 1/I, 8/B, 2/Z.
    """
    CHAR_GROUPS = 4
    CHARS_PER_GROUP = 6
    GROUP_SEP = u'-'

    @staticmethod
    def new_key():
        """
        Generate a globally unique serial / product code of the form ``u'YRAC-EL4X-FQQE-AW4T-WNUV-VN6T'``.
        The generated value is cryptographically strong and has (at least) 114 bits of entropy.

        :return: new random string key
        """
        rng = random.SystemRandom()
        token_value = u''.join(
            rng.choice(_StringKeysMixin.CHARSET)
            for _ in range(_StringKeysMixin.CHAR_GROUPS * _StringKeysMixin.CHARS_PER_GROUP))
        if _StringKeysMixin.CHARS_PER_GROUP > 1:
            return _StringKeysMixin.GROUP_SEP.join(
                map(u''.join, zip(*[iter(token_value)] * _StringKeysMixin.CHARS_PER_GROUP)))
        else:
            return token_value

    def _serialize_key(self, key):
        return key.encode('utf8')

    def _deserialize_key(self, data):
        return data.decode('utf8')


class _UuidKeysMixin(object):
    @staticmethod
    def new_key():
        # https: // docs.python.org / 3 / library / uuid.html  # uuid.uuid4
        # return uuid.UUID(bytes=os.urandom(16))
        return uuid.uuid4()

    def _serialize_key(self, key):
        # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).
        # https://docs.python.org/3/library/uuid.html#uuid.UUID.bytes
        return key.bytes

    def _deserialize_key(self, data):
        return uuid.UUID(bytes=data)


#
# Value Types: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class _StringValuesMixin(object):
    def _serialize_value(self, value):
        return value.encode('utf8')

    def _deserialize_value(self, data):
        return data.decode('utf8')


class _OidValuesMixin(object):
    def _serialize_value(self, value):
        return struct.pack('>Q', value)

    def _deserialize_value(self, data):
        return struct.unpack('>Q', data)[0]


class _UuidValuesMixin(object):
    def _serialize_value(self, value):
        return value.bytes

    def _deserialize_value(self, data):
        return uuid.UUID(bytes=data)


class _JsonValuesMixin(object):
    def __init__(self, marshal=None, unmarshal=None):
        self._marshal = marshal or (lambda x: x)
        self._unmarshal = unmarshal or (lambda x: x)

    def _serialize_value(self, value):
        return json.dumps(
            self._marshal(value), separators=(',', ':'), ensure_ascii=False, sort_keys=False).encode('utf8')

    def _deserialize_value(self, data):
        return self._unmarshal(json.loads(data.decode('utf8')))


class _CborValuesMixin(object):
    def __init__(self, marshal=None, unmarshal=None):
        self._marshal = marshal or (lambda x: x)
        self._unmarshal = unmarshal or (lambda x: x)

    def _serialize_value(self, value):
        return cbor2.dumps(self._marshal(value))

    def _deserialize_value(self, data):
        return self._unmarshal(cbor2.loads(data))


class _PickleValuesMixin(object):

    # PROTOCOL = _NATIVE_PICKLE_PROTOCOL
    PROTOCOL = 2

    def _serialize_value(self, value):
        return pickle.dumps(value, protocol=self.PROTOCOL)

    def _deserialize_value(self, data):
        return pickle.loads(data)


class _FlatBuffersValuesMixin(object):
    def __init__(self, build, cast):
        self._build = build
        self._cast = cast

    def _serialize_value(self, value):
        builder = flatbuffers.Builder(0)
        obj = self._build(value, builder)
        builder.Finish(obj)
        buf = builder.Output()
        return bytes(buf)

    def _deserialize_value(self, data):
        return self._cast(data)


#
# Key: UUID -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapUuidString(_UuidKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and string (utf8) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapUuidOid(_UuidKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and OID (uint64) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapUuidUuid(_UuidKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapUuidJson(_UuidKeysMixin, _JsonValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and JSON values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapUuidCbor(_UuidKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and CBOR values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapUuidPickle(_UuidKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and Python Pickle values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapUuidFlatBuffers(_UuidKeysMixin, _FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and FlatBuffers values.
    """

    def __init__(self, slot, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


#
# Key: String -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapStringString(_StringKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and string (utf8) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapStringOid(_StringKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and OID (uint64) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapStringUuid(_StringKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapStringJson(_StringKeysMixin, _JsonValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and JSON values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapStringCbor(_StringKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and CBOR values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapStringPickle(_StringKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and Python pickle values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapStringFlatBuffers(_StringKeysMixin, _FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and FlatBuffers values.
    """

    def __init__(self, slot, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)


#
# Key: OID -> Value: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


class MapOidString(_OidKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and string (utf8) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapOidOid(_OidKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and OID (uint64) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapOidUuid(_OidKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and UUID (16 bytes) values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapOidJson(_OidKeysMixin, _JsonValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and JSON values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _JsonValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapOidCbor(_OidKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and CBOR values.
    """

    def __init__(self, slot, compress=None, marshal=None, unmarshal=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _CborValuesMixin.__init__(self, marshal=marshal, unmarshal=unmarshal)


class MapOidPickle(_OidKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and Python pickle values.
    """

    def __init__(self, slot, compress=None):
        PersistentMap.__init__(self, slot, compress=compress)


class MapOidFlatBuffers(_OidKeysMixin, _FlatBuffersValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and FlatBuffers values.
    """

    def __init__(self, slot, compress=None, build=None, cast=None):
        PersistentMap.__init__(self, slot, compress=compress)
        _FlatBuffersValuesMixin.__init__(self, build=build, cast=cast)
