import random
import uuid
import datetime
import zlmdb


class User(object):
    def __init__(self):
        self.oid = None
        self.name = None
        self.authid = None
        self.uuid = None
        self.email = None
        self.birthday = None
        self.is_friendly = None
        self.tags = None
        self.ratings = {}
        self.friends = []
        self.referred_by = None

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
            u'oid': self.oid,
            u'name': self.name,
            u'authid': self.authid,
            u'uuid': self.uuid.hex if self.uuid else None,
            u'email': self.email,
            u'birthday': {
                u'year': self.birthday.year if self.birthday else None,
                u'month': self.birthday.month if self.birthday else None,
                u'day': self.birthday.day if self.birthday else None,
            },
            u'is_friendly': self.is_friendly,
            u'tags': self.tags,
            u'ratings': self.ratings,
            u'friends': self.friends,
            u'referred_by': self.referred_by,
        }
        return obj

    @staticmethod
    def parse(obj):
        user = User()
        user.oid = obj.get(u'oid', None)
        user.name = obj.get(u'name', None)
        user.authid = obj.get(u'authid', None)
        if u'uuid' in obj:
            user.uuid = uuid.UUID(hex=obj[u'uuid'])
        user.email = obj.get(u'email', None)
        if u'birthday' in obj:
            b = obj[u'birthday']
            user.birthday = datetime.date(b.year, b.month, b.day)
        user.is_friendly = obj.get(u'is_friendly', None)
        user.tags = obj.get(u'tags', None)
        user.ratings = obj.get(u'ratings', {})
        user.friends = obj.get(u'friends', [])
        user.referred_by = obj.get(u'referred_by', None)
        return user

    @staticmethod
    def create_test_user(oid=None):
        user = User()
        if oid is not None:
            user.oid = oid
        else:
            user.oid = random.randint(0, 9007199254740992)
        user.name = u'Test {}'.format(user.oid)
        user.authid = u'test-{}'.format(user.oid)
        user.uuid = uuid.uuid4()
        user.email = u'{}@example.com'.format(user.authid)
        user.birthday = datetime.date(1950, 12, 24)
        user.is_friendly = True
        user.tags = [u'geek', u'sudoko', u'yellow']
        for j in range(10):
            user.ratings[u'test-rating-{}'.format(j)] = random.random()
        user.friends = [random.randint(0, 9007199254740992) for _ in range(10)]
        user.referred_by = random.randint(0, 9007199254740992)
        return user


class Schema1(zlmdb.Schema):
    def __init__(self):
        super(Schema1, self).__init__()

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


class Schema2(zlmdb.Schema):
    def __init__(self):
        super(Schema2, self).__init__()
        self.users = zlmdb.MapOidPickle(1)


class Schema3(zlmdb.Schema):
    def __init__(self):
        super(Schema3, self).__init__()
        self.users = zlmdb.MapStringPickle(1)


class Schema4(zlmdb.Schema):
    def __init__(self):
        super(Schema4, self).__init__()
        self.users = zlmdb.MapOidPickle(1)

        self.idx_users_by_authid = zlmdb.MapStringOid(2)
        self.users.attach_index('idx1', lambda user: user.authid, self.idx_users_by_authid)

        self.idx_users_by_email = zlmdb.MapStringOid(3)
        self.users.attach_index('idx2', lambda user: user.email, self.idx_users_by_email)
