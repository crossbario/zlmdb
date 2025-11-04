High-Level ORM API
==================

.. note::
   **Status:** This page is under development.

Overview
--------

The **zlmdb ORM (Object-Relational Mapping) API** provides a high-level, Pythonic interface for working with LMDB databases through:

- **Schema-driven design** with ``@table`` decorator
- **Automatic serialization** (JSON, CBOR, FlatBuffers, NumPy)
- **Type-safe** object persistence
- **Index management** for efficient lookups
- **Relationship support** through foreign keys

.. code-block:: python

   import zlmdb
   from uuid import uuid4

   # Define schema
   schema = zlmdb.Schema()

   # Use built-in table types
   schema.users = zlmdb.MapUuidCbor(1,
                                    marshal=lambda u: u.__dict__,
                                    parse=lambda d: User(**d))

   # Open database and use
   db = zlmdb.Database.open('/tmp/mydb')
   db.__enter__()

   with db.begin(write=True) as txn:
       user = User(uuid4(), 'Alice', 'alice@example.com')
       schema.users[txn, user.oid] = user

When to Use the ORM API
-----------------------

Choose the ORM API when you:

**Want Object Persistence**
   - Store Python objects directly
   - Automatic serialization/deserialization
   - Type-safe data access

**Need Schema Management**
   - Define tables with decorators
   - Manage indexes automatically
   - Schema versioning

**Prefer High-Level API**
   - Less boilerplate code
   - Object-oriented interface
   - Built-in patterns (foreign keys, indexes)

**Building Applications**
   - Web applications
   - Data analysis tools
   - Business logic applications

When NOT to Use the ORM API
---------------------------

Consider the :doc:`../lmdb/index` instead if you:

- Need absolute maximum performance
- Want minimal overhead
- Have simple key-value needs
- Are porting existing py-lmdb code

The low-level API provides direct LMDB access without serialization overhead.

Coming Soon
-----------

This page will be expanded to cover:

1. **ORM Architecture**
   - Schema class pattern
   - Table types and decorators
   - Index management

2. **Core Concepts**
   - Database and Schema
   - Tables and Indexes
   - Transactions (ORM style)
   - Serialization strategies

3. **Quick Comparison**
   - ORM vs Low-level API
   - Performance trade-offs
   - Use case guidance

Real-World Usage
----------------

The ORM API is used in production by:

**Crossbar.io** (via cfxdb)
   - Cookie authentication storage
   - WAMP event history
   - XBR blockchain data
   - Management realm persistence

**pydefi**
   - Cryptocurrency market data
   - Real-time order books
   - Time-series storage
   - Blockchain integration

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   quickstart
   examples
   schema-design
   indexes
   serialization
   time-series
   performance
   best-practices
   api-reference

Quick Start
-----------

See :doc:`quickstart` for your first ORM application.

Key Features Preview
--------------------

**Multiple Serialization Formats**

.. code-block:: python

   # JSON (human-readable)
   users_json = zlmdb.MapUuidJson(slot=1)

   # CBOR (binary, compact)
   users_cbor = zlmdb.MapUuidCbor(slot=2,
                                  marshal=..., parse=...)

   # FlatBuffers (zero-copy, fastest)
   users_fbs = zlmdb.MapUuidFlatBuffers(slot=3,
                                         build=..., cast=...)

**Composite Keys**

.. code-block:: python

   # Time-series: (market_id, timestamp, trade_id)
   trades = zlmdb.MapUuidTimestampUuidFlatBuffers(slot=10)

   with db.begin(write=True) as txn:
       trades[txn, (market_id, timestamp, trade_id)] = trade

**Indexes**

.. code-block:: python

   # Main table
   schema.users = db.attach_table(Users)

   # Index by email
   schema.idx_users_by_email = db.attach_table(IndexUsersByEmail)

   # Link index to table
   schema.users.attach_index('idx1',
                             schema.idx_users_by_email,
                             lambda user: user.email)

See :doc:`schema-design` and :doc:`indexes` for complete patterns.

Next Steps
----------

- :doc:`quickstart` - Build your first ORM application
- :doc:`examples` - Real-world patterns from Crossbar.io and pydefi
- :doc:`schema-design` - Learn schema patterns from real projects
- :doc:`serialization` - Choose the right serialization format
- :doc:`indexes` - Efficient lookups and queries

.. seealso::

   - :doc:`../lmdb/index` - Low-level LMDB API alternative
   - `cfxdb <https://github.com/crossbario/cfxdb>`_ - Production ORM schemas
