import sys
import os
import pytest

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User, Schema2
else:
    from _schema_py2 import User, Schema2


@pytest.fixture(scope='module')
def testset1():
    users = []
    for i in range(1000):
        user = User.create_test_user(i)
        users.append(user)
    return users


def test_transaction():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema2()

        with schema.open(dbpath) as db:
            with db.begin() as txn:
                print('transaction open', txn.id())
            print('transaction committed')
        print('database closed')


def test_save_load():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema2()

        user = User.create_test_user()

        with schema.open(dbpath) as db:

            with db.begin(write=True) as txn:

                schema.users[txn, user.oid] = user
                print('user saved')

                _user = schema.users[txn, user.oid]
                assert _user
                assert user == _user
                print('user loaded')

            print('transaction committed')

        print('database closed')


def test_save_load_many_1(testset1):
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema2()

        with schema.open(dbpath) as db:

            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

                cnt = schema.users.count(txn)
                print('user saved:', cnt)
                assert cnt == len(testset1)

            with db.begin() as txn:
                cnt = schema.users.count(txn)
                assert cnt == len(testset1)

        with schema.open(dbpath) as db:
            with db.begin() as txn:
                cnt = schema.users.count(txn)
                assert cnt == len(testset1)


def test_save_load_many_2(testset1):
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema2()

        oids = []

        with schema.open(dbpath) as db:

            # write records in a 1st transaction
            with db.begin(write=True) as txn:

                c = 0
                for user in testset1:
                    schema.users[txn, user.oid] = user
                    oids.append(user.oid)
                    c += 1
                assert c == len(testset1)
                print('[1] successfully stored {} records'.format(c))

                # in the same transaction, read back records
                c = 0
                for oid in oids:
                    user = schema.users[txn, oid]
                    if user:
                        c += 1
                assert c == len(testset1)
                print('[1] successfully loaded {} records'.format(c))

            # in a new transaction, read back records
            c = 0
            with db.begin() as txn:
                for oid in oids:
                    user = schema.users[txn, oid]
                    if user:
                        c += 1
            assert c == len(testset1)
            print('[2] successfully loaded {} records'.format(c))

        # in a new database environment (and hence new transaction), read back records
        with schema.open(dbpath) as db:

            with db.begin() as txn:

                count = schema.users.count(txn)
                assert count == len(testset1)
                print('total records:', count)

                c = 0
                for oid in oids:
                    user = schema.users[txn, oid]
                    if user:
                        c += 1
                assert c == len(testset1)
                print('[3] successfully loaded {} records'.format(c))
