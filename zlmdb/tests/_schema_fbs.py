###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
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

from __future__ import absolute_import

import random
import uuid
import datetime

from zlmdb.flatbuffers.demo import User as _user
from zlmdb.flatbuffers.demo import Date as _date


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

        _user.UserStart(builder)
        _user.UserAddName(builder, name)
        _user.UserAddAuthid(builder, authid)
        _user.UserAddEmail(builder, email)

        if self._birthday is not None:
            _user.UserAddBirthday(
                builder, _date.CreateDate(builder, self._birthday.year, self._birthday.month, self._birthday.day))
        else:
            bd = self._from_fbs.Birthday()
            _user.UserAddBirthday(builder, _date.CreateDate(builder, bd.Year(), bd.Month(), bd.Day()))

        # FIXME: tags
        # FIXME: ratings
        # FIXME: friends

        if self._is_friendly is not None:
            _user.UserAddIsFriendly(builder, self._is_friendly)
        else:
            _user.UserAddIsFriendly(builder, self._from_fbs.IsFriendly())

        if self._referred_by is not None:
            _user.UserAddReferredBy(builder, self._referred_by)
        else:
            _user.UserAddReferredBy(builder, self._from_fbs.ReferredBy())

        return _user.UserEnd(builder)

    @staticmethod
    def cast(buf):
        return User(_user.User.GetRootAsUser(buf, 0))

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
