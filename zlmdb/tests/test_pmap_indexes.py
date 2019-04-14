###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
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

from __future__ import absolute_import

import os
import sys
import pytest
from copy import deepcopy

import txaio
txaio.use_twisted()

import zlmdb  # noqa

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from _schema_py3 import User, Schema4
else:
    from _schema_py2 import User, Schema4


@pytest.fixture(scope='function')
def testset1(N=10, M=100):
    users = []
    for j in range(N):
        for i in range(M):
            user = User.create_test_user(oid=j * M + i, realm_oid=j)
            users.append(user)
    return users


def test_fill_unique_indexes(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # check indexes has been written to (in addition to the table itself)
            num_indexes = len(schema.users.indexes())
            assert stats.puts == len(testset1) * (1 + num_indexes)

            # check saved objects
            with db.begin() as txn:
                for user in testset1:
                    obj = schema.users[txn, user.oid]

                    assert user == obj

            # check unique indexes
            with db.begin() as txn:
                for user in testset1:
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid

                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user.oid == user_oid


def test_fill_unique_indexes_nullable(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    user.email = None
                    schema.users[txn, user.oid] = user

            # check indexes has been written to (in addition to the table itself)
            num_indexes = len(schema.users.indexes())
            assert stats.puts == len(testset1) * (1 + num_indexes - 1)

            # check saved objects
            with db.begin() as txn:
                for user in testset1:
                    obj = schema.users[txn, user.oid]

                    assert user == obj

            # check unique indexes
            with db.begin() as txn:
                for user in testset1:
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid


def test_fill_nonunique_indexes(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # check non-unique indexes
            with db.begin() as txn:
                for j in range(10):
                    user_oids = list(
                        schema.idx_users_by_realm.select(txn, return_keys=False, from_key=(j, 0), to_key=(j + 1, 0)))

                    assert list(range(j * 100, (j + 1) * 100)) == user_oids


def test_delete_unique_indexes(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            with db.begin(write=True) as txn:
                for user in testset1:
                    del schema.users[txn, user.oid]

                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user_oid is None


def test_delete_nonunique_indexes(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            with db.begin(write=True) as txn:
                for user in testset1:
                    del schema.users[txn, user.oid]

            with db.begin() as txn:
                for j in range(10):
                    user_oids = list(
                        schema.idx_users_by_realm.select(txn, return_keys=False, from_key=(j, 0), to_key=(j + 1, 0)))

                    assert [] == user_oids


def test_delete_nonunique_indexes2(testset1):
    # WARNING: quadratic run-time (in testset size)
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            with db.begin(write=True) as txn:
                for j in range(10):
                    fullset = set(range(j * 100, (j + 1) * 100))
                    for i in range(100):
                        user_oid = j * 100 + i
                        del schema.users[txn, user_oid]
                        fullset.discard(user_oid)

                        user_oids = set(
                            schema.idx_users_by_realm.select(txn,
                                                             return_keys=False,
                                                             from_key=(j, 0),
                                                             to_key=(j + 1, 0)))

                        assert fullset == user_oids


def test_set_null_unique_indexes_nullable(testset1):
    """
    Fill table with indexed column (unique-nullable) with indexed column
    values NULL, then (in a 2nd transaction) set the indexed column
    to NON-NULL value and check that index records are deleted.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            # fill table with NON-NULLs in indexed column
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # now update table with NULLs in indexed column
            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    _user = schema.users[txn, user.oid]
                    _user.email = None
                    schema.users[txn, _user.oid] = _user

            # check that the table records have their indexed
            # column values updated to NULLs
            with db.begin() as txn:
                for user in testset1:
                    _user = deepcopy(user)
                    _user.email = None
                    obj = schema.users[txn, user.oid]
                    assert _user == obj

            # check that the index records that previously existed
            # have been deleted (as the indexed column values have been
            # set to NULLs)
            with db.begin() as txn:
                for user in testset1:
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid

                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user_oid is None


def test_set_notnull_unique_indexes_nullable(testset1):
    """
    Fill table with indexed column (unique-nullable) with indexed column
    values NON-NULL, then (in a 2nd transaction) set the indexed column
    to NULL value and check that index records are created.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            # fill table with NULLs in indexed column
            with db.begin(write=True) as txn:
                for user in testset1:
                    _user = deepcopy(user)
                    _user.email = None
                    schema.users[txn, _user.oid] = _user

            # now update table with NON-NULLs in indexed column
            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    _user = schema.users[txn, user.oid]
                    _user.email = user.email
                    schema.users[txn, _user.oid] = _user

            # check that the table records have their indexed
            # column values updated to NON-NULLs
            with db.begin() as txn:
                for user in testset1:
                    obj = schema.users[txn, user.oid]
                    assert user == obj

            # check that the index records that previously not existed
            # have been created (as the indexed column values have been
            # set to NON-NULLs)
            with db.begin() as txn:
                for user in testset1:
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid

                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user.oid == user_oid


def test_truncate_table_with_index(testset1):
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

        stats = zlmdb.TransactionStats()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True, stats=stats) as txn:
                records = schema.users.truncate(txn)

                assert records == len(testset1) * (len(schema.users.indexes()) + 1)

        assert stats.dels == records
        assert stats.puts == 0
