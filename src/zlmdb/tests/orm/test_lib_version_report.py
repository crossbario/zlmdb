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
Reporting the LMDB format of a database (#171).

- ``Database.stats()`` has ``"lib_version"`` (the format, as ``db.lib_version``)
  and ``"lmdb_version"`` (the LMDB library servicing it, e.g. ``"1.0.2"``).
- ``zlmdb info DBPATH [--lib-version 1.0|0.9]`` opens the database read-only and
  prints its format and LMDB version. Exit code 0 if fine, 1 on a format
  mismatch or when there is no database (nothing is created), 2 on a usage error.
"""

import os
from tempfile import TemporaryDirectory

import pytest
import txaio

txaio.use_twisted()

from click.testing import CliRunner  # noqa: E402

import zlmdb  # noqa: E402
from zlmdb import lmdb  # noqa: E402
from zlmdb.cli import main  # noqa: E402

FORMATS = [(0, "0.9"), (1, "1.0")]


def _create_lowlevel(dbpath: str, major: int) -> None:
    env = lmdb.open(dbpath, lib_version=major)
    with env.begin(write=True) as txn:
        txn.put(b"key", b"value")
    env.close()


@pytest.mark.parametrize("major, lib_version", FORMATS)
def test_stats_reports_format(major, lib_version):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        with zlmdb.Database(dbpath) as db:
            stats = db.stats()
            assert stats["lib_version"] == lib_version
            assert stats["lmdb_version"].startswith(lib_version + ".")
            assert stats["lmdb_version"] == "{}.{}.{}".format(*db._env.lib_version())


@pytest.mark.parametrize("major, lib_version", FORMATS)
def test_cli_info(major, lib_version):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        result = CliRunner().invoke(main, ["info", dbpath])
        assert result.exit_code == 0, result.output
        assert "lib_version: {}".format(lib_version) in result.output
        assert "lmdb_version: {}.".format(lib_version) in result.output


@pytest.mark.parametrize("major, lib_version", FORMATS)
def test_cli_info_matching_lib_version(major, lib_version):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        result = CliRunner().invoke(
            main, ["info", dbpath, "--lib-version", lib_version]
        )
        assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "major, existing, requested", [(0, "0.9", "1.0"), (1, "1.0", "0.9")]
)
def test_cli_info_mismatch_exits_1(major, existing, requested):
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, major)
        result = CliRunner().invoke(main, ["info", dbpath, "--lib-version", requested])
        assert result.exit_code == 1, result.output
        assert existing in result.output
        assert requested in result.output


def test_cli_info_no_database_exits_1():
    with TemporaryDirectory() as tmp:
        dbpath = os.path.join(tmp, "nope")
        result = CliRunner().invoke(main, ["info", dbpath])
        assert result.exit_code == 1, result.output
        assert not os.path.exists(dbpath)


def test_cli_info_invalid_lib_version_exits_2():
    with TemporaryDirectory() as dbpath:
        _create_lowlevel(dbpath, 1)
        result = CliRunner().invoke(main, ["info", dbpath, "--lib-version", "2.0"])
        assert result.exit_code == 2, result.output
        # rejected as an invalid choice of --lib-version, not as an unknown argument
        assert "Invalid value for '--lib-version'" in result.output
