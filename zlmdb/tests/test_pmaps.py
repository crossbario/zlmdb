import os
import shutil
import datetime
import random
from typing import Optional, List, Dict

import lmdb
import pytest

from zlmdb import BaseTransaction, TransactionStats, MapOidPickle, MapStringOid


DBNAME = '.test-db1'


class User(object):

    oid: int
    name: str
    authid: str
    email: str
    birthday: datetime.date
    is_friendly: bool
    tags: Optional[List[str]]
    ratings: Dict[str, float] = {}
    friends: List[int] = []
    referred_by: int = None


class Transaction1(BaseTransaction):
    pass


class Transaction2(BaseTransaction):

    users: MapOidPickle = MapOidPickle(slot=1)

    def attach(self):
        self.users.attach_transaction(self)


class Transaction3(BaseTransaction):

    users: MapOidPickle = MapOidPickle(slot=1)
    idx_users_by_authid: MapStringOid = MapStringOid(slot=2)
    idx_users_by_email: MapStringOid = MapStringOid(slot=3)

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


def test_create_txn(env):
    with Transaction1(env) as txn:
        assert txn._txn.id() == 0


def test_fill_no_idx(env):
    n = 100
    stats = TransactionStats()
    with Transaction2(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = User()
            user.oid = i
            user.name = 'Test {}'.format(i)
            user.authid = 'test-{}'.format(i)
            user.email = '{}@example.com'.format(user.authid)
            for j in range(10):
                user.ratings['test-rating-{}'.format(j)] = random.random()

            _user = txn.users[user.oid]
            assert not _user

            txn.users[user.oid] = user

    assert stats.puts == n * 1


def test_fill_with_idxs(env):
    n = 100
    stats = TransactionStats()
    with Transaction3(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = User()
            user.oid = i
            user.name = 'Test {}'.format(i)
            user.authid = 'test-{}'.format(i)
            user.email = '{}@example.com'.format(user.authid)
            for j in range(10):
                user.ratings['test-rating-{}'.format(j)] = random.random()

            _user = txn.users[user.oid]
            assert not _user

            txn.users[user.oid] = user

    assert stats.puts == n * 3
