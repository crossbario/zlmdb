#############################################################################
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
import shutil
import tempfile
import uuid
import pprint
import struct
import inspect
import time
from typing import Dict, Any, Tuple, List, Optional, Callable, Type

import lmdb
import yaml
import cbor2

from zlmdb._transaction import Transaction, TransactionStats
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

_LMDB_MYPID_ENVS: Dict[str, Tuple['Database', int]] = {}


class ConfigurationElement(object):
    """
    Internal zLMDB configuration element base type.
    """

    __slots__ = (
        '_oid',
        '_name',
        '_description',
        '_tags',
    )

    def __init__(self,
                 oid: Optional[uuid.UUID] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        self._oid = oid
        self._name = name
        self._description = description
        self._tags = tags

    def __eq__(self, other: Any) -> bool:
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

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @property
    def oid(self) -> Optional[uuid.UUID]:
        return self._oid

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def tags(self) -> Optional[List[str]]:
        return self._tags

    def __str__(self) -> str:
        return pprint.pformat(self.marshal())

    def marshal(self) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            'oid': str(self._oid),
            'name': self._name,
        }
        if self.description:
            value['description'] = self._description
        if self.tags:
            value['tags'] = self._tags
        return value

    @staticmethod
    def parse(value: Dict[str, Any]) -> 'ConfigurationElement':
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
    """
    Internal zLMDB database slot configuration element.
    """

    __slots__ = (
        '_slot',
        '_creator',
    )

    def __init__(self,
                 oid: Optional[uuid.UUID] = None,
                 name: Optional[str] = None,
                 description: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 slot: Optional[int] = None,
                 creator: Optional[str] = None):
        ConfigurationElement.__init__(self, oid=oid, name=name, description=description, tags=tags)
        self._slot = slot
        self._creator = creator

    @property
    def creator(self) -> Optional[str]:
        return self._creator

    @property
    def slot(self) -> Optional[int]:
        return self._slot

    def __str__(self) -> str:
        return pprint.pformat(self.marshal())

    def marshal(self) -> Dict[str, Any]:
        obj = ConfigurationElement.marshal(self)
        obj.update({
            'creator': self._creator,
            'slot': self._slot,
        })
        return obj

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'Slot':
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
            _meta = yaml.safe_load(f.read())

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
    __slots__ = (
        'log',
        '_is_temp',
        '_tempdir',
        '_dbpath',
        '_maxsize',
        '_readonly',
        '_lock',
        '_sync',
        '_create',
        '_open_now',
        '_writemap',
        '_context',
        '_slots',
        '_slots_by_index',
        '_env',
    )

    def __init__(self,
                 dbpath: Optional[str] = None,
                 maxsize: int = 10485760,
                 readonly: bool = False,
                 lock: bool = True,
                 sync: bool = True,
                 create: bool = True,
                 open_now: bool = True,
                 writemap: bool = False,
                 context: Any = None,
                 log: Optional[txaio.interfaces.ILogger] = None):
        """

        :param dbpath: LMDB database path: a directory with (at least) 2 files, a ``data.mdb`` and a ``lock.mdb``.
            If no database exists at the given path, create a new one.
        :param maxsize: Database size limit in bytes, with a default of 1MB.
        :param readonly: Open database read-only. When ``True``, deny any modifying database operations.
            Note that the LMDB lock file (``lock.mdb``) still needs to be written (by readers also),
            and hence at the filesystem level, a LMDB database directory must be writable.
        :param sync: Open database with sync on commit.
        :param create: Automatically create database if it does not yet exist.
        :param open_now: Open the database immediately (within this constructor).
        :param writemap: Use direct write to mmap'ed database rather than regular file IO writes. Be careful when
            using any storage other than locally attached filesystem/drive.
        :param context: Optional context within which this database instance is created.
        :param log: Log object to use for logging from this class.
        """
        self._context = context

        if log:
            self.log = log
        else:
            if not txaio._explicit_framework:
                txaio.use_asyncio()
            self.log = txaio.make_logger()

        if dbpath:
            self._is_temp = False
            self._tempdir = None
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
        self._open_now = open_now
        self._writemap = writemap
        self._context = context

        self._slots: Optional[Dict[uuid.UUID, Slot]] = None
        self._slots_by_index: Optional[Dict[uuid.UUID, int]] = None

        # in a context manager environment we initialize with LMDB handle
        # when we enter the actual temporary, managed context ..
        self._env: Optional[lmdb.Environment] = None

        # in a direct run environment, we immediately open LMDB
        if self._open_now:
            self.__enter__()

    def __enter__(self):
        """
        Enter database runtime context and open the underlying LMDB database environment.

        .. note::

            Enter the runtime context related to this object. The with statement will bind this method’s
            return value to the target(s) specified in the as clause of the statement, if any.
            [Source](https://docs.python.org/3/reference/datamodel.html#object.__enter__)

        .. note::

            A context manager is an object that defines the runtime context to be established when
            executing a with statement. The context manager handles the entry into, and the exit from,
            the desired runtime context for the execution of the block of code. Context managers are
            normally invoked using the with statement (described in section The with statement), but
            can also be used by directly invoking their methods."
            [Source](https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers)

        :return: This database instance (in open state).
        """
        if not self._env:
            # protect against opening the same database file multiple times within the same process:
            #    "It is a serious error to have open (multiple times) the same LMDB file in
            #     the same process at the same time. Failure to heed this may lead to data
            #     corruption and interpreter crash."
            #    https://lmdb.readthedocs.io/en/release/#environment-class

            if not self._is_temp:
                if self._dbpath in _LMDB_MYPID_ENVS:
                    other_obj, other_pid = _LMDB_MYPID_ENVS[self._dbpath]
                    raise RuntimeError(
                        'tried to open same dbpath "{}" twice within same process: cannot open database '
                        'for {} (PID {}, Context {}), already opened in {} (PID {}, Context {})'.format(
                            self._dbpath, self, os.getpid(), self.context, other_obj, other_pid, other_obj.context))
                _LMDB_MYPID_ENVS[self._dbpath] = self, os.getpid()

            # handle lmdb.LockError: mdb_txn_begin: Resource temporarily unavailable
            #   "The environment was locked by another process."
            #   https://lmdb.readthedocs.io/en/release/#lmdb.LockError

            # count number of retries
            retries = 0
            # delay (in seconds) before retrying
            retry_delay = 0
            while True:
                try:
                    # https://lmdb.readthedocs.io/en/release/#lmdb.Environment
                    # https://lmdb.readthedocs.io/en/release/#writemap-mode
                    # map_size: Maximum size database may grow to; used to size the memory mapping.
                    # lock=True is needed for concurrent access, even when only by readers (because of space mgmt)
                    self._env = lmdb.open(self._dbpath,
                                          map_size=self._maxsize,
                                          create=self._create,
                                          readonly=self._readonly,
                                          sync=self._sync,
                                          subdir=True,
                                          lock=self._lock,
                                          writemap=self._writemap)

                    # ok, good: we've got a LMDB env
                    break

                # see https://github.com/crossbario/zlmdb/issues/53
                except lmdb.LockError as e:
                    retries += 1
                    if retries >= 3:
                        # give up and signal to user code
                        raise RuntimeError('cannot open LMDB environment (giving up '
                                           'after {} retries): {}'.format(retries, e))

                    # use synchronous (!) sleep (1st time is sleep(0), which releases execution of this process to OS)
                    time.sleep(retry_delay)

                    # increase sleep time by 10ms _next_ time. that is, for our 3 attempts
                    # the delays are: 0ms, 10ms, 20ms
                    retry_delay += 0.01

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit runtime context and close the underlying LMDB database environment.

        .. note::

            Exit the runtime context related to this object. The parameters describe the exception that
            caused the context to be exited. If the context was exited without an exception, all three
            arguments will be None.
            [Source](https://docs.python.org/3/reference/datamodel.html#object.__exit__).

        :param exc_type:
        :param exc_value:
        :param traceback:
        :return:
        """
        if self._env:
            self._env.close()
            self._env = None
            if not self._is_temp and self._dbpath in _LMDB_MYPID_ENVS:
                del _LMDB_MYPID_ENVS[self._dbpath]

    @staticmethod
    def open(dbpath: Optional[str] = None,
             maxsize: int = 10485760,
             readonly: bool = False,
             lock: bool = True,
             sync: bool = True,
             create: bool = True,
             open_now: bool = True,
             writemap: bool = False,
             context: Any = None,
             log: Optional[txaio.interfaces.ILogger] = None) -> 'Database':
        if dbpath is not None and dbpath in _LMDB_MYPID_ENVS:
            db, _ = _LMDB_MYPID_ENVS[dbpath]
            print(
                '{}: reusing database instance for path "{}" in new context {} already opened from (first) context {}'.
                format(Database.open, dbpath, context, db.context))
        else:
            db = Database(dbpath=dbpath,
                          maxsize=maxsize,
                          readonly=readonly,
                          lock=lock,
                          sync=sync,
                          create=create,
                          open_now=open_now,
                          writemap=writemap,
                          context=context,
                          log=log)
            print('{}: creating new database instance for path "{}" in context {}'.format(
                Database.open, dbpath, context))
        return db

    @property
    def context(self):
        """

        :return:
        """
        return self._context

    @property
    def dbpath(self) -> Optional[str]:
        """

        :return:
        """
        return self._dbpath

    @property
    def maxsize(self) -> int:
        """

        :return:
        """
        return self._maxsize

    @property
    def is_sync(self) -> bool:
        """

        :return:
        """
        return self._sync

    @property
    def is_readonly(self) -> bool:
        """

        :return:
        """
        return self._readonly

    @property
    def is_writemap(self) -> bool:
        """

        :return:
        """
        return self._writemap

    @property
    def is_open(self) -> bool:
        """

        :return:
        """
        return self._env is not None

    @staticmethod
    def scratch(dbpath: str):
        """

        :param dbpath:
        :return:
        """
        if os.path.exists(dbpath):
            if os.path.isdir(dbpath):
                shutil.rmtree(dbpath)
            else:
                os.remove(dbpath)

    def begin(self,
              write: bool = False,
              buffers: bool = False,
              stats: Optional[TransactionStats] = None) -> Transaction:
        """

        :param write:
        :param buffers:
        :param stats:
        :return:
        """
        assert self._env is not None

        if write and self._readonly:
            raise Exception('database is read-only')

        txn = Transaction(db=self, write=write, buffers=buffers, stats=stats)
        return txn

    def sync(self, force: bool = False):
        """

        :param force:
        :return:
        """
        assert self._env is not None

        self._env.sync(force=force)

    def config(self) -> Dict[str, Any]:
        """

        :return:
        """
        res = {
            'is_temp': self._is_temp,
            'dbpath': self._dbpath,
            'maxsize': self._maxsize,
            'readonly': self._readonly,
            'lock': self._lock,
            'sync': self._sync,
            'create': self._create,
            'open_now': self._open_now,
            'writemap': self._writemap,
            'context': str(self._context) if self._context else None,
        }
        return res

    def stats(self, include_slots: bool = False) -> Dict[str, Any]:
        """

        :param include_slots:
        :return:
        """
        assert self._env is not None

        current_size = os.path.getsize(os.path.join(self._dbpath, 'data.mdb'))

        # psize 	        Size of a database page in bytes.
        # depth 	        Height of the B-tree.
        # branch_pages 	    Number of internal (non-leaf) pages.
        # leaf_pages 	    Number of leaf pages.
        # overflow_pages 	Number of overflow pages.
        # entries 	        Number of data items.
        stats = self._env.stat()
        pages = stats['leaf_pages'] + stats['overflow_pages'] + stats['branch_pages']
        used = stats['psize'] * pages

        self._cache_slots()
        res: Dict[str, Any] = {
            'num_slots': len(self._slots) if self._slots else 0,
            'current_size': current_size,
            'max_size': self._maxsize,
            'page_size': stats['psize'],
            'pages': pages,
            'used': used,
            'free': 1. - float(used) / float(self._maxsize),
            'read_only': self._readonly,
            'sync_enabled': self._sync,
        }
        res.update(stats)

        # map_addr 	        Address of database map in RAM.
        # map_size 	        Size of database map in RAM.
        # last_pgno 	    ID of last used page.
        # last_txnid 	    ID of last committed transaction.
        # max_readers 	    Number of reader slots allocated in the lock file. Equivalent to the value of
        #                   maxreaders= specified by the first process opening the Environment.
        # num_readers 	    Maximum number of reader slots in simultaneous use since the lock file was initialized.
        res.update(self._env.info())

        if include_slots:
            slots = self._get_slots()
            res['slots'] = []
            with self.begin() as txn:
                for slot_id in slots:
                    slot = slots[slot_id]
                    pmap = _pmap.PersistentMap(slot.slot)
                    res['slots'].append({
                        'oid': str(slot_id),
                        'slot': slot.slot,
                        'name': slot.name,
                        'description': slot.description,
                        'records': pmap.count(txn),
                    })

        return res

    def _cache_slots(self):
        """

        :return:
        """
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

    def _get_slots(self, cached=True) -> Dict[uuid.UUID, Slot]:
        """

        :param cached:
        :return:
        """
        if self._slots is None or not cached:
            self._cache_slots()
        assert self._slots
        return self._slots

    def _get_free_slot(self) -> int:
        """

        :return:
        """
        if self._slots_by_index is None:
            self._cache_slots()
        assert self._slots_by_index is not None
        slot_indexes = sorted(self._slots_by_index.values())
        if len(slot_indexes) > 0:
            return slot_indexes[-1] + 1
        else:
            return 1

    def _set_slot(self, slot_index: int, slot: Optional[Slot]):
        """

        :param slot_index:
        :param slot:
        :return:
        """
        assert type(slot_index) == int
        assert 0 < slot_index < 65536
        assert slot is None or isinstance(slot, Slot)

        if self._slots is None:
            self._cache_slots()
        assert self._slots is not None
        assert self._slots_by_index is not None

        key = b'\0\0' + struct.pack('>H', slot_index)
        if slot:
            assert slot_index == slot.slot
            assert slot.oid

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
                    slot = Slot.parse(cbor2.loads(result))
                    if slot.oid in self._slots:
                        del self._slots[slot.oid]
                    if slot.oid in self._slots_by_index:
                        del self._slots_by_index[slot.oid]

                    self.log.debug('Deleted metadata for table <{oid}> from slot {slot_index:03d}',
                                   oid=slot.oid,
                                   slot_index=slot_index)

    def attach_table(self, klass: Type[_pmap.PersistentMap]):
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
                     oid: uuid.UUID,
                     klass: Type[_pmap.PersistentMap],
                     marshal: Optional[Callable] = None,
                     parse: Optional[Callable] = None,
                     build: Optional[Callable] = None,
                     cast: Optional[Callable] = None,
                     compress: Optional[int] = None,
                     create: bool = True,
                     name: Optional[str] = None,
                     description: Optional[str] = None):
        """

        :param oid:
        :param klass:
        :param marshal:
        :param parse:
        :param build:
        :param cast:
        :param compress:
        :param create:
        :param name:
        :param description:
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

        assert compress is None or compress in [_pmap.PersistentMap.COMPRESS_ZLIB, _pmap.PersistentMap.COMPRESS_SNAPPY]
        assert type(create) == bool
        assert name is None or type(name) == str
        assert description is None or type(description) == str

        assert self._slots_by_index is not None

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
                raise RuntimeError('No slot found in database for DB table <{}>: "{}"'.format(oid, name))
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
            slot_pmap = klass(slot_index, marshal=marshal, unmarshal=parse, compress=compress)  # type: ignore
        elif build:
            slot_pmap = klass(slot_index, build=build, cast=cast, compress=compress)  # type: ignore
        else:
            slot_pmap = klass(slot_index, compress=compress)

        return slot_pmap
