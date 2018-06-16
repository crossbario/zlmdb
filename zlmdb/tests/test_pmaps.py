import os
import sys
import pytest

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User, Schema1, Schema3, Schema4
else:
    from _schema_py2 import User, Schema1, Schema3, Schema4


@pytest.fixture(scope='function')
def dbfile():
    _dbfile = '.testdb'
    zlmdb.Database.scratch(_dbfile)
    return _dbfile


@pytest.fixture(scope='module')
def testset1():
    users = []
    for i in range(1000):
        user = User.create_test_user(i)
        users.append(user)
    return users


def test_truncate_table(dbfile):
    schema = Schema1()

    stats = zlmdb.TransactionStats()
    tabs = [
        schema.tab_oid_json, schema.tab_str_json, schema.tab_uuid_json,
        schema.tab_oid_cbor, schema.tab_str_cbor, schema.tab_uuid_cbor,
        schema.tab_oid_pickle, schema.tab_str_pickle, schema.tab_uuid_pickle,
    ]

    with schema.open(dbfile) as db:
        with db.begin(write=True, stats=stats) as txn:
            for tab in tabs:
                tab.truncate(txn)

    print(stats.puts)
    print(stats.dels)


def test_count_all(dbfile, testset1):
    schema = Schema3()

    with schema.open(dbfile) as db:

        with db.begin(write=True) as txn:
            for user in testset1:
                schema.users[txn, user.authid] = user

            # table count within transaction
            cnt = schema.users.count(txn)
            assert cnt == len(testset1)

        # table count in new transaction
        with db.begin() as txn:
            cnt = schema.users.count(txn)
            assert cnt == len(testset1)

    # table count in new connection
    with schema.open(dbfile) as db:
        with db.begin() as txn:
            cnt = schema.users.count(txn)
            assert cnt == len(testset1)


def test_count_prefix(dbfile, testset1):
    schema = Schema3()

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            for user in testset1:
                schema.users[txn, user.authid] = user

    n = len(testset1)
    tests = [
        (None, n),
        ('', n),
        ('test-', n),
        ('test-1', 111),
        ('test-11', 11),
        ('test-111', 1),
    ]
    with schema.open(dbfile) as db:
        with db.begin() as txn:
            for prefix, num in tests:
                cnt = schema.users.count(txn, prefix)
                assert cnt == num


def test_fill_with_indexes(dbfile, testset1):
    schema = Schema4()

    with schema.open(dbfile) as db:

        stats = zlmdb.TransactionStats()

        with db.begin(write=True, stats=stats) as txn:
            for user in testset1:
                schema.users[txn, user.oid] = user

        # check indexes has been written to (in addition to the table itself)
        num_indexes = 2
        assert stats.puts == len(testset1) * (1 + num_indexes)


def test_truncate_table_with_index(dbfile, testset1):
    schema = Schema4()

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            for user in testset1:
                schema.users[txn, user.oid] = user

    stats = zlmdb.TransactionStats()

    with schema.open(dbfile) as db:
        with db.begin(write=True, stats=stats) as txn:
            records = schema.users.truncate(txn)
            print('table truncated:', records)

    print(stats.puts)
    print(stats.dels)


def test_rebuild_index(dbfile, testset1):
    schema = Schema4()

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            for user in testset1:
                schema.users[txn, user.oid] = user

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            records = schema.users.rebuild_index(txn, 'idx1')
            print('\nrebuilt specific index "idx1" on "users": {} records affected'.format(records))


def test_rebuild_all_indexes(dbfile, testset1):
    schema = Schema4()

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            for user in testset1:
                schema.users[txn, user.oid] = user

    with schema.open(dbfile) as db:
        with db.begin(write=True) as txn:
            records = schema.users.rebuild_indexes(txn)
            print('\nrebuilt all indexes on "users": {} records affected'.format(records))
