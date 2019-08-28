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
    print('Using _schema_py3 !')
    from _schema_py3 import User, Schema4
else:
    print('Using _schema_py2 !')
    from _schema_py2 import User, Schema4


@pytest.fixture(scope='function')
def testset1(N=10, M=100):
    users = []
    for j in range(N):
        for i in range(M):
            user = User.create_test_user(oid=j * M + i, realm_oid=j)
            users.append(user)
    return users


def test_fill_indexes(testset1):
    """
    Fill a table with multiple indexes with data records that have all columns filled
    with NON-NULL values.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            # fill table, which also triggers inserts into the index pmaps
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

                    user_oid = schema.idx_users_by_icecream[txn, (user.icecream, user.oid)]
                    assert user.oid == user_oid

                    user_oid = schema.idx_users_by_mrealm_authid[txn, (user.mrealm, user.authid)]
                    assert user.oid == user_oid

                    user_oid = schema.idx_users_by_mrealm_notnull_authid[txn, (user.mrealm_notnull, user.authid)]
                    assert user.oid == user_oid

            # check non-unique index
            users_by_icecream = {}
            for user in testset1:
                if user.icecream not in users_by_icecream:
                    users_by_icecream[user.icecream] = set()
                users_by_icecream[user.icecream].add(user.oid)

            MAX_OID = 9007199254740992
            with db.begin() as txn:
                for icecream in users_by_icecream:
                    for _, user_oid in schema.idx_users_by_icecream.select(
                            txn, from_key=(icecream, 0), to_key=(icecream, MAX_OID + 1), return_values=False):
                        assert user_oid in users_by_icecream[icecream]


def test_fill_indexes_nullable(testset1):
    """
    Test filling a table with multiple indexes, some of which are on NULLable columns, and fill
    with records that have those column values actually NULL.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    _user = deepcopy(user)

                    # "user.email" is an indexed column that is nullable
                    _user.email = None

                    # "user.mrealm" is an indexed (composite) column that is nullable
                    _user.mrealm = None
                    schema.users[txn, _user.oid] = _user

            # check indexes has been written to (in addition to the table itself)
            num_indexes = len(schema.users.indexes())

            # because we have set 2 indexed columns to NULL, we need to subtract those 2
            # from the total number of indexes
            assert stats.puts == len(testset1) * (1 + num_indexes - 2)

            # check saved objects
            with db.begin() as txn:
                for user in testset1:
                    _user = deepcopy(user)
                    _user.email = None
                    _user.mrealm = None

                    obj = schema.users[txn, _user.oid]

                    assert _user == obj

            # check unique indexes
            with db.begin() as txn:
                for user in testset1:
                    # check one of the indexes that was indeed filled
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid

                    # check indexes that have NOT been filled
                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_mrealm_authid[txn, (user.mrealm, user.authid)]
                    assert user_oid is None


def test_fill_index_non_nullable_raises(testset1):
    """
    Insert records into a table with a unique-non-nullable index with the
    record having a NULL value in the indexed column raises an exception.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            with db.begin(write=True) as txn:
                for user in testset1:
                    # "user.authid" is an indexed column that is non-nullable
                    _user = deepcopy(user)
                    _user.authid = None
                    with pytest.raises(zlmdb.NullValueConstraint):
                        schema.users[txn, _user.oid] = _user

                    # "user.mrealm_notnull" is an indexed (composite) column that is non-nullable
                    _user = deepcopy(user)
                    _user.mrealm_notnull = None
                    with pytest.raises(zlmdb.NullValueConstraint):
                        schema.users[txn, _user.oid] = _user


def test_fill_non_unique_indexes(testset1):
    """
    Insert records into a table with a non-unique, non-nullable indexed column.
    """
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


def test_delete_indexes(testset1):
    """
    Insert records into a table with indexes, delete data records and check that index
    records have been deleted as a consequence too.
    """
    with TemporaryDirectory() as dbpath:

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            # insert data records
            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # check that all index records have been deleted as well
            with db.begin(write=True) as txn:
                for user in testset1:
                    del schema.users[txn, user.oid]

                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_realm[txn, (user.realm_oid, user.oid)]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_icecream[txn, (user.icecream, user.oid)]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_mrealm_authid[txn, (user.mrealm, user.authid)]
                    assert user_oid is None

                    user_oid = schema.idx_users_by_mrealm_notnull_authid[txn, (user.mrealm_notnull, user.authid)]
                    assert user_oid is None


def test_delete_nonunique_indexes(testset1):
    """
    Insert records into a table with a non-unique index, delete data records and check
    that index records have been deleted as a consequence too.
    """
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


def test_delete_nonindexes2(testset1):
    """

    WARNING: quadratic run-time (in testset size)
    """
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
                            schema.idx_users_by_realm.select(
                                txn, return_keys=False, from_key=(j, 0), to_key=(j + 1, 0)))

                        assert fullset == user_oids


def test_set_null_indexes_nullable(testset1):
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


def test_set_notnull_indexes_nullable(testset1):
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
    """
    Fill a table with records that has indexes, truncate the table and check that
    all index records have been deleted as well.
    """
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
