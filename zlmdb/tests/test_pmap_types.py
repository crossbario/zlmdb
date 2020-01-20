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

import os
import sys

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

import txaio
txaio.use_twisted()

import zlmdb  # noqa

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

        with zlmdb.Database(dbpath) as db:
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
