import os
import sys

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User, Schema1
else:
    from _schema_py2 import User, Schema1


def test_pmap_value_types():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema1()

        n = 100
        stats = zlmdb.TransactionStats()

        tabs = [
            (schema.tab_oid_json, schema.tab_str_json, schema.tab_uuid_json),
            (schema.tab_oid_cbor, schema.tab_str_cbor, schema.tab_uuid_cbor),
            (schema.tab_oid_pickle, schema.tab_str_pickle, schema.tab_uuid_pickle),
        ]

        with schema.open(dbpath) as db:
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
