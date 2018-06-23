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

import random
import os
import lmdb
import struct

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory


def test_lmdb_create():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        env = lmdb.open(dbpath)

        with env.begin() as txn:
            assert txn.id() == 0


def test_lmdb_insert():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        n = 100
        total1 = 0
        env = lmdb.open(dbpath)

        with env.begin(write=True) as txn:
            for i in range(n):
                key = 'key-{}'.format(i).encode('utf8')
                value = random.randint(0, 2**32 - 1)
                total1 += value
                data = struct.pack('<L', value)
                txn.put(key, data)

        with env.begin() as txn:

            cursor = txn.cursor()
            assert cursor.first()

            count = 1
            total2 = struct.unpack('<L', cursor.value())[0]

            while cursor.next():
                count += 1
                total2 += struct.unpack('<L', cursor.value())[0]

            assert count == n
            assert total1 == total2


def test_lmdb_delete():
    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        n = 100
        env = lmdb.open(dbpath)

        with env.begin(write=True) as txn:
            for i in range(n):
                key = 'key-{}'.format(i).encode('utf8')
                value = os.urandom(16)
                txn.put(key, value)

        with env.begin(write=True) as txn:
            for i in range(n):
                key = 'key-{}'.format(i).encode('utf8')
                assert txn.delete(key)

        with env.begin() as txn:
            cursor = txn.cursor()
            assert not cursor.first()
