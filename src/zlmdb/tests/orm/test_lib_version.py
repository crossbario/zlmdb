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

"""
zlmdb.Database(lib_version=...): choose and report the LMDB format (#171).

- ``lib_version`` names the LMDB format: ``'1.0'`` (LMDB 1.0.x, data format v3)
  or ``'0.9'`` (LMDB 0.9.x, data format v1). ``None`` means "not given".
- A new database gets ``'1.0'`` when ``lib_version`` is not given.
- An existing database opens in its own format when ``lib_version`` is not given.
- An explicit ``lib_version`` that does not match an existing database raises
  ``ValueError``, naming the path and both formats.
- Anything other than ``None``, ``'1.0'`` or ``'0.9'`` raises ``ValueError``.
"""

import os
from tempfile import TemporaryDirectory

import pytest
import txaio

txaio.use_twisted()

import zlmdb  # noqa: E402
from zlmdb import lmdb  # noqa: E402


def _create_lowlevel(dbpath: str, major: int) -> None:
    """Create a database in the given LMDB format with the low-level binding,
    independently of the zlmdb.Database code under test."""
    env = lmdb.open(dbpath, lib_version=major)
    with env.begin(write=True) as txn:
        txn.put(b"key", b"value")
    env.close()


@pytest.mark.skipif(
    os.environ.get("ZLMDB_TEST_LIB_VERSION", "1.0") != "1.0",
    reason="ZLMDB_TEST_LIB_VERSION overrides the default for this test run",
)
def test_new_database_defaults_to_1_0():
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath) as db:
            assert db.lib_version == "1.0"


@pytest.mark.parametrize("lib_version", ["1.0", "0.9"])
def test_new_database_explicit(lib_version):
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath, lib_version=lib_version) as db:
            assert db.lib_version == lib_version
        # reopening without lib_version keeps the format it was created with
        with zlmdb.Database(dbpath) as db:
            assert db.lib_version == lib_version


@pytest.mark.parametrize("major, lib_version", [(0, "0.9"), (1, "1.0")])
def test_existing_database_opens_in_own_format(major, lib_version):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        with zlmdb.Database(dbpath) as db:
            assert db.lib_version == lib_version


@pytest.mark.parametrize("major, existing, requested", [(0, "0.9", "1.0"), (1, "1.0", "0.9")])
def test_existing_database_mismatch_raises(major, existing, requested):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        with pytest.raises(ValueError) as exc_info:
            zlmdb.Database(dbpath, lib_version=requested)
        msg = str(exc_info.value)
        assert dbpath in msg
        assert existing in msg
        assert requested in msg
        # the failed open must not leave the path registered as open
        with zlmdb.Database(dbpath) as db:
            assert db.lib_version == existing


@pytest.mark.parametrize("bad", ["2.0", "1", "0", "", 0, 1, 1.0])
def test_invalid_lib_version_raises(bad):
    with TemporaryDirectory() as dbpath:
        with pytest.raises(ValueError):
            zlmdb.Database(dbpath, lib_version=bad)
        assert not os.path.exists(os.path.join(dbpath, "data.mdb"))
