import os
import sys
import shutil
import random
import lmdb
import pytest

from zlmdb import BaseTransaction, TransactionStats, MapOidPickle, MapStringOid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from user_typed import User
else:
    from user import User


DBNAME = '.test-db1'


class Transaction1(BaseTransaction):

    def __init__(self, *args, **kwargs):
        BaseTransaction.__init__(self, *args, **kwargs)


class Transaction2(BaseTransaction):

    def __init__(self, *args, **kwargs):
        BaseTransaction.__init__(self, *args, **kwargs)
        self.users = MapOidPickle(slot=1)

    def attach(self):
        self.users.attach_transaction(self)


class Transaction3(BaseTransaction):

    def __init__(self, *args, **kwargs):
        BaseTransaction.__init__(self, *args, **kwargs)

        self.users = MapOidPickle(slot=1)
        self.idx_users_by_authid = MapStringOid(slot=2)
        self.idx_users_by_email = MapStringOid(slot=3)

    def attach(self):
        self.users.attach_transaction(self)

        self.idx_users_by_authid.attach_transaction(self)
        self.users.attach_index('idx1', lambda user: user.authid, self.idx_users_by_authid)

        self.idx_users_by_email.attach_transaction(self)
        self.users.attach_index('idx2', lambda user: user.email, self.idx_users_by_email)


@pytest.fixture(scope='function')
def env():
    if os.path.exists(DBNAME):
        if os.path.isdir(DBNAME):
            shutil.rmtree(DBNAME)
        else:
            os.remove(DBNAME)
    env = lmdb.open(DBNAME)
    return env


def _create_test_user(i):
    user = User()
    user.oid = i
    user.name = 'Test {}'.format(i)
    user.authid = 'test-{}'.format(i)
    user.email = '{}@example.com'.format(user.authid)
    for j in range(10):
        user.ratings['test-rating-{}'.format(j)] = random.random()
    return user


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
