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

"""Main module."""

import struct
import random
import string
import pickle
import sys
import os
import uuid

import cbor2
import lmdb

if sys.version_info < (3,):
    from UserDict import DictMixin as MutableMapping
    _PICKLE_PROTOCOL = 2
else:
    from collections.abc import MutableMapping
    _PICKLE_PROTOCOL = 4


class PersistentMap(MutableMapping):
    """
    Abstract base class for persistent maps stored in LMDB.
    """

    def __init__(self, *args, **kwargs):
        self._slot = kwargs.pop('slot', 0)
        self._indexes = {}

    def attach_transaction(self, txn):
        self._txn = txn

    def attach_index(self, index_name, index_key, index_map):
        self._indexes[index_name] = (index_key, index_map)

    def count(self, prefix=None):
        key_from = struct.pack('>H', self._slot)
        if prefix:
            key_from += self._serialize_key(prefix)

        cnt = 0

        cursor = self._txn._txn.cursor()
        if cursor.set_range(key_from):
            kfl = len(key_from)
            while True:
                _prefix = cursor.key()[:kfl]
                if _prefix != key_from:
                    break
                cnt += 1
                cursor.next()

        return cnt

    def truncate(self, rebuild_indexes=True):
        key_from = struct.pack('>H', self._slot)
        key_to = struct.pack('>H', self._slot + 1)
        cursor = self._txn._txn.cursor()
        cnt = 0
        if cursor.set_range(key_from):
            key = cursor.key()
            while key < key_to:
                if not cursor.delete(dupdata=True):
                    break
                cnt += 1
                self._txn._dels += 1
                self._txn._log.append((BaseTransaction.DEL, key))
        if rebuild_indexes:
            deleted, _ = self.rebuild_indexes()
            cnt += deleted
        return cnt

    def rebuild_indexes(self):
        total_deleted = 0
        total_inserted = 0
        for index_name in sorted(self._indexes.keys()):
            deleted, inserted = self.rebuild_index(index_name)
            total_deleted += deleted
            total_inserted += inserted
            print('rebuilt index "{}": {} deleted, {} inserted'.format(index_name, deleted, inserted))
        return total_deleted, total_inserted

    def rebuild_index(self, index_name):
        if index_name in self._indexes:
            index_key, index_map = self._indexes[index_name]

            deleted = index_map.truncate()

            key_from = struct.pack('>H', self._slot)
            key_to = struct.pack('>H', self._slot + 1)
            cursor = self._txn._txn.cursor()
            inserted = 0
            if cursor.set_range(key_from):
                while cursor.key() < key_to:
                    data = cursor.value()
                    if data:
                        value = self._deserialize_value(data)

                        _key = struct.pack('>H', index_map._slot) + index_map._serialize_key(index_key(value))
                        _data = index_map._serialize_value(value.oid)

                        self._txn.put(_key, _data)
                        inserted += 1
                    if not cursor.next():
                        break
            return deleted, inserted
        else:
            raise Exception('no index "{}" attached'.format(index_name))

    def _serialize_key(self, key):
        raise Exception('not implemented')

    def _serialize_value(self, value):
        raise Exception('not implemented')

    def _deserialize_value(self, data):
        raise Exception('not implemented')

    def __getitem__(self, key):
        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        _data = self._txn.get(_key)
        if _data:
            return self._deserialize_value(_data)
        else:
            return None

    def __setitem__(self, key, value):
        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        _data = self._serialize_value(value)
        self._txn.put(_key, _data)

        for index_key, index_map in self._indexes.values():
            _key = struct.pack('>H', index_map._slot) + index_map._serialize_key(index_key(value))
            _data = index_map._serialize_value(key)
            self._txn.put(_key, _data)

    def __delitem__(self, key):
        _key = struct.pack('>H', self._slot) + self._serialize_key(key)
        self._txn.delete(_key)

    def __iter__(self):
        raise Exception('not implemented')

    def __len__(self):
        raise Exception('not implemented')


class _OidKeysMixin(object):

    @staticmethod
    def new_key(secure=True):
        if secure:
            return struct.unpack('@Q', os.urandom(8))
        else:
            return random.randint(0, 2**64-1)

    def _serialize_key(self, key):
        return struct.pack('>Q', key)


class _StringKeysMixin(object):

    CHARSET = u'345679ACEFGHJKLMNPQRSTUVWXY'
    """
    Charset from which to generate random key IDs.
    
    .. note::

        We take out the following 9 chars (leaving 27), because there is visual ambiguity: 0/O/D, 1/I, 8/B, 2/Z.
    """
    CHAR_GROUPS = 4
    CHARS_PER_GROUP = 6
    GROUP_SET = u'-'

    @staticmethod
    def new_key():
        """
        Generate a globally unique serial / product code of the form ``u'YRAC-EL4X-FQQE-AW4T-WNUV-VN6T'``.
        The generated value is cryptographically strong and has (at least) 114 bits of entropy.

        :return: new random string key
        """
        rng = random.SystemRandom()
        token_value = u''.join(rng.choice(self.CHARSET) for _ in range(self.CHAR_GROUPS * self.CHARS_PER_GROUP))
        if self.CHARS_PER_GROUP > 1:
            return sep.join(map(u''.join, zip(*[iter(token_value)] * self.CHARS_PER_GROUP)))
        else:
            return token_value

    def _serialize_key(self, key):
        return key.encode('utf8')


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


class _OidValuesMixin(object):

    def _serialize_value(self, value):
        return struct.pack('>Q', value)

    def _deserialize_value(self, data):
        return struct.unpack('>Q', data)[0]


class _StringValuesMixin(object):

    def _serialize_value(self, value):
        return value.encode('utf8')

    def _deserialize_value(self, data):
        return data.decode('utf8')


class _UuidValuesMixin(object):

    def _serialize_value(self, value):
        return value.bytes

    def _deserialize_value(self, data):
        return uuid.UUID(bytes=data)


class _CborValuesMixin(object):

    def _serialize_value(self, value):
        return cbor2.dumps(value)

    def _deserialize_value(self, data):
        return cbor2.loads(data)


class _PickleValuesMixin(object):

    def _serialize_value(self, value):
        return pickle.dumps(value, protocol=_PICKLE_PROTOCOL)

    def _deserialize_value(self, data):
        return pickle.loads(data)


class MapUuidString(_UuidKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and string (utf8) values.
    """


class MapUuidOid(_UuidKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and OID (uint64) values.
    """


class MapUuidUuid(_UuidKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and UUID (16 bytes) values.
    """


class MapUuidCbor(_UuidKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and CBOR values.
    """


class MapUuidPickle(_UuidKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with UUID (16 bytes) keys and Python Pickle values.
    """


class MapStringString(_StringKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and string (utf8) values.
    """


class MapStringOid(_StringKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and OID (uint64) values.
    """


class MapStringUuid(_StringKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and UUID (16 bytes) values.
    """


class MapStringCbor(_StringKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and CBOR values.
    """


class MapStringPickle(_StringKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and Python pickle values.
    """


class MapOidString(_OidKeysMixin, _StringValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and string (utf8) values.
    """


class MapOidOid(_OidKeysMixin, _OidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and OID (uint64) values.
    """


class MapOidUuid(_OidKeysMixin, _UuidValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and UUID (16 bytes) values.
    """


class MapOidCbor(_OidKeysMixin, _CborValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and CBOR values.
    """


class MapOidPickle(_OidKeysMixin, _PickleValuesMixin, PersistentMap):
    """
    Persistent map with OID (uint64) keys and Python pickle values.
    """


class TransactionStats(object):

    def __init__(self):
        self.puts = 0
        self.dels = 0

    def reset(self):
        self.puts = 0
        self.dels = 0


class BaseTransaction(object):

    PUT = 1
    DEL = 2

    def __init__(self, env, write=False, stats=None):
        self._env = env
        self._write = write
        self._txn = None
        self._log = None
        self._stats = stats

    def get(self, key):
        return self._txn.get(key)

    def put(self, key, data, overwrite=True):
        # store the record, returning True if it was written, or False to indicate the key
        # was already present and overwrite=False.
        was_written = self._txn.put(key, data, overwrite=overwrite)
        if was_written:
            if self._stats:
                self._stats.puts += 1
            if self._log:
                self._log.append((BaseTransaction.PUT, key))
        return was_written

    def delete(self, key):
        was_deleted = self._txn.delete(key)
        if was_deleted:
            if self._stats:
                self._stats.dels += 1
            if self._log:
                self._log.append((BaseTransaction.DEL, key))
        return was_deleted

    def attach(self):
        pass

    def __enter__(self):
        assert(self._txn is None)
        self._txn = lmdb.Transaction(self._env, write=self._write)
        self.attach()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert(self._txn is not None)
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        # If the context was exited without an exception, all three arguments will be None.
        if exc_type is None:
            if self._log:
                cnt = 0
                for op, key in self._log:
                    _key = struct.pack('>H', 0)
                    _data = struct.pack('>H', op) + key
                    self._txn.put(_key, _data)
                    cnt += 1
            self._txn.commit()
        else:
            self._txn.abort()
