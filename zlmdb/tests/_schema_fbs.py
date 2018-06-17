import random
import uuid
import datetime

from zlmdb.flatbuffer import demo


class User(object):
    def __init__(self, from_fbs=None):
        self._from_fbs = from_fbs

        self._name = None
        self._authid = None
        self._uuid = None
        self._email = None
        self._birthday = None
        self._is_friendly = None
        self._tags = None
        self._ratings = None
        self._ratings_cached = None
        self._friends = None
        self._friends_cached = None
        self._referred_by = None

    @property
    def name(self):
        return self._name or self._from_fbs.Name()

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def authid(self):
        return self._authid or self._from_fbs.Authid()

    @authid.setter
    def authid(self, value):
        self._authid = value

    @property
    def uuid(self):
        return self._uuid or self._from_fbs.Uuid()

    @uuid.setter
    def uuid(self, value):
        self._uuid = value

    @property
    def email(self):
        return self._email or self._from_fbs.Email()

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def birthday(self):
        return self._birthday or self._from_fbs.Birthday()

    @birthday.setter
    def birthday(self, value):
        self._birthday = value

    @property
    def is_friendly(self):
        return self._is_friendly or self._from_fbs.IsFriendly()

    @is_friendly.setter
    def is_friendly(self, value):
        self._is_friendly = value

    @property
    def ratings(self):
        if self._ratings is not None:
            return self._ratings
        if self._ratings_cached is None:
            self._ratings_cached = {}
            if self._from_fbs:
                for i in range(self._from_fbs.RatingsLength()):
                    rat = self._from_fbs.Ratings(i)
                    self._ratings_cached[rat.Name()] = rat.Rating()
        return self._ratings_cached

    @ratings.setter
    def ratings(self, value):
        self._ratings = value

    @property
    def friends(self):
        if self._friends is not None:
            return self._friends
        if self._friends_cached is None:
            self._friends_cached = []
            if self._from_fbs:
                for i in range(self._from_fbs.FriendsLength()):
                    friend_oid = self._from_fbs.Friends(i)
                    self._friends_cached.append(friend_oid)
        return self._friends_cached

    @friends.setter
    def friends(self, value):
        self._friends = value

    @property
    def referred_by(self):
        return self._referred_by or self._from_fbs.ReferredBy()

    @referred_by.setter
    def referred_by(self, value):
        self._referred_by = value

    def build(self, builder):
        if self._name is not None:
            name = builder.CreateString(self._name)
        else:
            name = builder.CreateString(self._from_fbs.Name())

        if self._authid is not None:
            authid = builder.CreateString(self._authid)
        else:
            authid = builder.CreateString(self._from_fbs.Authid())

        if self._email is not None:
            email = builder.CreateString(self._email)
        else:
            email = builder.CreateString(self._from_fbs.Email())

        demo.UserStart(builder)
        demo.UserAddName(builder, name)
        demo.UserAddAuthid(builder, authid)
        demo.UserAddEmail(builder, email)

        if self._birthday is not None:
            demo.UserAddBirthday(
                builder, demo.CreateDate(builder, self._birthday.year, self._birthday.month, self._birthday.day))
        else:
            bd = self._from_fbs.Birthday()
            demo.UserAddBirthday(builder, demo.CreateDate(builder, bd.Year(), bd.Month(), bd.Day()))

        # FIXME: tags
        # FIXME: ratings
        # FIXME: friends

        if self._is_friendly is not None:
            demo.UserAddIsFriendly(builder, self._is_friendly)
        else:
            demo.UserAddIsFriendly(builder, self._from_fbs.IsFriendly())

        if self._referred_by is not None:
            demo.UserAddReferredBy(builder, self._referred_by)
        else:
            demo.UserAddReferredBy(builder, self._from_fbs.ReferredBy())

        return demo.UserEnd(builder)

    @staticmethod
    def cast(buf):
        return User(demo.User.GetRootAsUser(buf, 0))

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
