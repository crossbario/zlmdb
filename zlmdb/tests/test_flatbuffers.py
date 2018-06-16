import os
import sys

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _schema_fbs import User  # noqa


class UsersSchema(zlmdb.Schema):

    def __init__(self):
        self.tab_oid_fbs = zlmdb.MapOidFlatBuffers(1, build=User.build, root=User.root)


def test_pmap_flatbuffers_values():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = UsersSchema()

        with schema.open(dbpath) as db:

            N = 100
            stats = zlmdb.TransactionStats()

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
