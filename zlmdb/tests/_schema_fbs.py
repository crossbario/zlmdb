import random
import uuid
import datetime

from zlmdb.flatbuffer.demo import User as _user
from zlmdb.flatbuffer.demo import Date as _date


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

    def build(self, builder):
        name = builder.CreateString(self.name)
        authid = builder.CreateString(self.authid)
        email = builder.CreateString(self.email)

        _user.UserStart(builder)
        _user.UserAddName(builder, name)
        _user.UserAddAuthid(builder, authid)
        _user.UserAddEmail(builder, email)
        if self.birthday:
            _user.UserAddBirthday(builder,
                                  _date.CreateDate(builder,
                                                   self.birthday.year,
                                                   self.birthday.month,
                                                   self.birthday.day))
        _user.UserAddIsFriendly(builder, self.is_friendly)

        return _user.UserEnd(builder)

    @staticmethod
    def root(buf):
        return _user.User.GetRootAsUser(buf, 0)

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
        return user
