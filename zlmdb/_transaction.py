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

"""Transactions"""

import struct
import lmdb


class TransactionStats(object):

    def __init__(self):
        self.puts = 0
        self.dels = 0

    def reset(self):
        self.puts = 0
        self.dels = 0


class BaseTransaction(object):

    PUT = 1
    DEL = 2

    def __init__(self, env, write=False, stats=None):
        self._env = env
        self._write = write
        self._txn = None
        self._log = None
        self._stats = stats

    def get(self, key):
        return self._txn.get(key)

    def put(self, key, data, overwrite=True):
        # store the record, returning True if it was written, or False to indicate the key
        # was already present and overwrite=False.
        was_written = self._txn.put(key, data, overwrite=overwrite)
        if was_written:
            if self._stats:
                self._stats.puts += 1
            if self._log:
                self._log.append((BaseTransaction.PUT, key))
        return was_written

    def delete(self, key):
        was_deleted = self._txn.delete(key)
        if was_deleted:
            if self._stats:
                self._stats.dels += 1
            if self._log:
                self._log.append((BaseTransaction.DEL, key))
        return was_deleted

    def attach(self):
        pass

    def __enter__(self):
        assert(self._txn is None)
        self._txn = lmdb.Transaction(self._env, write=self._write)
        self.attach()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert(self._txn is not None)
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        # If the context was exited without an exception, all three arguments will be None.
        if exc_type is None:
            if self._log:
                cnt = 0
                for op, key in self._log:
                    _key = struct.pack('>H', 0)
                    _data = struct.pack('>H', op) + key
                    self._txn.put(_key, _data)
                    cnt += 1
            self._txn.commit()
        else:
            self._txn.abort()
