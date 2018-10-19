import six

from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks

import txaio
from autobahn.twisted import util

import numpy as np
import pandas as pd
import pyarrow as pa

import zlmdb
from zlmdb._pmap import _StringKeysMixin, PersistentMap


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

    def __init__(self, slot=None, compress=None):
        PersistentMap.__init__(self, slot=slot, compress=compress)


class MySchema(zlmdb.Schema):

    samples: MapStringDataFrame

    def __init__(self):
        self.samples = MapStringDataFrame(1)


@inlineCallbacks
def main(reactor):

    with TemporaryDirectory() as dbpath:
        print('Using temporary directory {} for database'.format(dbpath))

        schema = MySchema()
        db = zlmdb.Database(dbpath)

        # WRITE some native pandas data frames to zlmdb
        with db.begin(write=True) as txn:
            for i in range(10):
                if i % 2:
                    key = 'key{}'.format(i)
                    value = pd.DataFrame(np.random.randn(8, 4),
                                         columns=['A','B','C','D'])
                    schema.samples[txn, key] = value

        # READ back native pandas data frames from zlmdb
        with db.begin() as txn:
            for i in range(10):
                key = 'key{}'.format(i)
                value = schema.samples[txn, key]
                print('key={} : value=\n{}'.format(key, value))

    yield util.sleep(1)


if __name__ == '__main__':
    txaio.start_logging(level='info')
    react(main)
