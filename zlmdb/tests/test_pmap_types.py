import os
import sys
import pytest

import zlmdb

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.version_info >= (3, 6):
    from user_py3 import User, UsersSchema
else:
    from user_py2 import User, UsersSchema


@pytest.fixture(scope='function')
def dbfile():
    _dbfile = '.testdb'
    zlmdb.Database.scratch(_dbfile)
    return _dbfile


class TestSchema(zlmdb.Schema):

    def __init__(self):
        super(TestSchema, self).__init__()
        self.users = zlmdb.MapOidPickle(1)

        self.tab_uuid_str = zlmdb.MapUuidString(slot=1)
        self.tab_uuid_oid = zlmdb.MapUuidOid(slot=2)
        self.tab_uuid_uuid = zlmdb.MapUuidUuid(slot=3)

        self.tab_str_str = zlmdb.MapStringString(slot=4)
        self.tab_str_oid = zlmdb.MapStringOid(slot=5)
        self.tab_str_uuid = zlmdb.MapStringUuid(slot=6)

        self.tab_oid_str = zlmdb.MapOidString(slot=7)
        self.tab_oid_oid = zlmdb.MapOidOid(slot=8)
        self.tab_oid_uuid = zlmdb.MapOidUuid(slot=9)

        self.tab_uuid_json = zlmdb.MapUuidJson(slot=10, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_cbor = zlmdb.MapUuidCbor(slot=11, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_uuid_pickle = zlmdb.MapUuidPickle(slot=12)

        self.tab_str_json = zlmdb.MapStringJson(slot=20, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_cbor = zlmdb.MapStringCbor(slot=21, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_str_pickle = zlmdb.MapStringPickle(slot=22)

        self.tab_oid_json = zlmdb.MapOidJson(slot=30, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_cbor = zlmdb.MapOidCbor(slot=31, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
        self.tab_oid_pickle = zlmdb.MapOidPickle(slot=32)


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
