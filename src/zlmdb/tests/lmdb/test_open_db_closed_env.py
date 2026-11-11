###############################################################################
#
#  Copyright (C) typedef int GmbH
#  SPDX-License-Identifier: MIT
#
###############################################################################
"""
``open_db()`` on a closed environment raises the binding's ``Error``, as every other
operation on a closed environment does, not an ``AttributeError`` on ``None`` (#211).
"""

import pytest

from zlmdb import _lmdb_vendor as lmdb


def test_open_db_after_close(tmp_path):
    env = lmdb.open(str(tmp_path), max_dbs=2)
    env.open_db(b"before")
    env.close()
    with pytest.raises(lmdb.Error, match="closed/deleted/dropped"):
        env.open_db(b"after")
    # the same error as the other operations on a closed environment
    with pytest.raises(lmdb.Error, match="closed/deleted/dropped"):
        env.stat()
