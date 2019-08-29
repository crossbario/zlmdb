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
import binascii
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


CHARSET = u'345679ACEFGHJKLMNPQRSTUVWXY'
"""
Charset from which to generate random key IDs.

.. note::

    We take out the following 9 chars (leaving 27), because there is visual ambiguity: 0/O/D, 1/I, 8/B, 2/Z.
"""

CHAR_GROUPS = 4
CHARS_PER_GROUP = 6
GROUP_SEP = u'-'


def _random_string():
    """
    Generate a globally unique serial / product code of the form ``u'YRAC-EL4X-FQQE-AW4T-WNUV-VN6T'``.
    The generated value is cryptographically strong and has (at least) 114 bits of entropy.

    :return: new random string key
    """
    rng = random.SystemRandom()
    token_value = u''.join(rng.choice(CHARSET) for _ in range(CHAR_GROUPS * CHARS_PER_GROUP))
    if CHARS_PER_GROUP > 1:
        return GROUP_SEP.join(map(u''.join, zip(*[iter(token_value)] * CHARS_PER_GROUP)))
    else:
        return token_value


def dt_to_bytes(dt):
    """
    Serialize a timestamp in big-endian byte order.

    :param dt: Timestamp to serialize.
    :return: Serialized bytes.
    """
    assert isinstance(dt, np.datetime64)

    data = bytearray(dt.tobytes())
    data.reverse()
    return bytes(data)


def bytes_to_dt(data):
    """
    Deserialize a timestamp from big-endian byte order data.

    :param data: Data to deserialize.
    :return: Deserialized timestamp.
    """
    assert type(data) == six.binary_type

    data = bytearray(data)
    data.reverse()
    dt = np.frombuffer(bytes(data), dtype='datetime64[ns]')[0]
    return dt


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
        key1, key2 = struct.unpack('>Q>Q', data)
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
        assert len(data) > 16

        oid, ts = struct.unpack('>Q>Q', data[:16])
        ts = np.datetime64(ts, 'ns')
        s = data[16:]
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
        assert len(data) > 8
        oid = struct.unpack('>Q', data[:8])[0]
        data = data[8:]
        s = data.decode('utf8')
        return oid, s


class _StringOidKeysMixin(object):
    @staticmethod
    def new_key(secure=False):
        return _random_string(), _OidKeysMixin.new_key(secure=secure)

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) == six.text_type
        assert type(key2) in six.integer_types

        return key1.encode('utf8') + struct.pack('>Q', key2)

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 8
        oid = struct.unpack('>Q', data[-8:])[0]
        data = data[0:8]
        s = data.decode('utf8')
        return s, oid


class _StringKeysMixin(object):
    @staticmethod
    def new_key():
        return _random_string()

    def _serialize_key(self, key):
        assert type(key) == six.text_type

        return key.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type

        return data.decode('utf8')


class _UuidKeysMixin(object):
    @staticmethod
    def new_key():
        # https: // docs.python.org / 3 / library / uuid.html  # uuid.uuid4
        # return uuid.UUID(bytes=os.urandom(16))
        return uuid.uuid4()

    def _serialize_key(self, key):
        assert isinstance(key, uuid.UUID)

        # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).
        # https://docs.python.org/3/library/uuid.html#uuid.UUID.bytes
        return key.bytes

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type

        return uuid.UUID(bytes=data)


class _UuidUuidKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = uuid.UUID(bytes=b'\x00' * 16)
        if key2 is None:
            key2 = uuid.UUID(bytes=b'\x00' * 16)

        assert isinstance(key1, uuid.UUID)
        assert isinstance(key2, uuid.UUID)

        return key1.bytes + key2.bytes

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 32

        data1, data2 = data[0:16], data[16:32]
        return uuid.UUID(bytes=data1), uuid.UUID(bytes=data2)


class _TimestampKeysMixin(object):
    @staticmethod
    def new_key():
        return np.datetime64(time.time_ns(), 'ns')

    def _serialize_key(self, key1):
        assert isinstance(key1, np.datetime64)

        return dt_to_bytes(key1)

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 8

        return bytes_to_dt(data[0:8])


class _TimestampUuidKeysMixin(object):
    @staticmethod
    def new_key():
        return np.datetime64(time.time_ns(), 'ns'), uuid.uuid4()

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = np.datetime64(0, 'ns')
        if key2 is None:
            key2 = uuid.UUID(bytes=b'\x00' * 16)

        assert isinstance(key1, np.datetime64)
        assert isinstance(key2, uuid.UUID)

        return dt_to_bytes(key1) + key2.bytes

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 24

        data1, data2 = data[0:8], data[8:24]

        key1 = bytes_to_dt(data1)
        key2 = uuid.UUID(bytes=data2)
        return key1, key2


class _TimestampUuidStringKeysMixin(object):
    @staticmethod
    def new_key():
        return np.datetime64(time.time_ns(), 'ns'), uuid.uuid4(), ''

    def _serialize_key(self, key1_key2_key3):
        assert type(key1_key2_key3) == tuple and len(key1_key2_key3) == 3
        key1, key2, key3 = key1_key2_key3

        if key1 is None:
            key1 = np.datetime64(0, 'ns')
        if key2 is None:
            key2 = uuid.UUID(bytes=b'\x00' * 16)
        if key3 is None:
            key3 = u''

        assert isinstance(key1, np.datetime64)
        assert isinstance(key2, uuid.UUID)
        assert type(key3) == six.text_type

        return dt_to_bytes(key1) + key2.bytes + key3.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) >= 24

        data1, data2, data3 = data[0:8], data[8:24], data[24:]

        key1 = bytes_to_dt(data1)
        key2 = uuid.UUID(bytes=data2)
        key3 = data3.decode('utf8') if data3 else u''
        return key1, key2, key3


class _TimestampBytes32KeysMixin(object):
    @staticmethod
    def new_key():
        return np.datetime64(time.time_ns(), 'ns'), os.urandom(32)

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = np.datetime64(0, 'ns')
        if key2 is None:
            key2 = b'\x00' * 32

        assert isinstance(key1, np.datetime64)
        assert isinstance(key2, six.binary_type)
        assert isinstance(key2, six.binary_type) and len(key2) == 32

        return dt_to_bytes(key1) + key2

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type, 'data must be binary, but got {}'.format(type(data))
        assert len(data) == 40, 'data must have len 40, but got {}'.format(len(data))

        data1, data2 = data[0:8], data[8:40]

        key1 = bytes_to_dt(data1)
        key2 = data2
        return key1, key2


class _TimestampStringKeysMixin(object):
    @staticmethod
    def new_key():
        return np.datetime64(time.time_ns(), 'ns'), _StringKeysMixin.new_key()

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = np.datetime64(0, 'ns')
        if key2 is None:
            key2 = u''

        assert isinstance(key1, np.datetime64)
        assert type(key2) == six.text_type

        return dt_to_bytes(key1) + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 8

        data1, data2 = data[0:8], data[8:]
        key1 = bytes_to_dt(data1)
        key2 = data2.decode('utf8')
        return key1, key2


class _StringTimestampKeysMixin(object):
    @staticmethod
    def new_key():
        return _StringKeysMixin.new_key(), np.datetime64(time.time_ns(), 'ns')

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = u''
        if key2 is None:
            key2 = np.datetime64(0, 'ns')

        assert type(key1) == six.text_type
        assert isinstance(key2, np.datetime64)

        return key1.encode('utf8') + dt_to_bytes(key2)

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 8

        slen = len(data) - 8
        data1, data2 = data[0:slen], data[slen:]
        key1 = data1.decode('utf8')
        key2 = bytes_to_dt(data2)
        return key1, key2


class _UuidTimestampKeysMixin(object):
    @staticmethod
    def new_key():
        return uuid.uuid4(), np.datetime64(time.time_ns(), 'ns')

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = uuid.UUID(bytes=b'\x00' * 16)
        if key2 is None:
            key2 = np.datetime64(0, 'ns')

        assert isinstance(key1, uuid.UUID)
        assert isinstance(key2, np.datetime64)

        return key1.bytes + dt_to_bytes(key2)

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 24

        data1, data2 = data[0:16], data[16:24]
        key1 = uuid.UUID(bytes=data1)
        key2 = bytes_to_dt(data2)
        return key1, key2


class _UuidStringKeysMixin(object):
    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        if key1 is None:
            key1 = uuid.UUID(bytes=b'\x00' * 16)
        if key2 is None:
            key2 = u''

        assert isinstance(key1, uuid.UUID), 'key1 must be of type UUID, but was {}'.format(type(key1))
        assert type(key2) == six.text_type, 'key2 must be of type string, but was {}'.format(type(key2))

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
        assert type(key) == six.binary_type, 'key must be bytes[32], was "{}"'.format(key)
        assert len(key) == 32

        return key

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type, 'data must be bytes[32], was "{}"'.format(data)
        assert len(data) == 32

        return data


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
        assert len(key2) > 0

        return key1 + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 32

        data1, data2 = data[:32], data[32:]
        return data1, data2.decode('utf8')


class _Bytes20KeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(20)

    def _serialize_key(self, key):
        assert type(key) == six.binary_type and len(key) == 20, 'key must be bytes[20], was "{}"'.format(key)

        return key

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type and len(data) == 20, 'data must be bytes[20], was "{}"'.format(data)

        return data


class _Bytes16KeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(16)

    def _serialize_key(self, key):
        assert type(key) == six.binary_type and len(key) == 16, 'key must be bytes[16], was "{}"'.format(key)

        return key

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type and len(data) == 16, 'data must be bytes[16], was "{}"'.format(data)

        return data


class _Bytes20Bytes20KeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(20), os.urandom(20)

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) == six.binary_type
        assert len(key1) == 20

        assert type(key2) == six.binary_type
        assert len(key2) == 20

        return key1 + key2

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) == 40

        data1, data2 = data[0:20], data[20:40]
        return data1, data2


class _Bytes20StringKeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(20), binascii.b2a_base64(os.urandom(8)).decode().strip()

    def _serialize_key(self, key1_key2):
        assert type(key1_key2) == tuple and len(key1_key2) == 2
        key1, key2 = key1_key2

        assert type(key1) == six.binary_type
        assert len(key1) == 20

        assert type(key2) == six.text_type
        assert len(key2) > 0

        return key1 + key2.encode('utf8')

    def _deserialize_key(self, data):
        assert type(data) == six.binary_type
        assert len(data) > 20
        data1, data2 = data[:20], data[20:]

        return data1, data2.decode('utf8')


class _Bytes20TimestampKeysMixin(object):
    @staticmethod
    def new_key():
        return os.urandom(20), np.datetime64(time.time_ns(), 'ns')

    def _serialize_key(self, keys):
        assert type(keys) == tuple, 'keys in {}._serialize_key must be a tuple, was: "{}"'.format(
            self.__class__.__name__, keys)
        assert len(keys) == 2
        key1, key2 = keys

        if not key1:
            key1 = b'\x00' * 20

        assert key1 is None or (type(key1) == six.binary_type and len(key1) == 20)
        assert isinstance(key2, np.datetime64)

        return key1 + dt_to_bytes(key2)

    def _deserialize_key(self, data):
        assert data is None or (type(data) == six.binary_type and len(data) == 28)

        if data:
            key1 = data[:20]
            key2 = bytes_to_dt(data[20:])
        else:
            key1 = b'\x00' * 20
            key2 = np.datetime64(0, 'ns')

        return key1, key2


#
# Value Types
#


class _StringValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or type(value) == six.text_type

        if value is not None:
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
        for v in value_set:
            assert v is None or type(v) == six.text_type

        return b'\0'.join([(value.encode('utf8') if value else b'') for value in value_set])

    def _deserialize_value(self, data):
        assert type(data) == bytes
        return set([(d.decode('utf8') if d else None) for d in data.split('\0')])


class _OidValuesMixin(object):
    def _serialize_value(self, value):
        assert type(value) in six.integer_types
        assert value >= 0 and value <= _OidKeysMixin.MAX_OID

        return struct.pack('>Q', value)

    def _deserialize_value(self, data):
        return struct.unpack('>Q', data)[0]


class _OidSetValuesMixin(object):
    def _serialize_value(self, value_set):
        assert type(value_set) == set
        for value in value_set:
            assert value >= 0 and value <= _OidKeysMixin.MAX_OID
        return b''.join([struct.pack('>Q', value) for value in value_set])

    def _deserialize_value(self, data):
        VLEN = 8
        assert len(data) % VLEN == 0
        cnt = len(data) // VLEN
        return set([struct.unpack('>Q', data[i:i + VLEN])[0] for i in range(0, cnt, VLEN)])


class _UuidValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or isinstance(value, uuid.UUID)

        # The UUID as a 16-byte string (containing the six integer fields in big-endian byte order).
        # https://docs.python.org/3/library/uuid.html#uuid.UUID.bytes
        if value:
            return value.bytes
        else:
            return b'\x00' * 16

    def _deserialize_value(self, data):
        assert data is None or type(data) == six.binary_type

        if data:
            return uuid.UUID(bytes=data)
        else:
            return uuid.UUID(bytes=b'\x00' * 16)


class _TimestampValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or isinstance(value, np.datetime64)

        if value:
            return dt_to_bytes(value)
        else:
            return b'\x00' * 8

    def _deserialize_value(self, data):
        assert data is None or type(data) == six.binary_type and len(data) == 8

        if data:
            return bytes_to_dt(data)
        else:
            return None


class _Bytes32ValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or (type(value) == six.binary_type and len(value) == 32)
        if value:
            return value
        else:
            return b'\x00' * 32

    def _deserialize_value(self, data):
        assert data is None or (type(data) == six.binary_type and len(data) == 32)
        if data:
            return data
        else:
            return None


class _Bytes20ValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or (type(value) == six.binary_type and len(value) == 20)
        if value:
            return value
        else:
            return b'\x00' * 20

    def _deserialize_value(self, data):
        assert data is None or (type(data) == six.binary_type and len(data) == 20)
        if data:
            return data
        else:
            return None


class _Bytes20TimestampValuesMixin(object):
    def _serialize_value(self, values):
        assert type(values) == tuple
        assert len(values) == 2
        value1, value2 = values

        if not value1:
            value1 = b'\x00' * 20

        assert value1 is None or (type(value1) == six.binary_type and len(value1) == 20)
        assert isinstance(value2, np.datetime64)

        return value1 + dt_to_bytes(value2)

    def _deserialize_value(self, data):
        assert data is None or (type(data) == six.binary_type and len(data) == 28)

        if data:
            value1 = data[:20]
            value2 = bytes_to_dt(data[20:])
        else:
            value1 = b'\x00' * 20
            value2 = np.datetime64(0, 'ns')

        return value1, value2


class _Bytes16ValuesMixin(object):
    def _serialize_value(self, value):
        assert value is None or (type(value) == six.binary_type and len(value) == 16)
        if value:
            return value
        else:
            return b'\x00' * 16

    def _deserialize_value(self, data):
        assert data is None or (type(data) == six.binary_type and len(data) == 16)
        if data:
            return data
        else:
            return None


class _UuidSetValuesMixin(object):
    def _serialize_value(self, value_set):
        assert type(value_set) == set
        return b''.join([value.bytes for value in value_set])

    def _deserialize_value(self, data):
        VLEN = 16
        assert len(data) % VLEN == 0
        cnt = len(data) // VLEN
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
