import random
import os
import shutil
import lmdb
import struct
import pytest

DBNAME = '.test-db1'


@pytest.fixture(scope='function')
def dbenv():
    if os.path.exists(DBNAME):
        if os.path.isdir(DBNAME):
            shutil.rmtree(DBNAME)
        else:
            os.remove(DBNAME)
    env = lmdb.open(DBNAME)
    return env


def test_create(dbenv):
    assert isinstance(dbenv, lmdb.Environment)
    with dbenv.begin() as txn:
        assert txn.id() == 0


def test_insert(dbenv):
    n = 100
    total1 = 0

    with dbenv.begin(write=True) as txn:
        for i in range(n):
            key = 'key-{}'.format(i).encode('utf8')
            # value = os.urandom(16)
            value = random.randint(0, 2 ** 32 - 1)
            total1 += value
            data = struct.pack('<L', value)
            txn.put(key, data)

    with dbenv.begin() as txn:

        cursor = txn.cursor()
        assert cursor.first()

        count = 1
        total2 = struct.unpack('<L', cursor.value())[0]

        while cursor.next():
            count += 1
            total2 += struct.unpack('<L', cursor.value())[0]

        assert count == n
        assert total1 == total2


def test_delete(dbenv):
    n = 100

    with dbenv.begin(write=True) as txn:
        for i in range(n):
            key = 'key-{}'.format(i).encode('utf8')
            value = os.urandom(16)
            txn.put(key, value)

    with dbenv.begin(write=True) as txn:
        for i in range(n):
            key = 'key-{}'.format(i).encode('utf8')
            assert txn.delete(key)

    with dbenv.begin() as txn:
        cursor = txn.cursor()
        assert not cursor.first()
