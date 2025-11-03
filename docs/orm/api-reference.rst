ORM API Reference
=================

.. note::
   **Status:** This page is under development.

Complete API reference for the zlmdb ORM (object-relational mapping).

Overview
--------

This reference documents all ORM classes, decorators, and methods.

Coming Soon
-----------

This page will provide detailed API documentation for:

1. **Core Classes**
   - ``Database`` - Database handle
   - ``Schema`` - Schema base class
   - ``Transaction`` - ORM transaction wrapper

2. **Decorators**
   - ``@table`` - Table class decorator
   - Parameters: UUID, build, cast, marshal, parse

3. **Table Types (Pmap Classes)**
   - ``MapStringJson`` - String keys, JSON values
   - ``MapUuidJson`` - UUID keys, JSON values
   - ``MapStringCbor`` - String keys, CBOR values
   - ``MapUuidCbor`` - UUID keys, CBOR values
   - ``MapUuidFlatBuffers`` - UUID keys, FlatBuffers values
   - ``MapUuidTimestampUuidFlatBuffers`` - Composite key (UUID, timestamp, UUID)
   - ``MapUint16UuidTimestampFlatBuffers`` - Composite key (uint16, UUID, timestamp)
   - ``MapBytes20Numpy`` - NumPy array storage
   - And many more...

4. **Index Types**
   - ``MapStringUuid`` - String → UUID index
   - ``MapUuidStringUuid`` - (UUID, string) → UUID index
   - ``MapUuidUuid`` - UUID → UUID index

5. **Schema Methods**
   - ``Schema.attach(db)`` - Attach schema to database
   - ``db.attach_table(TableClass)`` - Attach table
   - ``table.attach_index(name, index_table, lambda)`` - Attach index

6. **Database Methods**
   - ``Database.open()`` - Open database
   - ``Database.scratch()`` - Purge database
   - ``db.begin()`` - Start transaction
   - ``db.stats()`` - Get statistics
   - ``db.__enter__()`` / ``db.__exit__()`` - Context manager

7. **Table Operations**
   - ``table[txn, key]`` - Get value
   - ``table[txn, key] = value`` - Set value
   - ``del table[txn, key]`` - Delete key
   - ``table.count(txn)`` - Count records
   - ``table.select(txn, ...)`` - Range query

For now, see the main :doc:`../reference` for auto-generated API documentation.

See Also
--------

- :doc:`index` - ORM overview
- :doc:`quickstart` - Getting started
- :doc:`schema-design` - Schema patterns
