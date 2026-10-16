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
Run the ORM test suite against one LMDB format (#171).

``ZLMDB_TEST_LIB_VERSION`` (``"0.9"`` or ``"1.0"``) sets the format that
``zlmdb.Database`` gives new databases for this test run. It is a test-only
switch, not a zlmdb configuration knob: ``just test-orm`` runs the suite once
per format. Unset, the real default applies.
"""

import os

import pytest

import zlmdb._database

TEST_LIB_VERSION = os.environ.get("ZLMDB_TEST_LIB_VERSION") or None


def pytest_configure(config):
    if TEST_LIB_VERSION is not None:
        if TEST_LIB_VERSION not in zlmdb._database._LIB_VERSION_TO_MAJOR:
            raise pytest.UsageError(
                "ZLMDB_TEST_LIB_VERSION={!r}: must be 0.9 or 1.0".format(
                    TEST_LIB_VERSION
                )
            )
        # set before any test module (and its module-scoped fixtures) creates a database
        zlmdb._database.DEFAULT_LIB_VERSION = TEST_LIB_VERSION


def pytest_report_header(config):
    return "zlmdb: new databases in LMDB format {}{}".format(
        zlmdb._database.DEFAULT_LIB_VERSION,
        " (ZLMDB_TEST_LIB_VERSION)" if TEST_LIB_VERSION else " (default)",
    )
