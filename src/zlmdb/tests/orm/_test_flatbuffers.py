###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) typedef int GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

import os
import sys
import random
import logging

import txaio

txaio.use_twisted()

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory  # type:ignore

import zlmdb  # noqa

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _schema_fbs import User  # noqa


class UsersSchema(zlmdb.Schema):
    def __init__(self):
        self.tab_oid_fbs = zlmdb.MapOidFlatBuffers(1, build=User.build, cast=User.cast)


def test_pmap_flatbuffers_values():
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = UsersSchema()

        with zlmdb.Database(dbpath) as db:
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
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = UsersSchema()

        # max DB size is 100 MB
        with zlmdb.Database(dbpath, maxsize=100 * (2**20)) as db:
            oids = set()
            oid_to_referred_by = {}

            stats = zlmdb.TransactionStats()

            # number of transactions
            M = 5

            # number of insert rows per transaction
            N = 10000
            for j in range(M):
                with db.begin(write=True, stats=stats) as txn:
                    for i in range(N):
                        user = User.create_test_user()
                        schema.tab_oid_fbs[txn, user.oid] = user
                        oids.add(user.oid)
                        oid_to_referred_by[user.oid] = user.referred_by

                assert stats.puts == N
                assert stats.dels == 0
                duration_ns = stats.duration
                duration_ms = int(duration_ns / 1000000.0)
                rows_per_sec = int(
                    round(float(stats.puts + stats.dels) * 1000.0 / float(duration_ms))
                )
                logging.info(
                    "Transaction ended: puts={} / dels={} rows in {} ms, {} rows/sec".format(
                        stats.puts, stats.dels, duration_ms, rows_per_sec
                    )
                )

                stats.reset()

            # count all rows
            with db.begin() as txn:
                cnt = schema.tab_oid_fbs.count(txn)

            assert cnt == N * M

            # retrieve
            with db.begin() as txn:
                for j in range(5):
                    started = zlmdb.walltime()
                    M = 100
                    for i in range(M):
                        for oid in random.sample(oids, N):
                            user = schema.tab_oid_fbs[txn, oid]
                            assert user
                            assert user.referred_by == oid_to_referred_by.get(oid, None)
                    duration_ns = zlmdb.walltime() - started
                    duration_ms = int(duration_ns / 1000000.0)
                    rows_per_sec = int(
                        round(float(M * N) * 1000.0 / float(duration_ms))
                    )
                    logging.info(
                        "Transaction ended: {} rows read in {} ms, {} rows/sec".format(
                            M * N, duration_ms, rows_per_sec
                        )
                    )
