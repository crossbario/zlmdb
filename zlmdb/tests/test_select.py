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

import uuid
import random

import flatbuffers
import numpy as np
import pytest

import zlmdb  # noqa
from zlmdb import time_ns

from _schema_mnode_log import Schema, MNodeLog

import txaio
txaio.use_twisted()

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory


@pytest.fixture(scope='function')
def builder():
    _builder = flatbuffers.Builder(0)
    return _builder


def fill_mnodelog(obj):

    obj.timestamp = np.datetime64(time_ns(), 'ns')
    obj.node_id = uuid.uuid4()
    obj.run_id = uuid.uuid4()
    obj.state = random.randint(0, 2)
    obj.ended = obj.timestamp + np.timedelta64(random.randint(0, 120), 's')
    obj.session = random.randint(0, 9007199254740992)
    obj.sent = obj.timestamp
    obj.seq = random.randint(0, 10000)

    obj.routers = random.randint(0, 32)
    obj.containers = random.randint(0, 32)
    obj.guests = random.randint(0, 32)
    obj.proxies = random.randint(0, 32)
    obj.marketmakers = random.randint(0, 32)


@pytest.fixture(scope='function')
def mnodelog():
    _mnodelog = MNodeLog()
    fill_mnodelog(_mnodelog)
    return _mnodelog


def test_mnodelog_roundtrip(mnodelog, builder):
    # serialize to bytes (flatbuffers) from python object
    obj = mnodelog.build(builder)
    builder.Finish(obj)
    data = builder.Output()
    assert len(data) in [152, 160]

    # create python object from bytes (flatbuffes)
    _mnodelog = MNodeLog.cast(data)

    assert mnodelog.timestamp == _mnodelog.timestamp
    assert mnodelog.node_id == _mnodelog.node_id
    assert mnodelog.run_id == _mnodelog.run_id
    assert mnodelog.state == _mnodelog.state
    assert mnodelog.ended == _mnodelog.ended
    assert mnodelog.session == _mnodelog.session
    assert mnodelog.sent == _mnodelog.sent
    assert mnodelog.seq == _mnodelog.seq

    assert mnodelog.routers == _mnodelog.routers
    assert mnodelog.containers == _mnodelog.containers
    assert mnodelog.guests == _mnodelog.guests
    assert mnodelog.proxies == _mnodelog.proxies
    assert mnodelog.marketmakers == _mnodelog.marketmakers


def test_mnodelog_insert(N=1000):
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath) as db:
            schema = Schema.attach(db)

            with db.begin(write=True) as txn:
                for i in range(N):
                    rec = MNodeLog()
                    fill_mnodelog(rec)
                    key = (rec.timestamp, rec.node_id)
                    schema.mnode_logs[txn, key] = rec

            with db.begin() as txn:
                cnt = schema.mnode_logs.count(txn)
                assert cnt == N
