import os
import sys
import shutil
import random
import lmdb
import pytest
import uuid
import datetime

from zlmdb import BaseTransaction, \
                  TransactionStats, \
                  MapUuidString, \
                  MapUuidOid, \
                  MapUuidUuid, \
                  MapUuidJson, \
                  MapUuidCbor, \
                  MapUuidPickle, \
                  MapStringString, \
                  MapStringOid, \
                  MapStringUuid, \
                  MapStringJson, \
                  MapStringCbor, \
                  MapStringPickle, \
                  MapOidString, \
                  MapOidOid, \
                  MapOidUuid, \
                  MapOidJson, \
                  MapOidCbor, \
                  MapOidPickle

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from user_typed import User
else:
    from user import User


DBNAME = '.test-db1'


class Schema(object):
    pass


class MySchema(Schema):
    def __init__(self):
        self.tab_uuid_json = MapUuidJson(slot=10, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_cbor = MapUuidCbor(slot=11, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_pickle = MapUuidPickle(slot=12)

        self.tab_str_json = MapStringJson(slot=20, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_cbor = MapStringCbor(slot=21, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_pickle = MapStringPickle(slot=22)

        self.tab_oid_json = MapOidJson(slot=30, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_cbor = MapOidCbor(slot=31, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_pickle = MapOidPickle(slot=32)




class Transaction(BaseTransaction):

    def __init__(self, *args, **kwargs):
        BaseTransaction.__init__(self, *args, **kwargs)

        if False:
            self.tab_uuid_str = MapUuidString(slot=1)
            self.tab_uuid_oid = MapUuidOid(slot=2)
            self.tab_uuid_uuid = MapUuidUuid(slot=3)

            self.tab_str_str = MapStringString(slot=4)
            self.tab_str_oid = MapStringOid(slot=5)
            self.tab_str_uuid = MapStringUuid(slot=6)

            self.tab_oid_str = MapOidString(slot=7)
            self.tab_oid_oid = MapOidOid(slot=8)
            self.tab_oid_uuid = MapOidUuid(slot=9)

        self.tab_uuid_json = MapUuidJson(slot=10, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_cbor = MapUuidCbor(slot=11, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_pickle = MapUuidPickle(slot=12)

        self.tab_str_json = MapStringJson(slot=20, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_cbor = MapStringCbor(slot=21, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_pickle = MapStringPickle(slot=22)

        self.tab_oid_json = MapOidJson(slot=30, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_cbor = MapOidCbor(slot=31, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_pickle = MapOidPickle(slot=32)

    def attach(self):
        if False:
            self.tab_uuid_str.attach_transaction(self)
            self.tab_uuid_oid.attach_transaction(self)
            self.tab_uuid_uuid.attach_transaction(self)

            self.tab_str_str.attach_transaction(self)
            self.tab_str_oid.attach_transaction(self)
            self.tab_str_uuid.attach_transaction(self)

            self.tab_oid_str.attach_transaction(self)
            self.tab_oid_oid.attach_transaction(self)
            self.tab_oid_uuid.attach_transaction(self)

        self.tab_uuid_json.attach_transaction(self)
        self.tab_uuid_cbor.attach_transaction(self)
        self.tab_uuid_pickle.attach_transaction(self)

        self.tab_str_json.attach_transaction(self)
        self.tab_str_cbor.attach_transaction(self)
        self.tab_str_pickle.attach_transaction(self)

        self.tab_oid_json.attach_transaction(self)
        self.tab_oid_cbor.attach_transaction(self)
        self.tab_oid_pickle.attach_transaction(self)


@pytest.fixture(scope='function')
def env():
    if os.path.exists(DBNAME):
        if os.path.isdir(DBNAME):
            shutil.rmtree(DBNAME)
        else:
            os.remove(DBNAME)
    env = lmdb.open(DBNAME)
    return env


def _create_test_user():
    user = User()
    user.oid = random.randint(0, 2**64-1)
    user.name = 'Test {}'.format(user.oid)
    user.authid = 'test-{}'.format(user.oid)
    user.uuid = uuid.uuid4()
    user.email = '{}@example.com'.format(user.authid)
    user.birthday = datetime.date(1950, 12, 24)
    user.is_friendly = True
    user.tags = ['relaxed', 'beerfan']
    for j in range(10):
        user.ratings['test-rating-{}'.format(j)] = random.random()
    return user


def test_pmap_json_values(env):
    n = 100

    stats = TransactionStats()

    with Transaction(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user()

            txn.tab_oid_json[user.oid] = user
            txn.tab_str_json[user.authid] = user
            txn.tab_uuid_json[user.uuid] = user

    assert stats.puts == n * 3
    assert stats.dels == 0

    stats.reset()

    with Transaction(env) as txn:
        for tab in [txn.tab_oid_json,
                    txn.tab_str_json,
                    txn.tab_uuid_json]:
            rows = tab.count()
            assert rows == n


def test_pmap_pickle_values(env):
    n = 100

    stats = TransactionStats()

    with Transaction(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user()

            txn.tab_oid_pickle[user.oid] = user
            txn.tab_str_pickle[user.authid] = user
            txn.tab_uuid_pickle[user.uuid] = user

    assert stats.puts == n * 3
    assert stats.dels == 0

    stats.reset()

    with Transaction(env) as txn:
        for tab in [txn.tab_oid_pickle,
                    txn.tab_str_pickle,
                    txn.tab_uuid_pickle]:
            rows = tab.count()
            assert rows == n


def test_pmap_cbor_values(env):
    n = 100

    stats = TransactionStats()

    with Transaction(env, write=True, stats=stats) as txn:
        for i in range(n):
            user = _create_test_user()

            txn.tab_oid_cbor[user.oid] = user
            txn.tab_str_cbor[user.authid] = user
            txn.tab_uuid_cbor[user.uuid] = user

    assert stats.puts == n * 3
    assert stats.dels == 0

    stats.reset()

    with Transaction(env) as txn:
        for tab in [txn.tab_oid_cbor,
                    txn.tab_str_cbor,
                    txn.tab_uuid_cbor]:
            rows = tab.count()
            assert rows == n
