import random
import uuid
import datetime
from typing import Optional, List, Dict

import zlmdb


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
            user.birthday = datetime.date(b.year, b.month, b.day)
        user.is_friendly = obj.get('is_friendly', None)
        user.tags = obj.get('tags', None)
        user.ratings = obj.get('ratings', {})
        user.friends = obj.get('friends', [])
        user.referred_by = obj.get('referred_by', None)
        return user

    @staticmethod
    def create_test_user(oid=None):
        user = User()
        user.oid = oid or random.randint(0, 2**64-1)
        user.name = 'Test {}'.format(user.oid)
        user.authid = 'test-{}'.format(user.oid)
        user.uuid = uuid.uuid4()
        user.email = '{}@example.com'.format(user.authid)
        user.birthday = datetime.date(1950, 12, 24)
        user.is_friendly = True
        user.tags = ['geek', 'sudoko', 'yellow']
        for j in range(10):
            user.ratings['test-rating-{}'.format(j)] = random.random()
        return user


class Schema1(zlmdb.Schema):

    tab_uuid_str: zlmdb.MapUuidString = zlmdb.MapUuidString(slot=1)
    tab_uuid_oid: zlmdb.MapUuidOid = zlmdb.MapUuidOid(slot=2)
    tab_uuid_uuid: zlmdb.MapUuidUuid = zlmdb.MapUuidUuid(slot=3)
    tab_str_str: zlmdb.MapStringString = zlmdb.MapStringString(slot=4)
    tab_str_oid: zlmdb.MapStringOid = zlmdb.MapStringOid(slot=5)
    tab_str_uuid: zlmdb.MapStringUuid = zlmdb.MapStringUuid(slot=6)
    tab_oid_str: zlmdb.MapOidString = zlmdb.MapOidString(slot=7)
    tab_oid_oid: zlmdb.MapOidOid = zlmdb.MapOidOid(slot=8)
    tab_oid_uuid: zlmdb.MapOidUuid = zlmdb.MapOidUuid(slot=9)
    tab_uuid_json: zlmdb.MapUuidJson = zlmdb.MapUuidJson(slot=10, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_uuid_cbor: zlmdb.MapUuidCbor = zlmdb.MapUuidCbor(slot=11, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_uuid_pickle: zlmdb.MapUuidPickle = zlmdb.MapUuidPickle(slot=12)
    tab_str_json: zlmdb.MapStringJson = zlmdb.MapStringJson(slot=20, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_str_cbor: zlmdb.MapStringCbor = zlmdb.MapStringCbor(slot=21, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_str_pickle: zlmdb.MapStringPickle = zlmdb.MapStringPickle(slot=22)
    tab_oid_json: zlmdb.MapOidJson = zlmdb.MapOidJson(slot=30, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_oid_cbor: zlmdb.MapOidCbor = zlmdb.MapOidCbor(slot=31, marshal=(lambda o: o.marshal()), unmarshal=User.parse)
    tab_oid_pickle: zlmdb.MapOidPickle = zlmdb.MapOidPickle(slot=32)


class Schema2(zlmdb.Schema):

    users: zlmdb.MapOidPickle = zlmdb.MapOidPickle(1)


class Schema3(zlmdb.Schema):

    users: zlmdb.MapStringPickle = zlmdb.MapStringPickle(1)


class Schema4(zlmdb.Schema):

    users: zlmdb.MapOidPickle = zlmdb.MapOidPickle(1)
    idx_users_by_authid: zlmdb.MapStringOid = zlmdb.MapStringOid(2)
    idx_users_by_email: zlmdb.MapStringOid = zlmdb.MapStringOid(3)

    def __init__(self):
        super(Schema4, self).__init__()
        self.users.attach_index('idx1', lambda user: user.authid, self.idx_users_by_authid)
        self.users.attach_index('idx2', lambda user: user.email, self.idx_users_by_email)
