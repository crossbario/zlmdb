import os
import sys
import random

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _schema_fbs import User  # noqa


class UsersSchema(zlmdb.Schema):
    def __init__(self):
        self.tab_oid_fbs = zlmdb.MapOidFlatBuffers(1, build=User.build, cast=User.cast)


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


def test_pmap_flatbuffers_count():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = UsersSchema()

        # max DB size is 100 MB
        with schema.open(dbpath, maxsize=100 * (2**20)) as db:

            oids = set()
            oid_to_referred_by = {}

            stats = zlmdb.TransactionStats()

            # number of transactions
            M = 5

            # number of insert rows per transaction
            N = 2000
            for j in range(M):
                with db.begin(write=True, stats=stats) as txn:
                    for i in range(N):
                        user = User.create_test_user()
                        schema.tab_oid_fbs[txn, user.oid] = user
                        oids.add(user.oid)
                        oid_to_referred_by[user.oid] = user.referred_by

                assert stats.puts == N * (j + 1)
                assert stats.dels == 0
                duration = stats.duration
                ms = int(1000. * duration)
                rows_per_sec = int(round(float(stats.puts + stats.dels) / float(duration)))
                print('Transaction committed (puts={}, dels={}) rows in {} ms, {} rows/sec)'.format(
                    stats.puts, stats.dels, ms, rows_per_sec))
            stats.reset()

            # count all rows
            with db.begin() as txn:
                cnt = schema.tab_oid_fbs.count(txn)

            assert cnt == N * M

            # retrieve
            started = zlmdb.walltime()
            with db.begin() as txn:
                M = 100
                for i in range(M):
                    for oid in random.sample(oids, N):
                        user = schema.tab_oid_fbs[txn, oid]
                        assert user
                        assert user.referred_by == oid_to_referred_by.get(oid, None)
                duration = zlmdb.walltime() - started
                ms = int(1000. * duration)
                rows_per_sec = int(round(float(M * N) / float(duration)))
                print('Transaction committed ({} rows in {} ms, {} rows/sec)'.format(M * N, ms, rows_per_sec))
