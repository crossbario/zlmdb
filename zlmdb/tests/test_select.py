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

import os
import uuid
import random
import struct

import flatbuffers
import numpy as np
import pytest

import zlmdb  # noqa

from _schema_mnode_log import Schema, MNodeLog

import txaio

txaio.use_twisted()

from txaio import time_ns  # noqa

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory  # type:ignore

if "COVERAGE_PROCESS_START" in os.environ:
    COVERAGE = True
else:
    COVERAGE = False


@pytest.fixture(scope="function")
def builder():
    _builder = flatbuffers.Builder(0)
    return _builder


def rfloat():
    return struct.unpack(">f", struct.pack(">f", random.random() * 10**10))[0]


def fill_mnodelog(obj):
    obj.timestamp = np.datetime64(time_ns(), "ns") + np.timedelta64(
        random.randint(1, 120), "s"
    )
    obj.node_id = uuid.uuid4()
    obj.run_id = uuid.uuid4()
    obj.state = random.randint(1, 2)
    obj.ended = obj.timestamp + np.timedelta64(random.randint(1, 120), "s")
    obj.session = random.randint(1, 9007199254740992)
    obj.sent = obj.timestamp
    obj.seq = random.randint(1, 10000)

    obj.routers = random.randint(1, 32)
    obj.containers = random.randint(1, 32)
    obj.guests = random.randint(1, 32)
    obj.proxies = random.randint(1, 32)
    obj.marketmakers = random.randint(1, 32)

    obj.cpu_ctx_switches = random.randint(1, 1000000)

    # we can't just use random() here, since it won't work for roundtrip
    # data checking (eg 33.42830630594208 != 33.428306579589844)
    # obj.cpu_freq = random.random() * 100.
    obj.cpu_freq = rfloat()

    obj.cpu_guest = rfloat()
    obj.cpu_guest_nice = rfloat()
    obj.cpu_idle = rfloat()
    obj.cpu_interrupts = random.randint(1, 100000)
    obj.cpu_iotwait = rfloat()
    obj.cpu_irq = rfloat()
    obj.cpu_nice = rfloat()
    obj.cpu_soft_interrupts = random.randint(1, 100000)
    obj.cpu_softirq = rfloat()
    obj.cpu_steal = rfloat()
    obj.cpu_system = rfloat()
    obj.cpu_user = rfloat()

    obj.network_bytes_recv = random.randint(1, 2**32)
    obj.network_bytes_sent = random.randint(1, 2**32)
    obj.network_connection_af_inet = random.randint(1, 1000)
    obj.network_connection_af_inet6 = random.randint(1, 1000)
    obj.network_connection_af_unix = random.randint(1, 1000)
    obj.network_dropin = random.randint(1, 10000)
    obj.network_dropout = random.randint(1, 10000)
    obj.network_errin = random.randint(1, 10000)
    obj.network_errout = random.randint(1, 10000)
    obj.network_packets_recv = random.randint(1, 2**32)
    obj.network_packets_sent = random.randint(1, 2**32)

    M = 32 * 2**30
    obj.memory_active = random.randint(1, M)
    obj.memory_available = random.randint(1, M)
    obj.memory_buffers = random.randint(1, M)
    obj.memory_cached = random.randint(1, M)
    obj.memory_free = random.randint(1, M)
    obj.memory_inactive = random.randint(1, M)
    obj.memory_percent = rfloat()
    obj.memory_shared = random.randint(1, M)
    obj.memory_slab = random.randint(1, M)
    obj.memory_total = random.randint(1, M)
    obj.memory_used = random.randint(1, M)

    M = 10 * 10
    obj.disk_busy_time = random.randint(1, M)
    obj.disk_read_bytes = random.randint(1, M)
    obj.disk_read_count = random.randint(1, M)
    obj.disk_read_merged_count = random.randint(1, M)
    obj.disk_read_time = random.randint(1, M)
    obj.disk_write_bytes = random.randint(1, M)
    obj.disk_write_count = random.randint(1, M)
    obj.disk_write_merged_count = random.randint(1, M)
    obj.disk_write_time = random.randint(1, M)


@pytest.fixture(scope="function")
def mnodelog():
    _mnodelog = MNodeLog()
    fill_mnodelog(_mnodelog)
    return _mnodelog


def test_mnodelog_roundtrip(mnodelog, builder):
    # serialize to bytes (flatbuffers) from python object
    obj = mnodelog.build(builder)
    builder.Finish(obj)
    data = builder.Output()
    assert len(data) == 544

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

    assert mnodelog.cpu_ctx_switches == _mnodelog.cpu_ctx_switches
    assert mnodelog.cpu_freq == _mnodelog.cpu_freq
    assert mnodelog.cpu_guest == _mnodelog.cpu_guest
    assert mnodelog.cpu_guest_nice == _mnodelog.cpu_guest_nice
    assert mnodelog.cpu_idle == _mnodelog.cpu_idle
    assert mnodelog.cpu_interrupts == _mnodelog.cpu_interrupts
    assert mnodelog.cpu_iotwait == _mnodelog.cpu_iotwait
    assert mnodelog.cpu_irq == _mnodelog.cpu_irq
    assert mnodelog.cpu_nice == _mnodelog.cpu_nice
    assert mnodelog.cpu_soft_interrupts == _mnodelog.cpu_soft_interrupts
    assert mnodelog.cpu_softirq == _mnodelog.cpu_softirq
    assert mnodelog.cpu_steal == _mnodelog.cpu_steal
    assert mnodelog.cpu_system == _mnodelog.cpu_system
    assert mnodelog.cpu_user == _mnodelog.cpu_user

    assert mnodelog.network_bytes_recv == _mnodelog.network_bytes_recv
    assert mnodelog.network_bytes_sent == _mnodelog.network_bytes_sent
    assert mnodelog.network_connection_af_inet == _mnodelog.network_connection_af_inet
    assert mnodelog.network_connection_af_inet6 == _mnodelog.network_connection_af_inet6
    assert mnodelog.network_connection_af_unix == _mnodelog.network_connection_af_unix
    assert mnodelog.network_dropin == _mnodelog.network_dropin
    assert mnodelog.network_dropout == _mnodelog.network_dropout
    assert mnodelog.network_errin == _mnodelog.network_errin
    assert mnodelog.network_errout == _mnodelog.network_errout
    assert mnodelog.network_packets_recv == _mnodelog.network_packets_recv
    assert mnodelog.network_packets_sent == _mnodelog.network_packets_sent

    assert mnodelog.memory_active == _mnodelog.memory_active
    assert mnodelog.memory_available == _mnodelog.memory_available
    assert mnodelog.memory_buffers == _mnodelog.memory_buffers
    assert mnodelog.memory_cached == _mnodelog.memory_cached
    assert mnodelog.memory_free == _mnodelog.memory_free
    assert mnodelog.memory_inactive == _mnodelog.memory_inactive
    assert mnodelog.memory_percent == _mnodelog.memory_percent
    assert mnodelog.memory_shared == _mnodelog.memory_shared
    assert mnodelog.memory_slab == _mnodelog.memory_slab
    assert mnodelog.memory_total == _mnodelog.memory_total
    assert mnodelog.memory_used == _mnodelog.memory_used

    assert mnodelog.disk_busy_time == _mnodelog.disk_busy_time
    assert mnodelog.disk_read_bytes == _mnodelog.disk_read_bytes
    assert mnodelog.disk_read_count == _mnodelog.disk_read_count
    assert mnodelog.disk_read_merged_count == _mnodelog.disk_read_merged_count
    assert mnodelog.disk_read_time == _mnodelog.disk_read_time
    assert mnodelog.disk_write_bytes == _mnodelog.disk_write_bytes
    assert mnodelog.disk_write_count == _mnodelog.disk_write_count
    assert mnodelog.disk_write_merged_count == _mnodelog.disk_write_merged_count
    assert mnodelog.disk_write_time == _mnodelog.disk_write_time


def test_mnodelog_insert(N=1000):
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath) as db:
            schema = Schema.attach(db)

            data = {}

            # insert test data
            #
            with db.begin(write=True) as txn:
                for i in range(N):
                    rec = MNodeLog()
                    fill_mnodelog(rec)
                    key = (rec.timestamp, rec.node_id)
                    schema.mnode_logs[txn, key] = rec

                    data[key] = rec

            # do test scans over inserted data
            #
            with db.begin() as txn:
                cnt = schema.mnode_logs.count(txn)
                assert cnt == N

                # do a simple full scan and compare to original data
                #
                for mnodelog in schema.mnode_logs.select(txn, return_keys=False):
                    key = (mnodelog.timestamp, mnodelog.node_id)

                    _mnodelog = data.get(key, None)

                    # check that we have the record in the original data
                    assert _mnodelog

                    # check that the record data is equal to the original data
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

                    assert mnodelog.cpu_ctx_switches == _mnodelog.cpu_ctx_switches
                    assert mnodelog.cpu_freq == _mnodelog.cpu_freq
                    assert mnodelog.cpu_guest == _mnodelog.cpu_guest
                    assert mnodelog.cpu_guest_nice == _mnodelog.cpu_guest_nice
                    assert mnodelog.cpu_idle == _mnodelog.cpu_idle
                    assert mnodelog.cpu_interrupts == _mnodelog.cpu_interrupts
                    assert mnodelog.cpu_iotwait == _mnodelog.cpu_iotwait
                    assert mnodelog.cpu_irq == _mnodelog.cpu_irq
                    assert mnodelog.cpu_nice == _mnodelog.cpu_nice
                    assert mnodelog.cpu_soft_interrupts == _mnodelog.cpu_soft_interrupts
                    assert mnodelog.cpu_softirq == _mnodelog.cpu_softirq
                    assert mnodelog.cpu_steal == _mnodelog.cpu_steal
                    assert mnodelog.cpu_system == _mnodelog.cpu_system
                    assert mnodelog.cpu_user == _mnodelog.cpu_user

                    assert mnodelog.network_bytes_recv == _mnodelog.network_bytes_recv
                    assert mnodelog.network_bytes_sent == _mnodelog.network_bytes_sent
                    assert (
                        mnodelog.network_connection_af_inet
                        == _mnodelog.network_connection_af_inet
                    )
                    assert (
                        mnodelog.network_connection_af_inet6
                        == _mnodelog.network_connection_af_inet6
                    )
                    assert (
                        mnodelog.network_connection_af_unix
                        == _mnodelog.network_connection_af_unix
                    )
                    assert mnodelog.network_dropin == _mnodelog.network_dropin
                    assert mnodelog.network_dropout == _mnodelog.network_dropout
                    assert mnodelog.network_errin == _mnodelog.network_errin
                    assert mnodelog.network_errout == _mnodelog.network_errout
                    assert (
                        mnodelog.network_packets_recv == _mnodelog.network_packets_recv
                    )
                    assert (
                        mnodelog.network_packets_sent == _mnodelog.network_packets_sent
                    )

                    assert mnodelog.memory_active == _mnodelog.memory_active
                    assert mnodelog.memory_available == _mnodelog.memory_available
                    assert mnodelog.memory_buffers == _mnodelog.memory_buffers
                    assert mnodelog.memory_cached == _mnodelog.memory_cached
                    assert mnodelog.memory_free == _mnodelog.memory_free
                    assert mnodelog.memory_inactive == _mnodelog.memory_inactive
                    assert mnodelog.memory_percent == _mnodelog.memory_percent
                    assert mnodelog.memory_shared == _mnodelog.memory_shared
                    assert mnodelog.memory_slab == _mnodelog.memory_slab
                    assert mnodelog.memory_total == _mnodelog.memory_total
                    assert mnodelog.memory_used == _mnodelog.memory_used

                    assert mnodelog.disk_busy_time == _mnodelog.disk_busy_time
                    assert mnodelog.disk_read_bytes == _mnodelog.disk_read_bytes
                    assert mnodelog.disk_read_count == _mnodelog.disk_read_count
                    assert (
                        mnodelog.disk_read_merged_count
                        == _mnodelog.disk_read_merged_count
                    )
                    assert mnodelog.disk_read_time == _mnodelog.disk_read_time
                    assert mnodelog.disk_write_bytes == _mnodelog.disk_write_bytes
                    assert mnodelog.disk_write_count == _mnodelog.disk_write_count
                    assert (
                        mnodelog.disk_write_merged_count
                        == _mnodelog.disk_write_merged_count
                    )
                    assert mnodelog.disk_write_time == _mnodelog.disk_write_time


def test_mnodelog_queries(N=1000):
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath) as db:
            schema = Schema.attach(db)

            data = {}

            # insert test data
            #
            with db.begin(write=True) as txn:
                for i in range(N):
                    rec = MNodeLog()
                    fill_mnodelog(rec)
                    key = (rec.timestamp, rec.node_id)
                    schema.mnode_logs[txn, key] = rec

                    data[key] = rec

            # do test scans over inserted data
            #
            with db.begin() as txn:
                # do some record counting queries
                #
                skeys = sorted(data.keys())
                for key in skeys:
                    mnodelog = schema.mnode_logs[txn, key]
                    assert mnodelog

                first_key = (np.datetime64(0, "ns"), uuid.UUID(bytes=b"\0" * 16))
                last_key = (
                    np.datetime64(2**63 - 1, "ns"),
                    uuid.UUID(bytes=b"\xff" * 16),
                )
                cnt = schema.mnode_logs.count_range(
                    txn, from_key=first_key, to_key=last_key
                )
                assert cnt == N

                cnt = schema.mnode_logs.count_range(
                    txn, from_key=skeys[0], to_key=skeys[-1]
                )
                assert cnt == N - 1

                from_key = skeys[0]
                to_key = (skeys[-1][0], uuid.UUID(bytes=b"\xff" * 16))
                cnt = schema.mnode_logs.count_range(
                    txn, from_key=from_key, to_key=to_key
                )
                assert cnt == N

                K = len(skeys) // 2
                cnt = schema.mnode_logs.count_range(
                    txn, from_key=skeys[0], to_key=skeys[K]
                )
                assert cnt == N - K

                K = 10
                from_key = skeys[-K]
                to_key = (skeys[-1][0], uuid.UUID(bytes=b"\xff" * 16))
                cnt = schema.mnode_logs.count_range(
                    txn, from_key=from_key, to_key=to_key
                )
                assert cnt == K

                # do some scanning queries
                #

                # full scan
                keys1 = []
                for key in schema.mnode_logs.select(
                    txn, return_values=False, reverse=False
                ):
                    keys1.append(key)

                assert len(keys1) == N

                # full reverse scan
                keys2 = []
                for key in schema.mnode_logs.select(
                    txn, return_values=False, reverse=True
                ):
                    keys2.append(key)

                assert len(keys2) == N
                assert keys1 == list(reversed(keys2))

                # scan [from_key, to_key[
                keys1 = []
                for key in schema.mnode_logs.select(
                    txn,
                    return_values=False,
                    from_key=from_key,
                    to_key=to_key,
                    reverse=False,
                ):
                    keys1.append(key)

                assert len(keys1) == K

                # reverse scan [from_key, to_key[
                keys2 = []
                for key in schema.mnode_logs.select(
                    txn,
                    return_values=False,
                    from_key=from_key,
                    to_key=to_key,
                    reverse=True,
                ):
                    keys2.append(key)

                assert len(keys2) == K
                assert keys1 == list(reversed(keys2))

                K = len(skeys) // 2
                anchor_key = skeys[K]

                # scan [from_key, ..
                keys1 = []
                for key in schema.mnode_logs.select(
                    txn, return_values=False, from_key=anchor_key, reverse=False
                ):
                    keys1.append(key)

                assert len(keys1) == K
                assert skeys[K:] == keys1

                # reverse scan ..., to_key[
                keys2 = []
                for key in schema.mnode_logs.select(
                    txn, return_values=False, to_key=anchor_key, reverse=True
                ):
                    keys2.append(key)

                assert len(keys2) == K
                assert skeys[:K] == list(reversed(keys2))

                # scan a range with 2 boundaries
                #
                K = 10
                from_key = skeys[K]
                to_key = skeys[-K]

                _skeys = skeys[K:-K]
                L = len(_skeys)

                cnt = schema.mnode_logs.count_range(
                    txn, from_key=from_key, to_key=to_key
                )
                assert cnt == L

                # scan [from_key, to_key[
                keys1 = []
                for key in schema.mnode_logs.select(
                    txn,
                    return_values=False,
                    from_key=from_key,
                    to_key=to_key,
                    reverse=False,
                ):
                    keys1.append(key)

                assert len(keys1) == L
                assert _skeys == keys1

                # reverse scan [from_key, to_key[
                keys2 = []
                for key in schema.mnode_logs.select(
                    txn,
                    return_values=False,
                    from_key=from_key,
                    to_key=to_key,
                    reverse=True,
                ):
                    keys2.append(key)

                assert len(keys2) == L
                assert _skeys == list(reversed(keys2))


def _test_mnodelog_bigtable(N, M, K):
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath, maxsize=(5 * 2**30)) as db:
            schema = Schema.attach(db)

            data = {}
            print()

            # fill table
            #
            started = time_ns()
            with db.begin(write=True) as txn:
                for i in range(N):
                    rec = MNodeLog()
                    fill_mnodelog(rec)
                    key = (rec.timestamp, rec.node_id)
                    schema.mnode_logs[txn, key] = rec
                    data[key] = rec
            duration = (time_ns() - started) / 1000000000.0
            rps = int(round(N / duration))
            duration = int(round(duration))
            print(
                "Inserted {} records in {} seconds [{} records/sec]".format(
                    N, duration, rps
                )
            )

            skeys = sorted(data.keys())

            # random single record selects
            #
            if True:
                started = time_ns()
                with db.begin() as txn:
                    for i in range(M):
                        key = random.choice(skeys)
                        mnodelog = schema.mnode_logs[txn, key]
                        assert mnodelog
                duration = (time_ns() - started) / 1000000000.0
                rps = int(round(M / duration))
                duration = int(round(duration))
                print(
                    "Selected {} records in {} seconds [{} records/sec]".format(
                        M, duration, rps
                    )
                )

            # random range counts
            #
            if True:
                started = time_ns()
                with db.begin() as txn:
                    for i in range(K):
                        # we select a fixed range of (max) 1000 elements:
                        i1 = random.randint(0, len(skeys) - 1)
                        i2 = random.randint(i1, min(len(skeys) - 1, i1 + 1000))
                        key1 = skeys[i1]
                        key2 = skeys[i2]
                        cnt = schema.mnode_logs.count_range(
                            txn, from_key=key1, to_key=key2
                        )
                        assert cnt == len(skeys[i1:i2])
                duration = (time_ns() - started) / 1000000000.0
                rps = int(round(K / duration))
                duration = int(round(duration))
                print(
                    "Performed {} range counts in {} seconds [{} queries/sec]".format(
                        K, duration, rps
                    )
                )


def test_mnodelog_bigtable_size10k():
    _test_mnodelog_bigtable(N=10000, M=500000, K=10000)


@pytest.mark.skipif(COVERAGE, reason="skipping on coverage")
def test_mnodelog_bigtable_size20k():
    _test_mnodelog_bigtable(N=20000, M=1000000, K=20000)


@pytest.mark.skipif(COVERAGE, reason="skipping on coverage")
def test_mnodelog_bigtable_size40k():
    _test_mnodelog_bigtable(N=40000, M=2000000, K=40000)


@pytest.mark.skipif(COVERAGE, reason="skipping on coverage")
def test_mnodelog_bigtable_size80k():
    _test_mnodelog_bigtable(N=80000, M=4000000, K=80000)


@pytest.mark.skipif(COVERAGE, reason="skipping on coverage")
def test_mnodelog_bigtable_size160k():
    _test_mnodelog_bigtable(N=160000, M=8000000, K=160000)
