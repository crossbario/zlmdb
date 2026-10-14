###############################################################################
#
#  Copyright (C) typedef int GmbH
#  SPDX-License-Identifier: MIT
#
###############################################################################
"""
zlmdb bundles both LMDB release lines, and mixes them safely (#170).

LMDB 0.9.x writes data format v1, LMDB 1.0.x writes data format v3, and neither reads the
other's. Each environment is bound to one engine: an existing file opens with the engine
matching its format and is never converted; a new file uses the default engine (LMDB 0.9,
or the one LMDB_DEFAULT_LIB_VERSION names) or an explicit ``lib_version=``.

py-lmdb's own ``engine_test.py`` skips these checks on a build with a single engine. zlmdb
always bundles both, so here a missing engine is a failure, not a skip. Every test creates
its environments with an explicit ``lib_version=``, so it means the same in both passes of
``just test-lmdb`` (LMDB_DEFAULT_LIB_VERSION=0 and =1).
"""

import os
import struct
import subprocess
import sys

import pytest

import zlmdb.lmdb as lmdb

MDB_MAGIC = 0xBEEFC0DE
FORMAT = {0: 1, 1: 3}  # engine (LMDB major version) -> data format it writes


def data_format(path, subdir=True):
    """The data format of an environment's file, read from disk (0: none / unknown)."""
    data = os.path.join(path, "data.mdb") if subdir else path
    with open(data, "rb") as f:
        head = f.read(64)
    for off in range(0, len(head) - 7, 4):
        if struct.unpack_from("=I", head, off)[0] == MDB_MAGIC:
            return struct.unpack_from("=I", head, off + 4)[0]
    return 0


def create(path, engine, items=100, **kwargs):
    """Create an environment with ``engine`` and write ``items`` records."""
    env = lmdb.open(str(path), lib_version=engine, map_size=16 * 1024 * 1024, **kwargs)
    with env.begin(write=True) as txn:
        for i in range(items):
            txn.put(b"k%05d" % i, b"v%05d-%d" % (i, engine))
    return env


def records(env):
    with env.begin() as txn:
        return list(txn.cursor())


def test_both_engines_bundled():
    assert lmdb.version(lib_version=0)[0] == 0
    assert lmdb.version(lib_version=1)[0] == 1


@pytest.mark.parametrize("engine", [0, 1])
def test_new_file_has_the_engines_format(tmp_path, engine):
    env = create(tmp_path, engine)
    assert env.lib_version()[0] == engine
    env.close()
    assert data_format(str(tmp_path)) == FORMAT[engine]


def test_both_formats_side_by_side(tmp_path):
    env0 = create(tmp_path / "v1", 0)
    env1 = create(tmp_path / "v3", 1)
    assert env0.lib_version()[0] == 0
    assert env1.lib_version()[0] == 1
    for env, engine in ((env0, 0), (env1, 1)):
        with env.begin(write=True) as txn:
            txn.put(b"extra", b"%d" % engine)
    for env, engine in ((env0, 0), (env1, 1)):
        with env.begin() as txn:
            assert txn.get(b"k00042") == b"v00042-%d" % engine
            assert txn.get(b"extra") == b"%d" % engine
    env0.close()
    env1.close()


@pytest.mark.parametrize("engine", [0, 1])
def test_existing_file_keeps_its_format(tmp_path, engine):
    """Reopened without lib_version=, under either default, written to, resized and
    reopened again: the file stays in the format it was created in."""
    create(tmp_path, engine).close()
    for _ in range(2):
        env = lmdb.open(str(tmp_path), map_size=16 * 1024 * 1024)
        assert env.lib_version()[0] == engine
        with env.begin(write=True) as txn:
            for i in range(1000):
                txn.put(b"more%05d" % i, b"x" * 100)
        env.set_mapsize(32 * 1024 * 1024)
        with env.begin(write=True) as txn:
            txn.put(b"after-resize", b"1")
        env.close()
        assert data_format(str(tmp_path)) == FORMAT[engine]


@pytest.mark.parametrize("engine", [0, 1])
def test_readonly_open(tmp_path, engine):
    create(tmp_path, engine).close()
    env = lmdb.open(str(tmp_path), readonly=True)
    assert env.lib_version()[0] == engine
    assert len(records(env)) == 100
    env.close()


@pytest.mark.parametrize("engine", [0, 1])
def test_subdir_false(tmp_path, engine):
    path = tmp_path / "db.mdb"
    create(path, engine, subdir=False).close()
    assert data_format(str(path), subdir=False) == FORMAT[engine]
    env = lmdb.open(str(path), subdir=False)
    assert env.lib_version()[0] == engine
    env.close()


@pytest.mark.parametrize("engine", [0, 1])
@pytest.mark.parametrize("compact", [False, True])
def test_copy_keeps_the_format(tmp_path, engine, compact):
    env = create(tmp_path / "src", engine)
    (tmp_path / "dst").mkdir()
    env.copy(str(tmp_path / "dst"), compact=compact)
    expected = records(env)
    env.close()
    assert data_format(str(tmp_path / "dst")) == FORMAT[engine]
    copy = lmdb.open(str(tmp_path / "dst"))
    assert copy.lib_version()[0] == engine
    assert records(copy) == expected
    copy.close()


@pytest.mark.parametrize("engine", [0, 1])
def test_another_process_chooses_the_same_engine(tmp_path, engine):
    create(tmp_path, engine).close()
    for default in ("0", "1"):
        out = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, zlmdb.lmdb as lmdb; "
                "env = lmdb.open(sys.argv[1], readonly=True); "
                "print(env.lib_version()[0])",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=dict(os.environ, LMDB_DEFAULT_LIB_VERSION=default),
        )
        assert out.stdout.strip() == str(engine)


@pytest.mark.parametrize("engine", [0, 1])
def test_explicit_mismatch_is_an_error(tmp_path, engine):
    create(tmp_path, engine).close()
    with pytest.raises((lmdb.VersionMismatchError, lmdb.InvalidError)):
        lmdb.open(str(tmp_path), lib_version=1 - engine)
    # the failed open changed nothing
    assert data_format(str(tmp_path)) == FORMAT[engine]
    env = lmdb.open(str(tmp_path))
    assert len(records(env)) == 100
    env.close()


def test_data_format_v2_is_rejected(tmp_path):
    """Format v2 is a pre-1.0 LMDB development version (e.g. lmdb-js): no released LMDB
    reads it, and the error says so."""
    create(tmp_path, 0).close()
    data = os.path.join(str(tmp_path), "data.mdb")
    with open(data, "r+b") as f:
        head = f.read(64)
        for off in range(0, len(head) - 7, 4):
            if struct.unpack_from("=I", head, off)[0] == MDB_MAGIC:
                f.seek(off + 4)
                f.write(struct.pack("=I", 2))
                break
    with pytest.raises(lmdb.Error, match="format v2"):
        lmdb.open(str(tmp_path))


@pytest.mark.parametrize("src", [0, 1])
def test_conversion_by_copying(tmp_path, src):
    """The supported migration between formats: copy the data into a new environment of
    the other engine, and back. Nothing is lost."""
    dst = 1 - src
    a = create(tmp_path / "a", src)
    expected = records(a)
    b = lmdb.open(str(tmp_path / "b"), lib_version=dst, map_size=16 * 1024 * 1024)
    with b.begin(write=True) as txn:
        for key, value in expected:
            txn.put(key, value)
    assert records(b) == expected
    c = lmdb.open(str(tmp_path / "c"), lib_version=src, map_size=16 * 1024 * 1024)
    with c.begin(write=True) as txn:
        for key, value in records(b):
            txn.put(key, value)
    assert records(c) == expected
    for env in (a, b, c):
        env.close()
    assert data_format(str(tmp_path / "b")) == FORMAT[dst]
    assert data_format(str(tmp_path / "c")) == FORMAT[src]


@pytest.mark.parametrize("old", [0, 1])
@pytest.mark.parametrize("new", [0, 1])
def test_leftover_lock_file_without_data(tmp_path, old, new):
    """A lock file left over from either engine, with no data file, does not get in the
    way: nobody else has it open, so a new environment of the requested engine is
    created, and the lock file is reinitialized for it."""
    create(tmp_path, old).close()
    os.unlink(os.path.join(str(tmp_path), "data.mdb"))
    env = lmdb.open(str(tmp_path), lib_version=new, map_size=16 * 1024 * 1024)
    assert env.lib_version()[0] == new
    with env.begin(write=True) as txn:
        txn.put(b"a", b"1")
    env.close()
    assert data_format(str(tmp_path)) == FORMAT[new]
