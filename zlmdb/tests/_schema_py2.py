###############################################################################
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
        self.realm_oid = None
        self.icecream = None
        self.mrealm = None
        self.mrealm_notnull = None

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
        if other.realm_oid != self.realm_oid:
            return False
        if other.icecream != self.icecream:
            return False
        if other.mrealm != self.mrealm:
            return False
        if other.mrealm_notnull != self.mrealm_notnull:
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
            u'realm_oid': self.realm_oid,
            u'icecream': self.icecream,
            u'mrealm': self.mrealm.hex if self.mrealm else None,
            u'mrealm_notnull': self.mrealm_notnull.hex if self.mrealm_notnull else None,
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
        user.realm_oid = obj.get(u'realm_oid', None)
        user.icecream = obj.get(u'icecream', None)
        if 'mrealm' in obj and obj['mrealm']:
            user.mrealm = uuid.UUID(hex=obj['mrealm'])
        if 'mrealm_notnull' in obj and obj['mrealm_notnull']:
            user.mrealm_notnull = uuid.UUID(hex=obj['mrealm_notnull'])
        return user

    @staticmethod
    def create_test_user(oid=None, realm_oid=None):
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
        if realm_oid is not None:
            user.realm_oid = realm_oid
        else:
            user.realm_oid = random.randint(0, 9007199254740992)
        user.icecream = random.choice([u'vanilla', u'lemon', u'strawberry'])
        user.mrealm = uuid.uuid4()
        user.mrealm_notnull = uuid.uuid4()
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
        self.users.attach_index('idx1', self.idx_users_by_authid, lambda user: user.authid, nullable=False)

        self.idx_users_by_email = zlmdb.MapStringOid(3)
        self.users.attach_index('idx2', self.idx_users_by_email, lambda user: user.email, nullable=True)

        self.idx_users_by_realm = zlmdb.MapOidOidOid(4)
        self.users.attach_index('idx3', self.idx_users_by_realm, lambda user: (user.realm_oid, user.oid))

        self.idx_users_by_icecream = zlmdb.MapStringOidOid(5)
        self.users.attach_index('idx4',
                                self.idx_users_by_icecream,
                                lambda user: (user.icecream, user.oid),
                                nullable=False)

        self.idx_users_by_mrealm_authid = zlmdb.MapUuidStringOid(6)
        self.users.attach_index('idx5',
                                self.idx_users_by_mrealm_authid,
                                lambda user: (user.mrealm, user.authid),
                                nullable=True)

        self.idx_users_by_mrealm_notnull_authid = zlmdb.MapUuidStringOid(7)
        self.users.attach_index('idx6',
                                self.idx_users_by_mrealm_notnull_authid,
                                lambda user: (user.mrealm_notnull, user.authid),
                                nullable=False)
