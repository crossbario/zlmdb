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
import pytest
import logging

import txaio

txaio.use_twisted()

import zlmdb  # noqa

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory  # type:ignore

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User, Schema1, Schema3, Schema4
else:
    from _schema_py2 import User, Schema1, Schema3, Schema4


@pytest.fixture(scope="module")
def testset1():
    users = []
    for j in range(10):
        for i in range(100):
            user = User.create_test_user(oid=j * 100 + i, realm_oid=j)
            users.append(user)
    return users


def test_truncate_table():
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema1()

        stats = zlmdb.TransactionStats()
        tabs = [
            schema.tab_oid_json,
            schema.tab_str_json,
            schema.tab_uuid_json,
            schema.tab_oid_cbor,
            schema.tab_str_cbor,
            schema.tab_uuid_cbor,
            schema.tab_oid_pickle,
            schema.tab_str_pickle,
            schema.tab_uuid_pickle,
        ]

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True, stats=stats) as txn:
                for tab in tabs:
                    tab.truncate(txn)

        logging.info(stats.puts)
        logging.info(stats.dels)


def test_fill_check(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema3()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.authid] = user

        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for user in testset1:
                    _user = schema.users[txn, user.authid]
                    assert _user
                    assert _user == user


def test_fill_check2(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for user in testset1:
                    _user = schema.users[txn, user.oid]
                    assert _user
                    assert _user == user


def test_select(testset1):
    testset1_keys = set([user.authid for user in testset1])

    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema3()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.authid] = user

        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                i = 0
                for authid, user in schema.users.select(txn):
                    i += 1
                    assert user
                    assert authid == user.authid
                    assert authid in testset1_keys


def test_count_all(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema3()

        with zlmdb.Database(dbpath) as db:
            # count on empty table
            with db.begin() as txn:
                cnt = schema.users.count(txn)
                assert cnt == 0

            # fill (and count on each insert)
            with db.begin(write=True) as txn:
                i = 0
                for user in testset1:
                    schema.users[txn, user.authid] = user
                    i += 1

                    # table count within filling transaction
                    cnt = schema.users.count(txn)
                    assert cnt == i

                # table count within transaction
                cnt = schema.users.count(txn)
                assert cnt == len(testset1)

            # table count in new transaction
            with db.begin() as txn:
                cnt = schema.users.count(txn)
                assert cnt == len(testset1)

        # table count in new connection
        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                cnt = schema.users.count(txn)
                assert cnt == len(testset1)


def test_count_prefix(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema3()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.authid] = user

        n = len(testset1)
        tests = [
            (None, n),
            ("", n),
            ("test-", n),
            ("test-1", 111),
            ("test-11", 11),
            ("test-111", 1),
        ]
        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for prefix, num in tests:
                    cnt = schema.users.count(txn, prefix)
                    assert cnt == num


def test_fill_with_indexes(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # check indexes has been written to (in addition to the table itself)
            num_indexes = len(schema.users.indexes())
            assert stats.puts == len(testset1) * (1 + num_indexes)


def test_truncate_table_with_index(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

        stats = zlmdb.TransactionStats()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True, stats=stats) as txn:
                records = schema.users.truncate(txn)
                logging.info("table truncated: {}".format(records))

        logging.info(stats.puts)
        logging.info(stats.dels)


def test_rebuild_index(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                records = schema.users.rebuild_index(txn, "idx1")
                logging.info(
                    '\nrebuilt specific index "idx1" on "users": {} records affected'.format(
                        records
                    )
                )


def test_rebuild_all_indexes(testset1):
    with TemporaryDirectory() as dbpath:
        logging.info("Using temporary directory {} for database".format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                records = schema.users.rebuild_indexes(txn)
                logging.info(
                    '\nrebuilt all indexes on "users": {} records affected'.format(
                        records
                    )
                )
