import os
import sys
import shutil
import random
import lmdb
import pytest
import uuid
import datetime

from zlmdb import BaseTransaction, \
                  TransactionStats, \
                  MapOidFlatBuffers

DBNAME = '.test-db1'

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_fbs import User  # noqa


class Transaction(BaseTransaction):

    def __init__(self, *args, **kwargs):
        BaseTransaction.__init__(self, *args, **kwargs)
        self.tab_oid_fbs = MapOidFlatBuffers(slot=1, build=User.build, root=User.root)

    def attach(self):
        self.tab_oid_fbs.attach_transaction(self)


@pytest.fixture(scope='function')
def env():
    if os.path.exists(DBNAME):
        if os.path.isdir(DBNAME):
            shutil.rmtree(DBNAME)
        else:
            os.remove(DBNAME)
    env = lmdb.open(DBNAME)
    return env


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


def test_pmap_flatbuffers_values(env):
    n = 100

    stats = TransactionStats()

    with Transaction(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user()
            txn.tab_oid_fbs[user.oid] = user

    assert stats.puts == n
    assert stats.dels == 0

    stats.reset()

    with Transaction(env) as txn:
        for tab in [txn.tab_oid_fbs]:
            rows = tab.count()
            assert rows == n
