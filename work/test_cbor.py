import datetime
import pickle
import json
import cbor2
from typing import Optional, List, Dict

RESULT = {
    'objects': 0,
    'bytes': 0
}


class Tag(object):
    GEEK = 1
    VIP = 2

# requires python 3.6+:
#
# class User(object):
#     oid: int
#     name: str
#     authid: str
#     email: str
#     birthday: datetime.date
#     is_friendly: bool
#     tags: Optional[List[str]]
#     ratings: Dict[str, float] = {}
#     friends: List[int] = []
#     referred_by: int = None


class User(object):
    def __init__(self):
        self.oid = None
        self.name = None
        self.authid = None
        self.email = None
        self.birthday = None
        self.is_friendly = None
        self.tags = None
        self.ratings = {}
        self.friends = []
        self.referred_by = None

    def marshal(self):
        obj = {
            'oid': self.oid,
            'name': self.name,
            'authid': self.authid,
            'email': self.email,
            'birthday': self.birthday,
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
        user.email = obj.get('email', None)
        user.birthday = obj.get('birthday', None)
        user.is_friendly = obj.get('is_friendly', None)
        user.tags = obj.get('tags', None)
        user.ratings = obj.get('ratings', {})
        user.friends = obj.get('friends', [])
        user.referred_by = obj.get('referred_by', None)
        return user


def test():
    global RESULT

    user = User()
    user.oid = 23
    user.name = 'Homer Simpson'
    user.authid = 'homer'
    user.email = 'homer.simpson@example.com'
    user.birthday = {
        'year': 1950,
        'month': 12,
        'day': 24
    }
    user.is_friendly = True
    user.tags = [Tag.GEEK, Tag.VIP]

    #data = json.dumps(user.marshal(), ensure_ascii=False)
    data = cbor2.dumps(user.marshal())

    RESULT['objects'] += 1
    RESULT['bytes'] += len(data)


import timeit

N = 1000
M = 100000

for i in range(N):
    secs = timeit.timeit(test, number=M)
    ops = round(float(M) / secs, 1)
    print('{} objects/sec'.format(ops))
    print(RESULT)
