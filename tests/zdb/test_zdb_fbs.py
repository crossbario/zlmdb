import six
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
import txaio
txaio.use_twisted()
from autobahn.twisted import util

import os
import sys
import random

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _schema_fbs import User as UserFbs  # noqa


class UsersSchema(zlmdb.Schema):
    def __init__(self):
        self.tab_oid_fbs = zlmdb.MapOidFlatBuffers(1, build=UserFbs.build, cast=UserFbs.cast)


@inlineCallbacks
def main2(reactor):
    dbpath = '/tmp/zlmdb1'

    print('Using database directory {}'.format(dbpath))

    schema = UsersSchema()

    with zlmdb.Database(dbpath) as db:

        N = 1000
        with db.begin() as txn:
            cnt_begin = schema.tab_oid_fbs.count(txn)

        stats = zlmdb.TransactionStats()

        with db.begin(write=True, stats=stats) as txn:
            for i in range(N):
                user = UserFbs.create_test_user()
                schema.tab_oid_fbs[txn, user.oid] = user

        assert stats.puts == N
        assert stats.dels == 0
        stats.reset()

        with db.begin() as txn:
            cnt_end = schema.tab_oid_fbs.count(txn)

        cnt = cnt_end - cnt_begin
        assert cnt == N

        print('{} records written, {} records total'.format(cnt, cnt_end))

    yield util.sleep(1)


if __name__ == '__main__':
    txaio.start_logging(level='info')
    react(main2)
