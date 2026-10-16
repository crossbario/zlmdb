###############################################################################
#
#  Copyright (C) typedef int GmbH
#  SPDX-License-Identifier: MIT
#
###############################################################################
"""
A failed ``lmdb.open()`` raises its error, and nothing else (#197).

``Environment.__init__`` opens the main database in a first read transaction. When
that ``begin()`` fails (here: ``MDB_READERS_FULL``, because another process holds the
only reader slot), the half-built ``Transaction`` must not raise from ``__del__`` when
it is collected. Every test passes an explicit ``lib_version=``, so it means the same
in both passes of ``just test-lmdb``.
"""

import gc
import subprocess
import sys

import pytest

import zlmdb.lmdb as lmdb

HOLDER = (
    "import sys, zlmdb.lmdb as lmdb; "
    "env = lmdb.open(sys.argv[1], lib_version=int(sys.argv[2]), max_readers=1); "
    "txn = env.begin(); "
    "print('ready', flush=True); "
    "sys.stdin.readline()"
)


@pytest.mark.parametrize("engine", [0, 1])
def test_failed_open_raises_only_its_error(tmp_path, monkeypatch, engine):
    unraisable = []
    monkeypatch.setattr(
        sys,
        "unraisablehook",
        lambda args: unraisable.append(
            "{}: {}".format(args.exc_type.__name__, args.exc_value)
        ),
    )

    # another process takes the only reader slot, and keeps it until told to exit
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(tmp_path), str(engine)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "ready"

        with pytest.raises(lmdb.ReadersFullError):
            lmdb.open(str(tmp_path), lib_version=engine, max_readers=1)

        # collect the half-built objects of the failed open (PyPy needs explicit GC)
        for _ in range(3):
            gc.collect()
    finally:
        holder.stdin.close()
        holder.wait()

    assert holder.returncode == 0
    assert unraisable == []
