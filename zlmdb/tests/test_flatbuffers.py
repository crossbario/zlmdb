import os
import sys
import pytest

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from user_fbs import User


class UsersSchema(zlmdb.Schema):
    def __init__(self):
        self.tab_oid_fbs = zlmdb.MapOidFlatBuffers(1, build=User.build, root=User.root)


@pytest.fixture(scope='function')
def dbfile():
    _dbfile = '.testdb'
    zlmdb.Database.scratch(_dbfile)
    return _dbfile


@pytest.fixture(scope='function')
def schema():
    _schema = UsersSchema()
    return _schema


def test_pmap_flatbuffers_values(schema, dbfile):
    N = 100

    stats = zlmdb.TransactionStats()

    with schema.open(dbfile) as db:

        with db.begin(write=True, stats=stats) as txn:
            for i in range(N):
                user = User.create_test_user()
                schema.tab_oid_fbs[txn, user.oid] = user

        assert stats.puts == N
        assert stats.dels == 0
        stats.reset()

        with db.begin() as txn:
            cnt = schema.tab_oid_fbs.count(txn)

        assert cnt == N

