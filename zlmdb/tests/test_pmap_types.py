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


def test_pmap_value_types(schema, dbfile):
    """
    :type: UsersSchema2
    """
    n = 100
    stats = zlmdb.TransactionStats()

    tabs = [
        (schema.tab_oid_json, schema.tab_str_json, schema.tab_uuid_json),
        (schema.tab_oid_cbor, schema.tab_str_cbor, schema.tab_uuid_cbor),
        (schema.tab_oid_pickle, schema.tab_str_pickle, schema.tab_uuid_pickle),
    ]

    with schema.open(dbfile) as db:
        for tab_oid, tab_str, tab_uuid in tabs:
            with db.begin(write=True, stats=stats) as txn:
                for i in range(n):
                    user = User.create_test_user(i)
                    tab_oid[txn, user.oid] = user
                    tab_str[txn, user.authid] = user
                    tab_uuid[txn, user.uuid] = user

            print('transaction committed')
            assert stats.puts == n * 3
            assert stats.dels == 0

            stats.reset()

            with db.begin() as txn:
                cnt = tab_oid.count(txn)
                assert cnt == n

                cnt = tab_str.count(txn)
                assert cnt == n

                cnt = tab_uuid.count(txn)
                assert cnt == n

    print('database closed')
