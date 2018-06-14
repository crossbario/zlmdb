import os
import sys
import pytest

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from user_py3 import User, UsersSchema2
else:
    from user_py2 import User, UsersSchema2


@pytest.fixture(scope='function')
def dbfile():
    _dbfile = '.testdb'
    zlmdb.Database.scratch(_dbfile)
    return _dbfile


@pytest.fixture(scope='function')
def schema():
    _schema = UsersSchema2()
    return _schema


def test_create_txn(env):
    with Transaction1(env) as txn:
        assert txn._txn.id() == 0


def test_fill_no_idx(env):
    n = 100
    stats = TransactionStats()
    with Transaction2(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user(i)

            _user = txn.users[user.oid]
            assert not _user

            txn.users[user.oid] = user

            _user = txn.users[user.oid]
            assert _user
            assert _user.oid == user.oid

    assert stats.puts == n * 1


def test_fill_with_idxs(env):
    n = 100
    stats = TransactionStats()
    with Transaction3(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user(i)

            _user = txn.users[user.oid]
            assert not _user

            txn.users[user.oid] = user

            _user = txn.users[user.oid]
            assert _user
            assert _user.oid == user.oid

    assert stats.puts == n * 3


def test_table_count(env):
    n = 200

    stats = TransactionStats()

    with Transaction4(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user(i)
            txn.users[user.authid] = user

    with Transaction4(env) as txn:
        rows = txn.users.count()
        assert rows == n

    with Transaction4(env) as txn:
        rows = txn.users.count('test-111')
        assert rows == 1

        rows = txn.users.count('test-11')
        assert rows == 11

        rows = txn.users.count('test-1')
        assert rows == 111

        rows = txn.users.count('test-')
        assert rows == n

        rows = txn.users.count('')
        assert rows == n


def test_truncate_table(env):
    n = 100

    stats = TransactionStats()

    with Transaction2(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user(i)
            txn.users[user.oid] = user

    assert stats.puts == n


def test_rebuild_index(env):
    with Transaction3(env, write=True) as txn:
        records = txn.users.rebuild_index('idx1')
        print('\nrebuilt specific index "idx1" on "users": {} records affected'.format(records))


def test_rebuild_all_indexes(env):
    with Transaction3(env, write=True) as txn:
        records = txn.users.rebuild_indexes()
        print('\nrebuilt all indexes on "users": {} records affected'.format(records))
