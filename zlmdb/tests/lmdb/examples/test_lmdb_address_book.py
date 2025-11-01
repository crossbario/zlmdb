"""
Test low-level LMDB API (py-lmdb compatibility)

This test is based on the py-lmdb address-book.py example:
https://github.com/jnwatson/py-lmdb/blob/master/examples/address-book.py

It demonstrates that zlmdb provides a fully compatible py-lmdb API
for direct LMDB access.
"""

import tempfile
import shutil
import os

import zlmdb.lmdb as lmdb
import pytest


@pytest.fixture
def tmpdir():
    """Create a temporary directory for test database"""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


def test_address_book_example(tmpdir):
    """
    Test the complete py-lmdb address-book example workflow.

    This verifies:
    - Environment creation with multiple databases
    - Subdatabase creation
    - Write transactions
    - Read transactions
    - Cursor iteration (sorted keys)
    - Update operations
    - Delete operations
    - Drop database operations
    """
    dbpath = os.path.join(tmpdir, 'address-book.lmdb')

    # Open (and create if necessary) our database environment. Must specify
    # max_dbs=... since we're opening subdbs.
    env = lmdb.open(dbpath, max_dbs=10)

    # Now create subdbs for home and business addresses.
    home_db = env.open_db(b'home')
    business_db = env.open_db(b'business')

    # Add some telephone numbers to each DB:
    with env.begin(write=True) as txn:
        txn.put(b'mum', b'012345678', db=home_db)
        txn.put(b'dad', b'011232211', db=home_db)
        txn.put(b'dentist', b'044415121', db=home_db)
        txn.put(b'hospital', b'078126321', db=home_db)

        txn.put(b'vendor', b'0917465628', db=business_db)
        txn.put(b'customer', b'0553211232', db=business_db)
        txn.put(b'coworker', b'0147652935', db=business_db)
        txn.put(b'boss', b'0123151232', db=business_db)
        txn.put(b'manager', b'0644810485', db=business_db)

    # Verify: Iterate each DB to show the keys are sorted
    with env.begin() as txn:
        # Home database - check sorted order
        home_entries = list(txn.cursor(db=home_db))
        assert home_entries == [
            (b'dad', b'011232211'),
            (b'dentist', b'044415121'),
            (b'hospital', b'078126321'),
            (b'mum', b'012345678'),
        ]

        # Business database - check sorted order
        business_entries = list(txn.cursor(db=business_db))
        assert business_entries == [
            (b'boss', b'0123151232'),
            (b'coworker', b'0147652935'),
            (b'customer', b'0553211232'),
            (b'manager', b'0644810485'),
            (b'vendor', b'0917465628'),
        ]

    # Now let's update some phone numbers. We can specify the default subdb when
    # starting the transaction, rather than pass it in every time:
    with env.begin(write=True, db=home_db) as txn:
        # Update dentist number
        txn.put(b'dentist', b'099991231')

        # Delete hospital number
        txn.delete(b'hospital')

        # Verify home DB state
        home_entries = list(txn.cursor())
        assert home_entries == [
            (b'dad', b'011232211'),
            (b'dentist', b'099991231'),  # Updated
            (b'mum', b'012345678'),
        ]
        # Note: hospital should be deleted
        assert b'hospital' not in [key for key, _ in home_entries]

    # Now let's look up a number in the business DB
    with env.begin(db=business_db) as txn:
        boss_number = txn.get(b'boss')
        assert boss_number == b'0123151232'

    # We got fired, time to delete all keys from the business DB.
    with env.begin(write=True) as txn:
        txn.drop(business_db, delete=False)

        # Add number for recruiter to business DB
        txn.put(b'recruiter', b'04123125324', db=business_db)

        # Verify business DB is now only the recruiter
        business_entries = list(txn.cursor(db=business_db))
        assert business_entries == [
            (b'recruiter', b'04123125324'),
        ]

    # Clean up
    env.close()


def test_lmdb_basic_operations(tmpdir):
    """
    Test basic LMDB operations through py-lmdb compatible API.

    This is a simpler test focusing on core CRUD operations.
    """
    dbpath = os.path.join(tmpdir, 'test.lmdb')

    # Create environment and database
    env = lmdb.open(dbpath)

    # Write data
    with env.begin(write=True) as txn:
        txn.put(b'key1', b'value1')
        txn.put(b'key2', b'value2')
        txn.put(b'key3', b'value3')

    # Read data
    with env.begin() as txn:
        assert txn.get(b'key1') == b'value1'
        assert txn.get(b'key2') == b'value2'
        assert txn.get(b'key3') == b'value3'
        assert txn.get(b'nonexistent') is None

    # Update data
    with env.begin(write=True) as txn:
        txn.put(b'key2', b'new_value2')

    # Verify update
    with env.begin() as txn:
        assert txn.get(b'key2') == b'new_value2'

    # Delete data
    with env.begin(write=True) as txn:
        assert txn.delete(b'key1') is True
        assert txn.delete(b'nonexistent') is False

    # Verify deletion
    with env.begin() as txn:
        assert txn.get(b'key1') is None
        assert txn.get(b'key2') == b'new_value2'
        assert txn.get(b'key3') == b'value3'

    env.close()


def test_lmdb_cursor_operations(tmpdir):
    """
    Test cursor operations for iteration and positioning.
    """
    dbpath = os.path.join(tmpdir, 'cursor-test.lmdb')
    env = lmdb.open(dbpath)

    # Insert data with predictable sorting
    with env.begin(write=True) as txn:
        for i in range(10):
            key = f'key{i:02d}'.encode()
            value = f'value{i}'.encode()
            txn.put(key, value)

    # Test cursor iteration (should be sorted)
    with env.begin() as txn:
        cursor = txn.cursor()
        entries = list(cursor)

        # Verify sorted order
        assert len(entries) == 10
        assert entries[0] == (b'key00', b'value0')
        assert entries[9] == (b'key09', b'value9')

        # Verify all entries are in order
        for i, (key, value) in enumerate(entries):
            expected_key = f'key{i:02d}'.encode()
            expected_value = f'value{i}'.encode()
            assert key == expected_key
            assert value == expected_value

    # Test cursor positioning
    with env.begin() as txn:
        cursor = txn.cursor()

        # Move to first
        assert cursor.first() is True
        assert cursor.key() == b'key00'

        # Move to last
        assert cursor.last() is True
        assert cursor.key() == b'key09'

        # Move to specific key
        assert cursor.set_key(b'key05') is True
        assert cursor.key() == b'key05'
        assert cursor.value() == b'value5'

        # Move next
        assert cursor.next() is True
        assert cursor.key() == b'key06'

        # Move prev
        assert cursor.prev() is True
        assert cursor.key() == b'key05'

    env.close()


def test_lmdb_environment_info(tmpdir):
    """
    Test environment info and statistics.
    """
    dbpath = os.path.join(tmpdir, 'info-test.lmdb')
    env = lmdb.open(dbpath, map_size=10*1024*1024)  # 10MB

    # Get environment info
    info = env.info()
    assert info['map_size'] == 10*1024*1024
    assert info['last_pgno'] >= 0
    assert info['last_txnid'] >= 0
    assert info['max_readers'] > 0
    assert info['num_readers'] >= 0

    # Get environment stats
    stats = env.stat()
    assert stats['psize'] > 0
    assert stats['depth'] >= 0
    assert stats['entries'] >= 0

    env.close()


if __name__ == '__main__':
    # Allow running as a script for quick testing
    import sys
    tmpdir = tempfile.mkdtemp()
    try:
        test_address_book_example(tmpdir)
        test_lmdb_basic_operations(tmpdir)
        test_lmdb_cursor_operations(tmpdir)
        test_lmdb_environment_info(tmpdir)
        print("✓ All tests passed!")
    finally:
        shutil.rmtree(tmpdir)
