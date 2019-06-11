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

import os
import sys
import uuid
import pytest
from copy import deepcopy

import numpy as np

import txaio
txaio.use_twisted()

import zlmdb  # noqa
from zlmdb import time_ns

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory

from crossbarfx.master.database.mrealmschema import MrealmSchema
from crossbarfx.cfxdb.log import MNodeLog


def test_1():
    with TemporaryDirectory() as dbpath:

        with zlmdb.Database(dbpath) as db:

            schema = MrealmSchema.attach(db)

            with db.begin(write=True) as txn:
                for i in range(1000):
                    rec = MNodeLog()
                    rec.timestamp = np.datetime64(time_ns(), 'ns')
                    rec.node_id = uuid.uuid4()
                    rec.run_id = uuid.uuid4()

                    key = (rec.timestamp, rec.node_id)

                    schema.mnode_logs[txn, key] = rec
                
            with db.begin() as txn:
                cnt = schema.mnode_logs.count(txn)
                print('XXX', cnt)
