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


@pytest.fixture(scope='module')
def testset1():
    users = []
    for j in range(10):
        for i in range(100):
            user = User.create_test_user(oid=j * 100 + i, realm_oid=j)
            users.append(user)
    return users


def test_fill_with_indexes(testset1):
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = Schema4()

        with zlmdb.Database(dbpath) as db:

            stats = zlmdb.TransactionStats()

            with db.begin(write=True, stats=stats) as txn:
                for user in testset1:
                    schema.users[txn, user.oid] = user

            # check indexes has been written to (in addition to the table itself)
            num_indexes = 3
            assert stats.puts == len(testset1) * (1 + num_indexes)

            # check saved objects
            with db.begin() as txn:
                for user in testset1:
                    obj = schema.users[txn, user.oid]

                    assert user == obj

            # check indexes
            with db.begin() as txn:
                for user in testset1:
                    # unique index
                    user_oid = schema.idx_users_by_authid[txn, user.authid]
                    assert user.oid == user_oid

                    # unique index
                    user_oid = schema.idx_users_by_email[txn, user.email]
                    assert user.oid == user_oid

                    # non-unique index
