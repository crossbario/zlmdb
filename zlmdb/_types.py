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

from __future__ import absolute_import

import struct
import random
import pickle
import os
import uuid
import json
import time

import six
import cbor2
import flatbuffers

try:
    import numpy as np
except ImportError:
    HAS_NUMPY = False
else:
    HAS_NUMPY = True

# time_ns: epoch time in ns, corresponds to pandas.Timestamp or numpy.datetime64[ns]
# perf_counter_ns: hardware time in ns, use only in relative terms
if hasattr(time, 'time_ns'):
    # python 3.7
    time_ns = time.time_ns
    perf_counter_ns = time.perf_counter_ns
else:
    # python 3
    def time_ns():
        return int(time.time() * 1000000000.)

    def perf_counter_ns():
        return int(time.perf_counter() * 1000000000.)


#
# Key Types
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


class _OidOidKeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _OidKeysMixin.new_key(secure=secure), _OidKeysMixin.new_key(secure=secure)

    def _serialize_key(self, keys):
        assert type(keys) == tuple
        assert len(keys) == 2
        key1, key2 = keys
        assert type(key1) in six.integer_types
        assert key1 >= 0 and key1 <= _OidKeysMixin.MAX_OID
        assert type(key2) in six.integer_types
        assert key2 >= 0 and key2 <= _OidKeysMixin.MAX_OID
        return struct.pack('>QQ', key1, key2)

    def _deserialize_key(self, data):
        assert len(data) == 16
        return struct.unpack('>QQ', data)


class _Oid3KeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _OidKeysMixin.new_key(secure=secure), _OidKeysMixin.new_key(secure=secure), _OidKeysMixin.new_key(
            secure=secure)

    def _serialize_key(self, keys):
        assert type(keys) == tuple
        assert len(keys) == 3
        key1, key2, key3 = keys
        assert type(key1) in six.integer_types
        assert key1 >= 0 and key1 <= _OidKeysMixin.MAX_OID
        assert type(key2) in six.integer_types
        assert key2 >= 0 and key2 <= _OidKeysMixin.MAX_OID
        assert type(key3) in six.integer_types
        assert key3 >= 0 and key3 <= _OidKeysMixin.MAX_OID
        return struct.pack('>QQQ', key1, key2, key3)

    def _deserialize_key(self, data):
        assert len(data) == 24
        return struct.unpack('>QQQ', data)


class _OidTimestampKeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _OidKeysMixin.new_key(secure=secure), 0

    def _serialize_key(self, keys):
        assert type(keys) == tuple
        assert len(keys) == 2
        key1, key2 = keys
        assert type(key1) in six.integer_types
        assert key1 >= 0 and key1 <= _OidKeysMixin.MAX_OID
        assert isinstance(key2, np.datetime64)
        return struct.pack('>Q', key1) + key2.tobytes()

    def _deserialize_key(self, data):
        assert len(data) == 16
        key1, key2 = struct.unpack('>QQ', data)
        key2 = np.datetime64(key2, 'ns')
        return key1, key2


class _OidTimestampStringKeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _OidKeysMixin.new_key(secure=secure), 0, ''

    def _serialize_key(self, keys):
        assert type(keys) == tuple
        assert len(keys) == 3
        key1, key2, key3 = keys
        assert type(key1) in six.integer_types
        assert key1 >= 0 and key1 <= _OidKeysMixin.MAX_OID
        assert isinstance(key2, np.datetime64)
        assert type(key3) == six.text_type
        return struct.pack('>Q', key1) + key2.tobytes() + key3.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) >= 16

        oid, ts = struct.unpack('>QQ', data[:16])
        ts = np.datetime64(ts, 'ns')
        if len(data) > 16:
            s = data[16:]
        else:
            s = ''
        return oid, ts, s


class _OidStringKeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _OidKeysMixin.new_key(secure=secure), ''

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) in six.integer_types
        assert type(key2) == six.text_type

        return struct.pack('>Q', key1) + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) >= 8
        oid = struct.unpack('>Q', data[:8])
        if len(data) > 8:
            data = data[8:]
            s = data.decode('utf8')
        else:
            s = ''
        return oid, s


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
        assert key is None or type(key) == six.text_type

        if key:
            return key.encode('utf8')
        else:
            return b''

    def _deserialize_key(self, data):
        assert data is None or type(data) == six.binary_type

        if data:
            return data.decode('utf8')
        else:
            return None


class _UuidKeysMixin(object):
    @staticmethod
    def new_key():
        # https: // docs.python.org / 3 / library / uuid.html  # uuid.uuid4
        # return uuid.UUID(bytes=os.urandom(16))
        return uuid.uuid4()

    def _serialize_key(self, key):
        assert key is None or isinstance(key, uuid.UUID)

        # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).
        # https://docs.python.org/3/library/uuid.html#uuid.UUID.bytes
        if key:
            return key.bytes
        else:
            return b''

    def _deserialize_key(self, data):
        assert data is None or type(data) == six.binary_type

        if data:
            return uuid.UUID(bytes=data)
        else:
            return None


class _UuidUuidKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert isinstance(key1, uuid.UUID)
        assert isinstance(key2, uuid.UUID)

        return key1.bytes + key2.bytes

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 32

        data1, data2 = data[0:16], data[16:32]
        return uuid.UUID(bytes=data1), uuid.UUID(bytes=data2)


class _UuidStringKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert isinstance(key1, uuid.UUID)
        assert type(key2) == six.text_type

        # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).
        # https://docs.python.org/3/library/uuid.html#uuid.UUID.bytes
        return key1.bytes + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 16
        data1, data2 = data[:16], data[16:]

        return uuid.UUID(bytes=data1), data2.decode('utf8')


class _SlotUuidKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) in six.integer_types
        assert key1 >= 0 and key1 < 2**16
        assert isinstance(key2, uuid.UUID)

        return struct.pack('>H', key1) + key2.bytes

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == (2 + 16)
        data1, data2 = data[:2], data[2:]

        return struct.unpack('>H', data1)[0], uuid.UUID(bytes=data2)


class _Bytes32KeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(32)

    def _serialize_key(self, key):
        assert key is None or type(key) == six.binary_type
        if key:
            return key
        else:
            return b'\x00' * 32

    def _deserialize_key(self, data):
        assert data is None or type(data) == six.binary_type
        if data:
            return data
        else:
            return None


class _Bytes32Bytes32KeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) == six.binary_type
        assert len(key1) == 32

        assert type(key2) == six.binary_type
        assert len(key2) == 32

        return key1 + key2

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 64

        data1, data2 = data[0:32], data[32:64]
        return data1, data2


class _Bytes32StringKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) == six.binary_type
        assert len(key1) == 32

        assert type(key2) == six.text_type

        return key1 + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 32
        data1, data2 = data[:32], data[32:]

        return data1, data2.decode('utf8')


#
# Value Types
#


class _StringValuesMixin(object):
    def _serialize_value(self, value):
        if value:
            return value.encode('utf8')
        else:
            return b''

    def _deserialize_value(self, data):
        if data:
            return data.decode('utf8')
        else:
            return None


class _StringSetValuesMixin(object):
    def _serialize_value(self, value_set):
        assert type(value_set) == set
        return b'\0'.join([value.encode('utf8') for value in value_set])

    def _deserialize_value(self, data):
        assert type(data) == bytes
        return set([d.decode('utf8') for d in data.split('\0')])


class _OidValuesMixin(object):
    def _serialize_value(self, value):
        return struct.pack('>Q', value)

    def _deserialize_value(self, data):
        return struct.unpack('>Q', data)[0]


class _OidSetValuesMixin(object):
    def _serialize_value(self, value_set):
        assert type(value_set) == set
        return b''.join([struct.pack('>Q', value) for value in value_set])

    def _deserialize_value(self, data):
        VLEN = 8
        assert len(data) % VLEN == 0
        cnt = len(data) / VLEN
        return set([struct.unpack('>Q', data[i:i + VLEN])[0] for i in range(0, cnt, VLEN)])


class _UuidValuesMixin(object):
    def _serialize_value(self, value):
        if value:
            return value.bytes
        else:
            return b''

    def _deserialize_value(self, data):
        if data:
            return uuid.UUID(bytes=data)
        else:
            return None


class _UuidSetValuesMixin(object):
    def _serialize_value(self, value_set):
        assert type(value_set) == set
        return b''.join([value.bytes for value in value_set])

    def _deserialize_value(self, data):
        VLEN = 16
        assert len(data) % VLEN == 0
        cnt = len(data) / VLEN
        return set([uuid.UUID(bytes=data[i:i + VLEN]) for i in range(0, cnt, VLEN)])


class _JsonValuesMixin(object):
    def __init__(self, marshal=None, unmarshal=None):
        self._marshal = None
        if marshal:
            self._marshal = marshal
        else:
            if hasattr(self, '_zlmdb_marshal'):
                self._marshal = self._zlmdb_marshal
        assert self._marshal

        self._unmarshal = None
        if unmarshal:
            self._unmarshal = unmarshal
        else:
            if hasattr(self, '_zlmdb_unmarshal'):
                self._unmarshal = self._zlmdb_unmarshal
        assert self._unmarshal

    def _serialize_value(self, value):
        return json.dumps(
            self._marshal(value), separators=(',', ':'), ensure_ascii=False, sort_keys=False).encode('utf8')

    def _deserialize_value(self, data):
        return self._unmarshal(json.loads(data.decode('utf8')))


class _CborValuesMixin(object):
    def __init__(self, marshal=None, unmarshal=None):
        self._marshal = None
        if marshal:
            self._marshal = marshal
        else:
            if hasattr(self, '_zlmdb_marshal'):
                self._marshal = self._zlmdb_marshal
        assert self._marshal

        self._unmarshal = None
        if unmarshal:
            self._unmarshal = unmarshal
        else:
            if hasattr(self, '_zlmdb_unmarshal'):
                self._unmarshal = self._zlmdb_unmarshal
        assert self._unmarshal

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
        self._build = build or self._zlmdb_build
        self._cast = cast or self._zlmdb_cast

    def _serialize_value(self, value):
        builder = flatbuffers.Builder(0)
        obj = self._build(value, builder)
        builder.Finish(obj)
        buf = builder.Output()
        return bytes(buf)

    def _deserialize_value(self, data):
        return self._cast(data)
