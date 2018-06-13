import sys
import os
import uuid
import datetime
import random
import pytest

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from user_typed import User
else:
    from user import User


dbfile = '.testdb'

zlmdb.Database.scratch(dbfile)


def create_test_user(oid=None):
    user = User()
    user.oid = oid or random.randint(0, 2**64-1)
    user.name = 'Test {}'.format(user.oid)
    user.authid = 'test-{}'.format(user.oid)
    user.uuid = uuid.uuid4()
    user.email = '{}@example.com'.format(user.authid)
    user.birthday = datetime.date(1950, 12, 24)
    user.is_friendly = True
    user.tags = ['geek', 'sudoko', 'yellow']
    for j in range(10):
        user.ratings['test-rating-{}'.format(j)] = random.random()
    return user


@pytest.fixture(scope='module')
def schema1():
    schema = zlmdb.Schema()
    schema.register(1, 'users', zlmdb.MapOidPickle)
    return schema


@pytest.fixture(scope='module')
def testset1():
    N = 1000
    users = []
    for i in range(N):
        user = create_test_user()
        users.append(user)
    return users


class UsersSchema(object):
    """
    User database schema.
    """

    users: zlmdb.MapOidPickle

    def __init__(self, txn):
        self.users = zlmdb.MapOidPickle(1, txn)


def test_basic(testset1):
    N = 1000
    oids = []

    with zlmdb.Database(dbfile) as db:

        # write records in a 1st transaction
        with db.begin(write=True) as txn:

            schema = UsersSchema(txn)

            c = 0
            for user in testset1:
                schema.users[user.oid] = user
                oids.append(user.oid)
                c += 1
            assert c == N
            print('[1] successfully stored {} records'.format(c))

            # in the same transaction, read back records
            c = 0
            for oid in oids:
                user = schema.users[oid]
                if user:
                    c += 1
            assert c == N
            print('[1] successfully loaded {} records'.format(c))

        # in a new transaction, read back records
        c = 0
        with db.begin() as txn:

            schema = UsersSchema(txn)

            for oid in oids:
                user = schema.users[oid]
                if user:
                    c += 1
        assert c == N
        print('[2] successfully loaded {} records'.format(c))

    # in a new database environment (and hence new transaction), read back records
    with zlmdb.Database(dbfile) as db:
        with db.begin() as txn:
            schema = UsersSchema(txn)

            count = schema.users.count()
            assert count == N
            print('total records:', count)

            c = 0
            for oid in oids:
                user = schema.users[oid]
                if user:
                    c += 1
            assert c == N
            print('[3] successfully loaded {} records'.format(c))


def test_basic2(testset1):
    oids = [user.oid for user in testset1]

    with zlmdb.Database(dbfile) as db:
        with db.begin() as txn:
            schema = UsersSchema(txn)

            count = schema.users.count()
            print('total records:', count)
            assert count == len(oids)
