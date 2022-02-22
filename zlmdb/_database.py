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
import uuid
import pprint
import struct
import inspect

import lmdb
import yaml
import cbor2

from zlmdb._transaction import Transaction
from zlmdb import _pmap
from zlmdb._pmap import MapStringJson, MapStringCbor, MapUuidJson, MapUuidCbor

import txaio

try:
    from twisted.python.reflect import qual
except ImportError:

    def qual(klass):
        return klass.__name__


KV_TYPE_TO_CLASS = {
    'string-json': (MapStringJson, lambda x: x, lambda x: x),
    'string-cbor': (MapStringCbor, lambda x: x, lambda x: x),
    'uuid-json': (MapUuidJson, lambda x: x, lambda x: x),
    'uuid-cbor': (MapUuidCbor, lambda x: x, lambda x: x),
}


class ConfigurationElement(object):

    # oid: uuid.UUID
    # name: str
    # description: Optional[str]
    # tags: Optional[List[str]]

    def __init__(self, oid=None, name=None, description=None, tags=None):
        self._oid = oid
        self._name = name
        self._description = description
        self._tags = tags

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if other.oid != self.oid:
            return False
        if other.name != self.name:
            return False
        if other.description != self.description:
            return False
        if (self.tags and not other.tags) or (not self.tags and other.tags):
            return False
        if other.tags and self.tags:
            if set(other.tags) ^ set(self.tags):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def oid(self):
        return self._oid

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def tags(self):
        return self._tags

    def marshal(self):
        value = {
            u'oid': str(self._oid),
            u'name': self._name,
        }
        if self.description:
            value[u'description'] = self._description
        if self.tags:
            value[u'tags'] = self._tags
        return value

    @staticmethod
    def parse(value):
        assert type(value) == dict
        oid = value.get('oid', None)
        if oid:
            oid = uuid.UUID(oid)
        obj = ConfigurationElement(oid=oid,
                                   name=value.get('name', None),
                                   description=value.get('description', None),
                                   tags=value.get('tags', None))
        return obj


class Slot(ConfigurationElement):
    def __init__(self, oid=None, name=None, description=None, tags=None, slot=None, creator=None):
        ConfigurationElement.__init__(self, oid=oid, name=name, description=description, tags=tags)
        self._slot = slot
        self._creator = creator

    def __str__(self):
        return pprint.pformat(self.marshal())

    @property
    def creator(self):
        return self._creator

    @property
    def slot(self):
        return self._slot

    def marshal(self):
        obj = ConfigurationElement.marshal(self)
        obj.update({
            'creator': self._creator,
            'slot': self._slot,
        })
        return obj

    @staticmethod
    def parse(data):
        assert type(data) == dict

        obj = ConfigurationElement.parse(data)

        slot = data.get('slot', None)
        creator = data.get('creator', None)

        drvd_obj = Slot(oid=obj.oid,
                        name=obj.name,
                        description=obj.description,
                        tags=obj.tags,
                        slot=slot,
                        creator=creator)
        return drvd_obj


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
                assert type(_index) == int and _index >= 100 and _index < 65536
                assert _index not in slots

                _name = slot.get('name', None)
                assert type(_name) == str
                assert _name not in slots_byname

                _key = slot.get('key', None)
                assert _key in ['string', 'uuid']

                _value = slot.get('value', None)
                assert _value in ['json', 'cbor']

                _schema = slot.get('schema', None)
                assert _schema is None or type(_schema) == str

                _description = slot.get('description', None)
                assert (_description is None or type(_description) == str)

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
    def __init__(self,
                 dbpath=None,
                 maxsize=10485760,
                 readonly=False,
                 lock=True,
                 sync=True,
                 create=True,
                 open=True,
                 log=None):
        """

        :param dbpath: LMDB database path: a directory with (at least) 2 files, a ``data.mdb`` and a ``lock.mdb``.
            If no database exists at the given path, create a new one.
        :type dbpath: str

        :param maxsize: Database size limit in bytes, with a default of 1MB.
        :type maxsize: int

        :param read_only: Open database read-only. When ``True``, deny any modifying database operations.
            Note that the LMDB lock file (``lock.mdb``) still needs to be written (by readers also),
            and hence at the filesystem level, a LMDB database directory must be writable.
        :type read_only: bool

        :param sync: Open database with sync on commit.
        :type sync: bool
        """
        assert dbpath is None or type(dbpath) == str
        assert type(maxsize) == int
        assert type(readonly) == bool
        assert type(lock) == bool
        assert type(sync) == bool
        assert type(create) == bool
        assert type(open) == bool

        if log:
            self.log = log
        else:
            if not txaio._explicit_framework:
                txaio.use_asyncio()
            self.log = txaio.make_logger()

        if dbpath:
            self._is_temp = False
            self._dbpath = dbpath
        else:
            self._is_temp = True
            self._tempdir = tempfile.TemporaryDirectory()
            self._dbpath = self._tempdir.name

        self._maxsize = maxsize
        self._readonly = readonly
        self._lock = lock
        self._sync = sync
        self._create = create
        self._open = open

        self._slots = None
        self._slots_by_index = None

        # in a context manager environment we initialize with LMDB handle
        # when we enter the actual temporary, managed context ..
        self._env = None

        # in a direct run environment, we immediately open LMDB
        if self._open:
            self.__enter__()

    def __enter__(self):
        # lmdb.open(db_dir, create=False, subdir=True, readonly=True, lock=False)
        # https://stackoverflow.com/questions/56905502/lmdb-badrsloterror-mdb-txn-begin-mdb-bad-rslot-invalid-reuse-of-reader-lockta

        # temporary managed context entered ..
        if not self._env:
            # https://lmdb.readthedocs.io/en/release/#lmdb.Environment
            # lock=True is needed for concurrent access, even when only by readers (because of space mgmt)
            self._env = lmdb.open(self._dbpath,
                                  map_size=self._maxsize,
                                  create=self._create,
                                  readonly=self._readonly,
                                  sync=self._sync,
                                  subdir=True,
                                  lock=self._lock,
                                  writemap=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        assert (self._env is not None)

        self._env.close()
        self._env = None

    @property
    def dbpath(self):
        return self._dbpath

    @property
    def maxsize(self):
        return self._maxsize

    @property
    def is_sync(self):
        return self._sync

    @property
    def is_readonly(self):
        return self._readonly

    @property
    def is_open(self):
        return self._env is not None

    @staticmethod
    def scratch(dbpath):
        if os.path.exists(dbpath):
            if os.path.isdir(dbpath):
                shutil.rmtree(dbpath)
            else:
                os.remove(dbpath)

    def begin(self, write=False, buffers=False, stats=None):
        assert self._env is not None

        if write and self._readonly:
            raise Exception('database is read-only')

        txn = Transaction(db=self, write=write, buffers=buffers, stats=stats)
        return txn

    def sync(self, force=False):
        assert self._env is not None

        self._env.sync(force=force)

    def stats(self):
        assert self._env is not None

        current_size = os.path.getsize(os.path.join(self._dbpath, 'data.mdb'))

        res = {
            'zlmdb_slots': len(self._slots),
            'current_size': current_size,
            'max_size': self._maxsize,
            'free': 1. - float(current_size) / float(self._maxsize),
            'read_only': self._readonly,
            'sync_enabled': self._sync,
        }

        # psize 	        Size of a database page in bytes.
        # depth 	        Height of the B-tree.
        # branch_pages 	    Number of internal (non-leaf) pages.
        # leaf_pages 	    Number of leaf pages.
        # overflow_pages 	Number of overflow pages.
        # entries 	        Number of data items.
        res.update(self._env.stat())

        # map_addr 	        Address of database map in RAM.
        # map_size 	        Size of database map in RAM.
        # last_pgno 	    ID of last used page.
        # last_txnid 	    ID of last committed transaction.
        # max_readers 	    Number of reader slots allocated in the lock file. Equivalent to the value of
        #                   maxreaders= specified by the first process opening the Environment.
        # num_readers 	    Maximum number of reader slots in simultaneous use since the lock file was initialized.
        res.update(self._env.info())

        return res

    def _cache_slots(self):
        slots = {}
        slots_by_index = {}

        with self.begin() as txn:
            from_key = struct.pack('>H', 0)
            to_key = struct.pack('>H', 1)

            cursor = txn._txn.cursor()
            found = cursor.set_range(from_key)
            while found:
                _key = cursor.key()
                if _key >= to_key:
                    break

                if len(_key) >= 4:
                    # key = struct.unpack('>H', _key[0:2])
                    slot_index = struct.unpack('>H', _key[2:4])[0]
                    slot = Slot.parse(cbor2.loads(cursor.value()))
                    assert slot.slot == slot_index
                    slots[slot.oid] = slot
                    slots_by_index[slot.oid] = slot_index

                found = cursor.next()

        self._slots = slots
        self._slots_by_index = slots_by_index

    def _get_slots(self, cached=True):
        """

        :param cached:
        :return:
        """
        if self._slots is None or not cached:
            self._cache_slots()
        return self._slots

    def _get_free_slot(self):
        """

        :param cached:
        :return:
        """
        slot_indexes = sorted(self._slots_by_index.values())
        if len(slot_indexes) > 0:
            return slot_indexes[-1] + 1
        else:
            return 1

    def _set_slot(self, slot_index, slot):
        """

        :param slot_index:
        :param meta:
        :return:
        """
        assert type(slot_index) == int
        assert slot_index > 0 and slot_index < 65536
        assert slot is None or isinstance(slot, Slot)
        if slot:
            assert slot_index == slot.slot

        key = b'\0\0' + struct.pack('>H', slot_index)
        if slot:
            data = cbor2.dumps(slot.marshal())
            with self.begin(write=True) as txn:
                txn._txn.put(key, data)
                self._slots[slot.oid] = slot
                self._slots_by_index[slot.oid] = slot_index

            self.log.debug('Wrote metadata for table <{oid}> to slot {slot_index:03d}',
                           oid=slot.oid,
                           slot_index=slot_index)
        else:
            with self.begin(write=True) as txn:
                result = txn.get(key)
                if result:
                    txn._txn.delete(key)
                if slot.oid in self._slots:
                    del self._slots[slot.oid]
                if slot.oid in self._slots_by_index:
                    del self._slots_by_index[slot.oid]

            self.log.debug('Deleted metadata for table <{oid}> from slot {slot_index:03d}',
                           oid=slot.oid,
                           slot_index=slot_index)

    def attach_table(self, klass):
        """

        :param klass:
        :return:
        """
        if not inspect.isclass(klass):
            raise TypeError(
                'cannot attach object {} as database table: a subclass of zlmdb.PersistentMap is required'.format(
                    klass))

        name = qual(klass)

        if not issubclass(klass, _pmap.PersistentMap):
            raise TypeError(
                'cannot attach object of class {} as a database table: a subclass of zlmdb.PersistentMap is required'.
                format(name))

        if not hasattr(klass, '_zlmdb_oid') or not klass._zlmdb_oid:
            raise TypeError('{} is not decorated as table slot'.format(klass))

        description = klass.__doc__.strip() if klass.__doc__ else None

        if self._slots is None:
            self._cache_slots()

        pmap = self._attach_slot(klass._zlmdb_oid,
                                 klass,
                                 marshal=klass._zlmdb_marshal,
                                 parse=klass._zlmdb_parse,
                                 build=klass._zlmdb_build,
                                 cast=klass._zlmdb_cast,
                                 compress=klass._zlmdb_compress,
                                 create=True,
                                 name=name,
                                 description=description)
        return pmap

    def _attach_slot(self,
                     oid,
                     klass,
                     marshal=None,
                     parse=None,
                     build=None,
                     cast=None,
                     compress=None,
                     create=True,
                     name=None,
                     description=None):
        """

        :param slot:
        :param klass:
        :param marshal:
        :param unmarshal:
        :return:
        """
        assert isinstance(oid, uuid.UUID)
        assert issubclass(klass, _pmap.PersistentMap)

        assert marshal is None or callable(marshal)
        assert parse is None or callable(parse)

        assert build is None or callable(build)
        assert cast is None or callable(cast)

        # either marshal+parse (for CBOR/JSON) OR build+cast (for Flatbuffers) OR all unset
        assert (not marshal and not parse and not build and not cast) or \
               (not marshal and not parse and build and cast) or \
               (marshal and parse and not build and not cast)

        assert type(create) == bool

        assert name is None or type(name) == str
        assert (description is None or type(description) == str)

        if oid not in self._slots_by_index:
            self.log.debug('No slot found in database for DB table <{oid}>: <{name}>', name=name, oid=oid)
            if create:
                slot_index = self._get_free_slot()
                slot = Slot(oid=oid, creator='unknown', slot=slot_index, name=name, description=description)
                self._set_slot(slot_index, slot)
                self.log.info('Allocated new slot {slot_index:03d} for database table <{oid}>: {name}',
                              slot_index=slot_index,
                              oid=oid,
                              name=name)
            else:
                raise Exception('No slot found in database for DB table <{oid}>: {name}', name=name, oid=oid)
        else:
            slot_index = self._slots_by_index[oid]
            # pmap = _pmap.PersistentMap(slot_index)
            # with self.begin() as txn:
            #     records = pmap.count(txn)
            self.log.debug('Database table <{name}> attached [oid=<{oid}>, slot=<{slot_index:03d}>]',
                           name=name,
                           oid=oid,
                           slot_index=slot_index)

        if marshal:
            slot_pmap = klass(slot_index, marshal=marshal, unmarshal=parse, compress=compress)
        elif build:
            slot_pmap = klass(slot_index, build=build, cast=cast, compress=compress)
        else:
            slot_pmap = klass(slot_index, compress=compress)

        return slot_pmap
