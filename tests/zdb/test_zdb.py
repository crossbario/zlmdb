import six
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted import util

import txaio
from txaioetcd import Client, KeySet

import yaml

from pprint import pprint

import numpy as np
import pandas as pd
import pyarrow as pa
import lmdb

import zlmdb
from zlmdb._pmap import _StringKeysMixin, PersistentMap
from zlmdb._pmap import  MapStringJson, MapStringCbor, MapUuidJson, MapUuidCbor


try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory


class _DataFrameValuesMixin(object):
    def __init__(self, marshal=None, unmarshal=None):
        self._marshal = marshal or self._zlmdb_marshal
        self._unmarshal = unmarshal or self._zlmdb_unmarshal

    def _serialize_value(self, value):
        return pa.serialize(value).to_buffer()

    def _deserialize_value(self, data):
        return pa.deserialize(data)


class MapStringDataFrame(_StringKeysMixin, _DataFrameValuesMixin, PersistentMap):
    """
    Persistent map with string (utf8) keys and OID (uint64) values.
    """

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MySchema(zlmdb.Schema):

    samples: MapStringDataFrame

    def __init__(self):
        self.samples = MapStringDataFrame(1)


# dtypes - https://pandas.pydata.org/pandas-docs/stable/basics.html#basics-dtypes
#
# The main types stored in pandas objects are float, int, bool, datetime64[ns] and
# datetime64[ns, tz], timedelta[ns], category and object. In addition these dtypes
# have item sizes, e.g. int64 and int32.

# Key Types:
#
#  * OID (64 bit)
#  * UUID (128 bit)
#  * SHA256 (256 bit)
#  * String (arbitrary length)
#
#  * OID-OID
#  * OID-UUID
#  * OID-String
#
#  * UUID-OID
#  * UUID-UUID
#  * UUID-String

#
# Value Types: String, OID, UUID, JSON, CBOR, Pickle, FlatBuffers
#


@inlineCallbacks
def main2(reactor):
    etcd = Client(reactor)
    status = yield etcd.status()
    print(status)

    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = MySchema()

        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for i in range(10):
                    if i % 2:
                        key = 'key{}'.format(i)
                        value = pd.DataFrame(np.random.randn(8, 4), columns=['A','B','C','D'])
                        schema.samples[txn, key] = value

        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for i in range(10):
                    key = 'key{}'.format(i)
                    value = schema.samples[txn, key]
                    print('key={} : value=\n{}'.format(key, value))


    def on_change(kv):
        key = kv.key.decode()
        df = pa.deserialize(kv.value)
        print('on_change: value={} key=\n{}'.format(key, df))

    ks = [KeySet('k'.encode(), prefix=True)]
    d = etcd.watch(ks, on_change)

    for i in range(5):
        print('watching for 1s ..')
        yield txaio.sleep(1)

        key = 'key{}'.format(i).encode()

        df = pd.DataFrame(np.random.randn(8, 4), columns=['A','B','C','D'])
        value = pa.serialize(df).to_buffer()

        etcd.set(key, value)

    print('watching for 1s ..')
    yield txaio.sleep(1)

    d.cancel()


KV_TYPE_TO_CLASS = {
    'string-json': MapStringJson,
    'string-cbor': MapStringCbor,
    'uuid-json': MapUuidJson,
    'uuid-cbor': MapUuidCbor,
}

@inlineCallbacks
def main(reactor):
    dbpath = '/tmp/zlmdb1'

    print('Using database directory {}'.format(dbpath))

    meta = {}
    slots = {}

    with open('tests/zdb/zdb.yml') as f:
        _meta = yaml.load(f.read())

    for slot in _meta.get('slots', []):
        _index = slot.get('index', None)
        assert type(_index) in six.integer_types and _index >= 100 and _index < 65536
        assert _index not in slots

        _name = slot.get('name', None)
        assert type(_name) == six.text_type

        _key = slot.get('key', None)
        assert _key in ['string', 'uuid']

        _value = slot.get('value', None)
        assert _value in ['json', 'cbor']

        _description = slot.get('description', None)
        assert _description is None or type(_description) == six.text_type

        _kv_type = '{}-{}'.format(_key, _value)
        _kv_klass = KV_TYPE_TO_CLASS.get(_kv_type, None)
        assert _kv_klass

        slots[_index] = _kv_klass(_index)
        meta[_index] = {
            'index': _index,
            'name': _name,
            'key': _key,
            'value': _value,
            'impl': _kv_klass.__name__,
            'description': _description,
        }

    pprint(meta)
    pprint(slots)


    schema = MySchema()

    if False:
        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for i in range(10):
                    if i % 2:
                        key = 'key{}'.format(i)
                        value = pd.DataFrame(np.random.randn(8, 4), columns=['A','B','C','D'])
                        schema.samples[txn, key] = value

    if False:
        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for i in range(10):
                    key = 'key{}'.format(i)
                    value = schema.samples[txn, key]
                    print('key={} : value=\n{}'.format(key, value))

    yield util.sleep(1)


if __name__ == '__main__':
    txaio.start_logging(level='info')
    react(main)
