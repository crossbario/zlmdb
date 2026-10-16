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
"""Stress concurrent writers using one zLMDB database.

This test is opt-in because it starts multiple processes and performs thousands
of synchronous transactions.  The dedicated CI job enables it for every push
and pull request.
"""

import multiprocessing
import os
import platform
import queue
import struct
import sys
import time
import traceback

import pytest

import zlmdb
import zlmdb.lmdb as lmdb


RUN_STRESS_TEST = os.environ.get("ZLMDB_RUN_MULTIWRITER_STRESS") == "1"
WRITER_COUNT = int(os.environ.get("ZLMDB_STRESS_WRITERS", "8"))
WRITES_PER_WRITER = int(os.environ.get("ZLMDB_STRESS_WRITES", "250"))
ROUND_COUNT = int(os.environ.get("ZLMDB_STRESS_ROUNDS", "3"))
START_TIMEOUT_SECONDS = 60
ROUND_TIMEOUT_SECONDS = 120
MAP_SIZE = 128 * 1024 * 1024


pytestmark = pytest.mark.skipif(
    not RUN_STRESS_TEST,
    reason="enabled by the dedicated multi-writer stress CI job",
)


def _record(writer_id, sequence):
    key = "writer-{:04d}-record-{:08d}".format(writer_id, sequence).encode()
    value = struct.pack(">II", writer_id, sequence)
    return key, value


def _writer(dbpath, writer_id, start_barrier, result_queue):
    """Open the shared environment and commit this process's records."""
    pid = os.getpid()
    started = time.monotonic()

    try:
        # The parent participates in this barrier. Once released, every child
        # concurrently opens the same environment and begins writing.
        start_barrier.wait()

        with zlmdb.Database(
            dbpath=dbpath,
            maxsize=MAP_SIZE,
            open_now=False,
        ) as db:
            for sequence in range(WRITES_PER_WRITER):
                key, value = _record(writer_id, sequence)
                with db.begin(write=True) as txn:
                    if not txn.put(key, value, overwrite=False):
                        raise AssertionError("record already exists: {!r}".format(key))

        result_queue.put(
            {
                "status": "ok",
                "writer_id": writer_id,
                "pid": pid,
                "elapsed_seconds": time.monotonic() - started,
            }
        )
    except BaseException as exc:
        result_queue.put(
            {
                "status": "error",
                "writer_id": writer_id,
                "pid": pid,
                "exception": "{}.{}".format(
                    type(exc).__module__, type(exc).__qualname__
                ),
                "traceback": traceback.format_exc(),
            }
        )
        raise


def _run_round(dbpath, round_number):
    context = multiprocessing.get_context("spawn")
    start_barrier = context.Barrier(
        WRITER_COUNT + 1,
        timeout=START_TIMEOUT_SECONDS,
    )
    result_queue = context.Queue()
    processes = [
        context.Process(
            target=_writer,
            name="zlmdb-writer-{}-{}".format(round_number, writer_id),
            args=(dbpath, writer_id, start_barrier, result_queue),
        )
        for writer_id in range(WRITER_COUNT)
    ]

    started = time.monotonic()
    orchestration_failure = None
    try:
        for process in processes:
            process.start()

        start_barrier.wait()
        deadline = started + ROUND_TIMEOUT_SECONDS

        for process in processes:
            process.join(max(0, deadline - time.monotonic()))
    except Exception:
        orchestration_failure = traceback.format_exc()
    finally:
        # Never leave stress-test children running after a timeout or a broken
        # startup barrier.
        timed_out = [process for process in processes if process.is_alive()]
        for process in timed_out:
            process.terminate()
        for process in timed_out:
            process.join(5)

    results = []
    while len(results) < WRITER_COUNT:
        try:
            results.append(result_queue.get(timeout=1))
        except queue.Empty:
            break
    result_queue.close()
    result_queue.join_thread()

    failures = [result for result in results if result["status"] != "ok"]
    exit_failures = [
        (process.name, process.pid, process.exitcode)
        for process in processes
        if process.exitcode != 0
    ]

    assert not timed_out, "writer processes timed out: {}".format(
        [(process.name, process.pid) for process in timed_out]
    )
    assert orchestration_failure is None, orchestration_failure
    assert len(results) == WRITER_COUNT, (
        "expected {} worker results, received {}: {!r}".format(
            WRITER_COUNT, len(results), results
        )
    )
    assert not exit_failures, "writer processes failed: {!r}; results: {!r}".format(
        exit_failures, results
    )
    assert not failures, "writers raised exceptions: {!r}".format(failures)

    pids = {result["pid"] for result in results}
    assert len(pids) == WRITER_COUNT, "writers did not have unique PIDs: {!r}".format(
        sorted(pids)
    )

    expected_entries = WRITER_COUNT * WRITES_PER_WRITER
    with zlmdb.Database(
        dbpath=dbpath,
        maxsize=MAP_SIZE,
        create=False,
        open_now=False,
    ) as db:
        with db.begin() as txn:
            for writer_id in range(WRITER_COUNT):
                for sequence in range(WRITES_PER_WRITER):
                    key, expected_value = _record(writer_id, sequence)
                    assert txn.get(key) == expected_value

        assert db.stats()["entries"] == expected_entries

    return {
        "round": round_number,
        "writers": WRITER_COUNT,
        "writes_per_writer": WRITES_PER_WRITER,
        "entries": expected_entries,
        "elapsed_seconds": time.monotonic() - started,
        "pids": sorted(pids),
    }


def test_multi_writers_single_database(tmp_path):
    """Every writer must finish and every unique record must be readable."""
    assert WRITER_COUNT > 2
    assert WRITES_PER_WRITER > 0
    assert ROUND_COUNT > 0

    print(
        "stress environment: zlmdb={}, lmdb={}, python={}, platform={}, "
        "start_method=spawn".format(
            zlmdb.__version__,
            lmdb.version(),
            sys.version.replace("\n", " "),
            platform.platform(),
        )
    )

    for round_number in range(1, ROUND_COUNT + 1):
        dbpath = tmp_path / "round-{}".format(round_number)
        dbpath.mkdir()
        summary = _run_round(str(dbpath), round_number)
        print("stress round passed: {!r}".format(summary))

    total_transactions = WRITER_COUNT * WRITES_PER_WRITER * ROUND_COUNT
    print(
        "stress test passed: rounds={}, writers={}, transactions={}".format(
            ROUND_COUNT,
            WRITER_COUNT,
            total_transactions,
        )
    )
