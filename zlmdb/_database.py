#############################################################################
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
import shutil
import tempfile

import six
import lmdb

from zlmdb._transaction import Transaction


class Database(object):
    """
    ZLMDB database access.

    Objects of this class are generally "light-weight" (cheap to create and
    destroy), but do manage internal resource such as file descriptors.

    To manage these resources in a robust way, this class implements
    the Python context manager interface.
    """

    def __init__(self, dbfile=None, maxsize=10485760, readonly=False, sync=True):
        """

        :param schema: Database schema to use.
        :type schema: zlmdb.Schema

        :param dbfile: LMDB database file path.
        :type dbfile: str

        :param read_only: Open database read-only.
        :type read_only: bool
        """
        assert dbfile is None or type(dbfile) == str  # yes! not "six.text_type" in this case ..
        assert type(maxsize) in six.integer_types
        assert type(readonly) == bool
        assert type(sync) == bool

        if dbfile:
            self._is_temp = False
            self._dbfile = dbfile
        else:
            self._is_temp = True
            self._tempdir = tempfile.TemporaryDirectory()
            self._dbfile = self._tempdir.name
        self._maxsize = maxsize
        self._readonly = readonly
        self._sync = sync
        self._env = None

    def __enter__(self):
        assert self._env is None

        # https://lmdb.readthedocs.io/en/release/#lmdb.Environment
        self._env = lmdb.open(
            self._dbfile, map_size=self._maxsize, readonly=self._readonly, sync=self._sync, subdir=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert (self._env is not None)

        self._env.close()
        self._env = None

    @staticmethod
    def scratch(dbfile):
        if os.path.exists(dbfile):
            if os.path.isdir(dbfile):
                shutil.rmtree(dbfile)
            else:
                os.remove(dbfile)

    def begin(self, write=False, stats=None):
        assert self._env is not None

        if write and self._readonly:
            raise Exception('database is read-only')

        txn = Transaction(db=self, write=write, stats=stats)

        return txn

    def sync(self, force=False):
        assert self._env is not None

        self._env.sync(force=force)

    def stats(self):
        assert self._env is not None

        return self._env.stat()
