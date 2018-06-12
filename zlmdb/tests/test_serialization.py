import sys
import timeit
import random
import uuid
import datetime
import platform

import humanize

from zlmdb._pmap import _JsonValuesMixin, _CborValuesMixin, _PickleValuesMixin

if sys.version_info >= (3, 6):
    from user_typed import User
else:
    from user import User


_TEST = {
    'oid': 0,
    'uuid': None,
    'bytes': 0,
    'serializer': None
}


def _create_test_user1():
    user = User()
    user.oid = random.randint(0, 2**64-1)
    user.name = 'Test {}'.format(user.oid)
    user.authid = 'test-{}'.format(user.oid)
    user.uuid = uuid.uuid4()
    user.email = '{}@example.com'.format(user.authid)
    user.birthday = datetime.date(1950, 12, 24)
    user.is_friendly = True
    user.tags = ['relaxed', 'beerfan']
    for j in range(10):
        user.ratings['test-rating-{}'.format(j)] = random.random()
    return user


def _create_test_user2():
    _TEST['oid'] += 1
    user = User()
    user.oid = _TEST['oid']
    user.name = 'Test {}'.format(user.oid)
    user.authid = 'test-{}'.format(user.oid)
    user.uuid = _TEST['uuid']
    user.email = '{}@example.com'.format(user.authid)
    user.birthday = datetime.date(1950, 12, 24)
    user.is_friendly = True
    user.tags = ['relaxed', 'beerfan']
    for j in range(10):
        user.ratings['test-rating-{}'.format(j)] = float(j) / 10.
    return user


def _serializer_run():
    user = _create_test_user1()
    # user = _create_test_user2()
    data = _TEST['serializer']._serialize_value(user)
    _TEST['bytes'] += len(data)


def _serialization_speed(serializer):
    N = 20
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
    print('{} objects/sec max, {} bytes total'.format(ops_max, humanize.naturalsize(_TEST['bytes'])))

    return ops_max, _TEST['bytes']


def test_json_serialization_speed():
    ser = _JsonValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    ops_max, total = _serialization_speed(ser)
    # cpy36: 19564.6 objects/sec max, 135456153 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_cbor_serialization_speed():
    ser = _CborValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    ops_max, total = _serialization_speed(ser)
    # cpy36: 7787.4 objects/sec max, 97815364 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_pickle_serialization_speed():
    ser = _PickleValuesMixin()
    ops_max, total = _serialization_speed(ser)
    # cpy36: 33586.0 objects/sec max, 137738869 bytes total
    assert ops_max > 1000
    assert total > 1000000


if __name__ == '__main__':
    sers = []

    ser = _JsonValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    sers.append(ser)

    ser = _CborValuesMixin(marshal=User.marshal, unmarshal=User.parse)
    sers.append(ser)

    ser = _PickleValuesMixin()
    sers.append(ser)

    for ser in sers:
        print(_serialization_speed(ser))
