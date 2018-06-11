import os
import shutil
import lmdb
import pytest

DBNAME = '.test-db1'


@pytest.fixture(scope='module')
def lmdb_env():
    if os.path.exists(DBNAME):
        if os.path.isdir(DBNAME):
            shutil.rmtree(DBNAME)
        else:
            os.remove(DBNAME)
    env = lmdb.open(DBNAME)
    return env


def test_create_env(lmdb_env):
    assert isinstance(lmdb_env, lmdb.Environment)
