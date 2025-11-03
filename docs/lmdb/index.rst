Low-Level LMDB API
==================

Overview
--------

The **zlmdb low-level LMDB API** (``zlmdb.lmdb``) provides direct access to LMDB's core functionality with full control over transactions, cursors, and database operations.

This API is:

- **py-lmdb compatible**: Drop-in replacement for the popular py-lmdb package
- **Full-featured**: Complete access to LMDB capabilities
- **High-performance**: Minimal overhead, maximum speed
- **Expert-friendly**: For users who know LMDB and want fine-grained control

.. code-block:: python

   import zlmdb.lmdb as lmdb

   env = lmdb.open('/tmp/mydb', max_dbs=10)
   db = env.open_db(b'users')

   with env.begin(write=True) as txn:
       txn.put(b'alice', b'alice@example.com', db=db)

When to Use the Low-Level API
------------------------------

Choose the low-level LMDB API when you:

**Need Maximum Performance**
   - Every nanosecond counts
   - Want zero abstraction overhead
   - Direct control over memory layout

**Have Existing py-lmdb Code**
   - Migration from py-lmdb
   - Existing scripts and tools
   - Familiarity with LMDB concepts

**Require Fine-Grained Control**
   - Custom key/value encodings
   - Specialized cursor operations
   - Advanced LMDB features (duplicate keys, etc.)

**Want Simplicity**
   - No schema required
   - No serialization layer
   - Pure key-value operations

When NOT to Use the Low-Level API
----------------------------------

Consider the :doc:`../orm/index` instead if you:

- Want automatic serialization (JSON, CBOR, FlatBuffers)
- Need schema management and type safety
- Prefer object-oriented data access
- Want automatic indexes and relationships
- Are building a Python application (not a system tool)

The ORM provides these conveniences while maintaining good performance.

Key Differences from py-lmdb
-----------------------------

zlmdb's ``zlmdb.lmdb`` is designed as a **drop-in replacement** for py-lmdb with the following differences:

**Implementation**
   - zlmdb uses **CFFI** (not CPyExt)
   - Better PyPy performance (JIT-friendly)
   - Same API surface

**Dependencies**
   - zlmdb bundles LMDB (vendored)
   - py-lmdb requires system LMDB installation
   - zlmdb has no external dependencies

**Compatibility**
   Both libraries are compatible at the database file level - databases created with py-lmdb can be opened with zlmdb and vice versa.

Quick Start
-----------

Basic operations with the low-level API:

**Opening a database:**

.. code-block:: python

   import zlmdb.lmdb as lmdb

   # Open environment (directory, not file)
   env = lmdb.open('/tmp/mydb',
                   map_size=10*1024*1024,  # 10MB
                   max_dbs=10)              # Number of named databases

   # Open (or create) a named database
   db = env.open_db(b'users')

**Writing data:**

.. code-block:: python

   # Write transaction
   with env.begin(write=True) as txn:
       txn.put(b'alice', b'alice@example.com', db=db)
       txn.put(b'bob', b'bob@example.com', db=db)
       # Automatic commit on context exit

**Reading data:**

.. code-block:: python

   # Read transaction
   with env.begin() as txn:
       email = txn.get(b'alice', db=db)
       print(email)  # b'alice@example.com'

**Iterating with cursors:**

.. code-block:: python

   with env.begin() as txn:
       with txn.cursor(db=db) as cursor:
           for key, value in cursor:
               print(f"{key.decode()}: {value.decode()}")

For complete examples, see :doc:`quickstart`.

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   quickstart
   transactions
   cursors
   examples
   performance
   api-reference

Core Concepts
-------------

Environment
~~~~~~~~~~~

An LMDB **environment** is a directory containing one or more databases:

.. code-block:: python

   env = lmdb.open('/path/to/dir',
                   map_size=1024*1024*1024,  # 1GB
                   max_dbs=10,                # Up to 10 named databases
                   readonly=False,             # Read-write mode
                   metasync=True,              # Sync metadata
                   sync=True,                  # Sync data
                   map_async=False)            # Sync immediately

**Key parameters:**

- ``map_size``: Maximum database size (can be very large, only uses what's needed)
- ``max_dbs``: Number of named databases (sub-databases) allowed
- ``readonly``: Open in read-only mode (allows multiple reader processes)
- ``sync``: Flush data to disk on commit (durable but slower)

Database
~~~~~~~~

A **database** is a key-value store within an environment:

.. code-block:: python

   # Unnamed database (default)
   db = None

   # Named database
   db = env.open_db(b'users', dupsort=False)

**Parameters:**

- ``dupsort``: Allow duplicate keys (default: False)
- ``create``: Create if doesn't exist (default: True)

Transactions
~~~~~~~~~~~~

**Transactions** provide ACID guarantees:

.. code-block:: python

   # Read transaction (shared lock)
   with env.begin() as txn:
       value = txn.get(b'key', db=db)

   # Write transaction (exclusive lock)
   with env.begin(write=True) as txn:
       txn.put(b'key', b'value', db=db)
       txn.delete(b'old_key', db=db)

**Properties:**

- Read transactions are lock-free (MVCC)
- Write transactions serialize automatically
- Nested transactions not supported
- Use context managers for automatic commit/abort

See :doc:`transactions` for advanced patterns.

Cursors
~~~~~~~

**Cursors** enable efficient iteration and positioning:

.. code-block:: python

   with env.begin() as txn:
       with txn.cursor(db=db) as cursor:
           # Iterate all records
           for key, value in cursor:
               process(key, value)

           # Seek to position
           if cursor.set_key(b'start_key'):
               # Found, now iterate from here
               for key, value in cursor:
                   process(key, value)

See :doc:`cursors` for cursor operations.

Performance Characteristics
---------------------------

The low-level API delivers exceptional performance:

**Reads**
   - **Lock-free**: MVCC allows concurrent readers
   - **Zero-copy**: Memory-mapped I/O, no buffer copying
   - **Millions of reads/sec** on modern hardware

**Writes**
   - **Serialized**: One writer at a time
   - **Batch-friendly**: Commit overhead amortized over transaction
   - **Hundreds of thousands of writes/sec**

**Memory**
   - **Shared**: Memory-mapped pages shared across processes
   - **Efficient**: Only active data in RAM
   - **No cache**: OS manages page cache

See :doc:`performance` for detailed benchmarks.

Best Practices
--------------

**Use context managers:**

.. code-block:: python

   # Good: Auto-commit/abort
   with env.begin(write=True) as txn:
       txn.put(b'key', b'value')

   # Bad: Manual management
   txn = env.begin(write=True)
   txn.put(b'key', b'value')
   txn.commit()

**Batch writes:**

.. code-block:: python

   # Good: One transaction for many writes
   with env.begin(write=True) as txn:
       for key, value in data:
           txn.put(key, value, db=db)

   # Bad: Many transactions
   for key, value in data:
       with env.begin(write=True) as txn:
           txn.put(key, value, db=db)

**Use appropriate map_size:**

.. code-block:: python

   # Good: Generous map_size (only uses what's needed)
   env = lmdb.open(path, map_size=10*1024*1024*1024)  # 10GB

   # Bad: Too small, requires frequent resizing
   env = lmdb.open(path, map_size=1024*1024)  # 1MB

**Close resources:**

.. code-block:: python

   # Always close when done
   env.close()

   # Or use context manager (Python 3.10+)
   with lmdb.open(path) as env:
       # Use env
       pass

Migration from py-lmdb
----------------------

If you have existing py-lmdb code, migration is simple:

**Change import:**

.. code-block:: python

   # Old
   import lmdb

   # New
   import zlmdb.lmdb as lmdb

That's it! Your code should work unchanged.

**Why migrate?**

- **Vendored LMDB**: No system dependency
- **Binary wheels**: Easy installation
- **PyPy performance**: CFFI-based for JIT optimization
- **Consistent versioning**: LMDB version bundled with zlmdb

Examples
--------

See :doc:`examples` for complete working examples:

- **address-book.py**: Simple CRUD operations
- **dirtybench.py**: Write performance benchmarking
- **nastybench.py**: Stress testing
- **parabench.py**: Parallel access patterns

Next Steps
----------

- :doc:`quickstart` - Learn basic operations
- :doc:`transactions` - Master transaction patterns
- :doc:`cursors` - Efficient iteration and seeking
- :doc:`examples` - Study complete working examples
- :doc:`performance` - Understand performance characteristics

.. seealso::

   - `LMDB Documentation <https://lmdb.readthedocs.io/>`_
   - `LMDB Paper (SIGMOD 2016) <https://www.cs.princeton.edu/courses/archive/fall17/cos518/studpres/lmdb.pdf>`_
   - :doc:`../orm/index` - High-level ORM alternative
