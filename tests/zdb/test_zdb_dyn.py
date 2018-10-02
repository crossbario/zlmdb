import six
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted import util

import txaio
from txaioetcd import Client, KeySet

import yaml

from pprint import pprint, pformat

import numpy as np
import pandas as pd
import pyarrow as pa
import lmdb

import zlmdb
from zlmdb._pmap import _StringKeysMixin, PersistentMap
from zlmdb._pmap import  MapStringJson, MapStringCbor, MapUuidJson, MapUuidCbor

import random
import uuid
import datetime
from typing import Optional, List, Dict


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




class Tag(object):
    GEEK = 1
    VIP = 2




class User(object):
    oid: int
    name: str
    authid: str
    uuid: uuid.UUID
    email: str
    birthday: datetime.date
    is_friendly: bool
    tags: Optional[List[str]]
    ratings: Dict[str, float] = {}
    friends: List[int] = []
    referred_by: int = None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if other.oid != self.oid:
            return False
        if other.name != self.name:
            return False
        if other.authid != self.authid:
            return False
        if other.uuid != self.uuid:
            return False
        if other.email != self.email:
            return False
        if other.birthday != self.birthday:
            return False
        if other.is_friendly != self.is_friendly:
            return False
        if (self.tags and not other.tags) or (not self.tags and other.tags):
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return '\n{}\n'.format(pformat(self.marshal()))

    def marshal(self):
        obj = {
            'oid': self.oid,
            'name': self.name,
            'authid': self.authid,
            'uuid': self.uuid.hex if self.uuid else None,
            'email': self.email,
            'birthday': {
                'year': self.birthday.year if self.birthday else None,
                'month': self.birthday.month if self.birthday else None,
                'day': self.birthday.day if self.birthday else None,
            },
            'is_friendly': self.is_friendly,
            'tags': self.tags,
            'ratings': self.ratings,
            'friends': self.friends,
            'referred_by': self.referred_by,
        }
        return obj

    @staticmethod
    def parse(obj):
        user = User()
        user.oid = obj.get('oid', None)
        user.name = obj.get('name', None)
        user.authid = obj.get('authid', None)
        if 'uuid' in obj:
            user.uuid = uuid.UUID(hex=obj['uuid'])
        user.email = obj.get('email', None)
        if 'birthday' in obj:
            b = obj['birthday']
            user.birthday = datetime.date(b.get('year', None), b.get('month', None), b.get('day', None))
        user.is_friendly = obj.get('is_friendly', None)
        user.tags = obj.get('tags', None)
        user.ratings = obj.get('ratings', {})
        user.friends = obj.get('friends', [])
        user.referred_by = obj.get('referred_by', None)
        return user

    @staticmethod
    def create_test_user(oid=None):
        user = User()
        if oid is not None:
            user.oid = oid
        else:
            user.oid = random.randint(0, 9007199254740992)
        user.name = 'Test {}'.format(user.oid)
        user.authid = 'test-{}'.format(user.oid)
        user.uuid = uuid.uuid4()
        user.email = '{}@example.com'.format(user.authid)
        user.birthday = datetime.date(1950, 12, 24)
        user.is_friendly = True
        user.tags = ['geek', 'sudoko', 'yellow']
        for j in range(10):
            user.ratings['test-rating-{}'.format(j)] = random.random()
        user.friends = [random.randint(0, 9007199254740992) for _ in range(10)]
        user.referred_by = random.randint(0, 9007199254740992)
        return user



KV_TYPE_TO_CLASS = {
    'string-json': (MapStringJson, lambda x: x, lambda x: x),
    'string-json-user': (MapStringJson, User.marshal, User.parse),
    'string-cbor-user': (MapStringCbor, User.marshal, User.parse),
    'uuid-json-user': (MapUuidJson, User.marshal, User.parse),
    'uuid-cbor-user': (MapUuidCbor, User.marshal, User.parse),
}

@inlineCallbacks
def main(reactor):
    dbpath = '/tmp/zlmdb1'

    print('Using database directory {}'.format(dbpath))

    meta = {}
    slots = {}
    slots_byname = {}

    with open('tests/zdb/zdb.yml') as f:
        _meta = yaml.load(f.read())

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
        _kv_klass, _marshal, _unmarshal = KV_TYPE_TO_CLASS.get(_kv_type, (None, None, None))
        assert _kv_klass
        assert _marshal
        assert _unmarshal

        _table = _kv_klass(_index, marshal=_marshal, unmarshal=_unmarshal)
        slots[_index] = _table
        slots_byname[_name] = _table

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

    with zlmdb.Database(dbpath) as db:
        with db.begin(write=True) as txn:
            users = slots_byname['users']
            #users = slots_byname['foobar']
            mrealms = slots_byname['mrealms']

            key = 'user1'
            user = users[txn, key]
            if user:
                print('user object already exists for key {}: {}'.format(key, user))
            else:
                print('user does not exist, storing new object ..')

                user = User.create_test_user()
                #user = User.create_test_user().marshal()
                users[txn, key] = user

                print('user object created for key {}: {}'.format(key, user))

    yield util.sleep(1)


if __name__ == '__main__':
    txaio.start_logging(level='info')
    react(main)
