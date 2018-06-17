import os
import sys
import timeit
import random
import uuid
import datetime
import platform

import humanize

from zlmdb import _pmap

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User
else:
    from _schema_py2 import User

from _schema_fbs import User as UserFbs

_TEST = {
    'oid': 0,
    'uuid': None,
    'bytes': 0,
    'serializer': None
}


def _serializer_run():
    serialize = _TEST['serializer']._serialize_value
    user = UserFbs.create_test_user()
    data = serialize(user)
    _TEST['bytes'] += len(data)


def _serialization_speed(serializer):
    N = 10
    M = 10000

    samples = []

    print('running on:')
    print(sys.version)
    print(platform.uname())

    _TEST['oid'] = 0
    _TEST['uuid'] = uuid.uuid4()
    _TEST['bytes'] = 0
    _TEST['bytes'] = 0
    _TEST['serializer'] = serializer

    for i in range(N):
        secs = timeit.timeit(_serializer_run, number=M)
        ops = round(float(M) / secs, 1)
        samples.append(ops)
        print('{} objects/sec {}'.format(ops, humanize.naturalsize(_TEST['bytes'])))

    ops_max = max(samples)
    bytes_per_obj = float(_TEST['bytes']) / float(N * M)
    print('{} objects/sec max, {} bytes total, {} bytes/obj'.format(ops_max,
                                                                    humanize.naturalsize(_TEST['bytes']),
                                                                    humanize.naturalsize(bytes_per_obj)))

    return ops_max, _TEST['bytes']


def test_json_serialization_speed():
    ser = _pmap._JsonValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    ops_max, total = _serialization_speed(ser)
    # cpy36: 19564.6 objects/sec max, 135456153 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_cbor_serialization_speed():
    ser = _pmap._CborValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    ops_max, total = _serialization_speed(ser)
    # cpy36: 7787.4 objects/sec max, 97815364 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_pickle_serialization_speed():
    ser = _pmap._PickleValuesMixin()
    ops_max, total = _serialization_speed(ser)
    # cpy36: 33586.0 objects/sec max, 137738869 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_flatbuffer_serialization_speed():
    ser = _pmap._FlatBuffersValuesMixin(build=UserFbs.build, cast=UserFbs.cast)
    ops_max, total = _serialization_speed(ser)
    assert ops_max > 1000
    assert total > 1000000


if __name__ == '__main__':
    sers = []

    ser = _pmap._JsonValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    sers.append(ser)

    ser = _pmap._CborValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    sers.append(ser)

    ser = _pmap._PickleValuesMixin()
    sers.append(ser)

    ser = _pmap._FlatBuffersValuesMixin(build=UserFbs.build, cast=UserFbs.cast)
    sers.append(ser)

    for ser in sers:
        print(_serialization_speed(ser))
