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


def _create_test_user():
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


_TEST = {
    'bytes': 0,
    'serializer': None
}


def _serializer_run():
    user = _create_test_user()
    data = _TEST['serializer']._serialize_value(user.marshal())
    _TEST['bytes'] += len(data)


def _serialization_speed(serializer):
    _TEST['serializer'] = serializer
    N = 20
    M = 10000

    samples = []

    print('running on:')
    print(sys.version)
    print(platform.uname())
    _TEST['bytes'] = 0
    for i in range(N):
        secs = timeit.timeit(_serializer_run, number=M)
        ops = round(float(M) / secs, 1)
        samples.append(ops)
        print('{} objects/sec {}'.format(ops, humanize.naturalsize(_TEST['bytes'])))

    ops_max = max(samples)
    print('{} objects/sec max, {} bytes total'.format(ops_max, humanize.naturalsize(_TEST['bytes'])))

    return ops_max, _TEST['bytes']


def test_json_serialization_speed():
    s = _JsonValuesMixin()
    ops_max, total = _serialization_speed(s)
    # cpy36: 19564.6 objects/sec max, 135456153 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_cbor_serialization_speed():
    s = _CborValuesMixin()
    ops_max, total = _serialization_speed(s)
    # cpy36: 7787.4 objects/sec max, 97815364 bytes total
    assert ops_max > 1000
    assert total > 1000000


def test_pickle_serialization_speed():
    s = _PickleValuesMixin()
    ops_max, total = _serialization_speed(s)
    # cpy36: 33586.0 objects/sec max, 137738869 bytes total
    assert ops_max > 1000
    assert total > 1000000


if __name__ == '__main__':
    for ser in [_JsonValuesMixin(), _CborValuesMixin(), _PickleValuesMixin()]:
        print(_serialization_speed(ser))
