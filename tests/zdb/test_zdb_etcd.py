import six
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted import util

import txaio
from txaioetcd import Client, KeySet

import yaml

from pprint import pprint, pformat
import random

import zlmdb
from zlmdb._pmap import  MapStringString


try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory



class MySchema(zlmdb.Schema):

    samples: MapStringString

    def __init__(self):
        self.samples = MapStringString(1)


@inlineCallbacks
def main(reactor):
    if True:
        with TemporaryDirectory() as dbpath:
            print('Using temporary directory {} for database'.format(dbpath))

            schema = MySchema()

            with zlmdb.Database(dbpath) as db:
                # write records into zlmdb
                with db.begin(write=True) as txn:
                    for i in range(10):
                        key = 'key{}'.format(i)
                        value = 'value{}'.format(random.randint(0, 1000))
                        schema.samples[txn, key] = value

                # read records from zlmdb
                with db.begin() as txn:
                    for i in range(10):
                        key = 'key{}'.format(i)
                        value = schema.samples[txn, key]
                        print('key={} : value={}'.format(key, value))

    if True:
        # etcd database
        etcd = Client(reactor)
        status = yield etcd.status()
        print(status)

        # zlmdb database
        schema = MySchema()
        dbpath = '/tmp/.test-zlmdb'

        with zlmdb.Database(dbpath) as db:
            print('zlmdb open on {}'.format(dbpath))

            # check current record count
            with db.begin() as txn:
                cnt = schema.samples.count(txn)
                print('currently {} rows in table'.format(cnt))

            # watch changes in etcd and write to local zlmdb
            def on_change(kv):
                key = kv.key.decode()
                value = kv.value.decode()
                with db.begin(write=True) as txn:
                    schema.samples[txn, key] = value
                print('on_change received from etcd and written to zlmdb: key={} value={}'.format(key, value))

            # start watching for etcd changes ..
            ks = [KeySet('k'.encode(), prefix=True)]
            d = etcd.watch(ks, on_change)

            print('watching for 1s ..')
            yield txaio.sleep(1)

            # loop every 1s and write a key-value in etcd directly
            for i in range(5):
                print('watching for 1s ..')
                yield txaio.sleep(1)

                key = 'key{}'.format(i).encode()
                value = 'value{}'.format(random.randint(0, 1000)).encode()

                etcd.set(key, value)

            # cancel our watch
            d.cancel()

            yield util.sleep(1)

            # check current record count
            with db.begin() as txn:
                cnt = schema.samples.count(txn)
                print('currently {} rows in table'.format(cnt))

            yield util.sleep(1)


if __name__ == '__main__':
    txaio.start_logging(level='info')
    react(main)
