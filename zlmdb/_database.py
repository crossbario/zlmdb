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

from __future__ import absolute_import

import os
import shutil
import tempfile

import six
import lmdb
import yaml
import pprint

from zlmdb._transaction import Transaction
from zlmdb._pmap import MapStringJson, MapStringCbor, MapUuidJson, MapUuidCbor

KV_TYPE_TO_CLASS = {
    'string-json': (MapStringJson, lambda x: x, lambda x: x),
    'string-cbor': (MapStringCbor, lambda x: x, lambda x: x),
    'uuid-json': (MapUuidJson, lambda x: x, lambda x: x),
    'uuid-cbor': (MapUuidCbor, lambda x: x, lambda x: x),
}


class Schema(object):
    def __init__(self, meta, slots, slots_byname):
        self._meta = meta
        self._slots = slots
        self._slots_byname = slots_byname

    def __str__(self):
        return pprint.pformat(self._meta)

    def __getitem__(self, name):
        assert type(name) == str

        if name not in self._slots_byname:
            raise IndexError('no slot with name "{}"'.format(name))

        return self._slots[self._slots_byname[name]]

    def __setitem__(self, name, value):
        raise NotImplementedError('schema is read-only')

    def __delitem__(self, name):
        raise NotImplementedError('schema is read-only')

    def __len__(self):
        return len(self._slots_byname)

    def __iter__(self):
        raise Exception('not implemented')

    @staticmethod
    def parse(filename, klassmap=KV_TYPE_TO_CLASS):
        with open(filename) as f:
            _meta = yaml.load(f.read())

            meta = {}
            slots = {}
            slots_byname = {}

            for slot in _meta.get('slots', []):
                _index = slot.get('index', None)
                assert type(_index) in six.integer_types and _index >= 100 and _index < 65536
                assert _index not in slots

                _name = slot.get('name', None)
                assert type(_name) == six.text_type
                assert _name not in slots_byname

                _key = slot.get('key', None)
                assert _key in ['string', 'uuid']

                _value = slot.get('value', None)
                assert _value in ['json', 'cbor']

                _schema = slot.get('schema', None)
                assert _schema is None or type(_schema) == six.text_type

                _description = slot.get('description', None)
                assert _description is None or type(_description) == six.text_type

                if _schema:
                    _kv_type = '{}-{}-{}'.format(_key, _value, _schema)
                else:
                    _kv_type = '{}-{}'.format(_key, _value)

                _kv_klass, _marshal, _unmarshal = klassmap.get(_kv_type, (None, None, None))

                assert _kv_klass
                assert _marshal
                assert _unmarshal

                meta[_index] = {
                    'index': _index,
                    'name': _name,
                    'key': _key,
                    'value': _value,
                    'impl': _kv_klass.__name__ if _kv_klass else None,
                    'description': _description,
                }
                slots[_index] = _kv_klass(_index, marshal=_marshal, unmarshal=_unmarshal)
                slots_byname[_name] = _index

            return Schema(meta, slots, slots_byname)


class Database(object):
    """
    ZLMDB database access.

    Objects of this class are generally "light-weight" (cheap to create and
    destroy), but do manage internal resource such as file descriptors.

    To manage these resources in a robust way, this class implements
    the Python context manager interface.
    """

    def __init__(self, dbfile=None, dbschema=None, maxsize=10485760, readonly=False, sync=True):
        """

        :param dbfile: LMDB database file path.
        :type dbfile: str

        :param dbschema: Database schema file to use.
        :type dbschema: str

        :param maxsize: Database size limit in bytes (default: 1MB).
        :type maxsize: int

        :param read_only: Open database read-only.
        :type read_only: bool

        :param sync: Open database with sync on commit (default: true).
        :type sync: bool
        """
        assert dbfile is None or type(dbfile) == str
        assert dbschema is None or isinstance(dbschema, Schema)
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

        self._dbschema = dbschema
        self._maxsize = maxsize
        self._readonly = readonly
        self._sync = sync

        # context manager environment we initialize with LMDB handle
        # when we enter the actual temporary, managed context ..
        self._env = None

    def __enter__(self):
        # temporary managed context entered ..
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
