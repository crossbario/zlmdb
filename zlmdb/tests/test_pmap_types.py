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


def test_pmap_json_values(schema, dbfile):
    n = 100
    stats = zlmdb.TransactionStats()

    with schema.open(dbfile) as db:
        with db.begin(write=True, stats=stats) as txn:
            print('transaction open', txn.id())
            for i in range(n):
                user = User.create_test_user(i)
                schema.tab_oid_json[txn, user.oid] = user
                schema.tab_str_json[txn, user.authid] = user
                schema.tab_uuid_json[txn, user.uuid] = user

        print('transaction committed')
        assert stats.puts == n * 3
        assert stats.dels == 0

        stats.reset()

        with db.begin() as txn:
            cnt = schema.tab_oid_json.count(txn)
            assert cnt == n

            cnt = schema.tab_str_json.count(txn)
            assert cnt == n

            cnt = schema.tab_uuid_json.count(txn)
            assert cnt == n

    print('database closed')
