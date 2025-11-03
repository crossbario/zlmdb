Introduction
============

What is zlmdb?
--------------

**zlmdb** is a transactional, embedded, in-memory database layer for Python that provides **two complementary APIs in one package**:

1. **Low-level LMDB API** - Direct access to LMDB with full control over transactions, cursors, and database operations
2. **High-level ORM API** - Object-relational mapping with automatic serialization, indexing, and schema management

zlmdb combines the raw performance of LMDB (Lightning Memory-Mapped Database) with the convenience of a modern Python ORM, making it ideal for applications that require both speed and ease of use.

.. note::
   **When to use zlmdb:**

   - Embedded database needs (no separate server process)
   - High-throughput read/write operations (millions of IOPS)
   - ACID transactional guarantees
   - Memory-mapped I/O for fast access
   - Both CPython and PyPy deployment

Key Features
------------

Dual API Design
~~~~~~~~~~~~~~~

zlmdb offers **two ways to work with LMDB**, depending on your needs:

**Low-level LMDB API** (``zlmdb.lmdb``)
   - Drop-in replacement for py-lmdb
   - Direct access to LMDB transactions and cursors
   - Full control over database operations
   - Maximum performance for expert users
   - See :doc:`lmdb/index` for details

**High-level ORM API** (``zlmdb``)
   - Type-safe persistent objects with automatic serialization
   - Schema definition with ``@table`` decorator
   - Automatic index management
   - Support for composite keys and foreign keys
   - See :doc:`orm/index` for details

Performance Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~

zlmdb delivers exceptional performance through LMDB's architecture:

**High IOPS (Input/Output Operations Per Second)**
   - Read operations: **Millions of reads per second** on modern hardware
   - Write operations: **Hundreds of thousands of writes per second**
   - Memory-mapped I/O eliminates buffer cache overhead
   - Zero-copy operations for maximum efficiency
   - See :doc:`performance` for detailed benchmarks

**Transactional Robustness**
   - **ACID compliance** (Atomicity, Consistency, Isolation, Durability)
   - MVCC (Multi-Version Concurrency Control) for lock-free reads
   - Write transactions are fully serialized
   - Crash-proof design with copy-on-write B+trees
   - No write-ahead logging or recovery needed

**Memory Efficiency**
   - Memory-mapped files shared across processes
   - Minimal memory overhead (metadata only)
   - No deserialization needed for memory-mapped data
   - Efficient storage with no internal fragmentation

Flexible Serialization
~~~~~~~~~~~~~~~~~~~~~~

The ORM API supports multiple serialization formats:

**JSON** (``MapStringJson``, ``MapUuidJson``, etc.)
   - Human-readable format
   - Great for debugging and data inspection
   - Good for configuration data
   - Slower than binary formats

**CBOR** (``MapStringCbor``, ``MapUuidCbor``, etc.)
   - Compact binary format
   - Faster than JSON
   - Supports more Python types (bytes, datetime, etc.)
   - Good balance of flexibility and performance

**FlatBuffers** (``MapUuidFlatBuffers``, etc.)
   - Zero-copy deserialization
   - Maximum performance
   - Schema evolution support
   - Used by production systems (Crossbar.io, pydefi)
   - Requires FlatBuffers schema definition

**NumPy Arrays** (``MapBytes20Numpy``, etc.)
   - Direct storage of NumPy arrays
   - Zero-copy access
   - Perfect for time-series and scientific data
   - Efficient vectorized operations

**Custom Serialization**
   - Define your own ``marshal``/``parse`` functions
   - Mix serialization strategies per table
   - See :doc:`orm/serialization` for details

Easy Installation and Deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

zlmdb is designed to be **batteries included** with **zero system dependencies**:

**Binary Wheels for All Platforms**
   - **CPython**: 3.11, 3.12, 3.13, 3.14 (including 3.14t free-threaded)
   - **PyPy**: 3.11
   - **Linux**: x86-64 (manylinux_2_34) and ARM64 (manylinux_2_28)
   - **macOS**: ARM64 (Apple Silicon)
   - **Windows**: x86-64

**CFFI-based Implementation**
   - Uses CFFI (C Foreign Function Interface), not CPyExt
   - Excellent PyPy performance (JIT-friendly)
   - No compilation needed during installation
   - See :doc:`installation` for platform compatibility table

**Vendored Dependencies**
   - LMDB library bundled (no external installation required)
   - FlatBuffers library bundled
   - Self-contained wheels
   - Works out of the box on fresh systems

**Simple Installation**::

   pip install zlmdb

That's it! No C compiler, no system libraries, no configuration.

Architecture Overview
---------------------

zlmdb is built on several key technologies:

.. graphviz::

   digraph architecture {
       rankdir=TB;
       node [shape=box, style=filled];

       app [label="Your Application", fillcolor=lightblue];

       subgraph cluster_zlmdb {
           label="zlmdb";
           style=filled;
           fillcolor=lightgray;

           orm [label="ORM API\n(Schema, Tables, Indexes)", fillcolor=lightyellow];
           lmdb_api [label="Low-level LMDB API\n(Transactions, Cursors)", fillcolor=lightyellow];

           serializers [label="Serializers\n(JSON, CBOR, FlatBuffers)", fillcolor=white];
       }

       cffi [label="CFFI\n(Foreign Function Interface)", fillcolor=lightgreen];
       lmdb_c [label="LMDB C Library\n(Vendored)", fillcolor=orange];

       app -> orm;
       app -> lmdb_api;
       orm -> serializers;
       orm -> lmdb_api;
       lmdb_api -> cffi;
       cffi -> lmdb_c;
   }

**Layer Stack:**

1. **Application Layer** - Your Python code using zlmdb
2. **ORM Layer** - High-level object mapping, schemas, indexes (optional)
3. **Serialization Layer** - Converts Python objects to bytes (when using ORM)
4. **LMDB API Layer** - Transaction and cursor management
5. **CFFI Layer** - Python ↔ C bridge
6. **LMDB C Library** - Core database engine (memory-mapped B+trees)

Use Cases
---------

zlmdb is ideal for:

**Embedded Databases**
   - Application-local storage without external database servers
   - Configuration and state persistence
   - Local caching layers

**High-Performance Applications**
   - Real-time data processing
   - Event sourcing and event stores
   - Session storage for web applications
   - Message queues and task queues

**Time-Series Data**
   - Financial market data (trades, order books, candles)
   - IoT sensor data
   - Application metrics and monitoring
   - See :doc:`orm/time-series` for patterns

**Network Applications**
   - Cookie stores (WAMP-Cookie authentication in Crossbar.io)
   - Session management
   - Realm stores (WAMP event history)
   - Blockchain data (XBR network in Crossbar.io)

**Data Analysis**
   - Intermediate results storage
   - Dataset caching
   - Benchmark results (see crossbar-examples)
   - Integration with Jupyter notebooks

Real-World Projects Using zlmdb
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

zlmdb powers production systems:

**Crossbar.io** (via cfxdb)
   Distributed application router using zlmdb for:

   - Cookie authentication storage
   - WAMP event history and session tracking
   - XBR (Crossbar Blockchain Router) network data
   - Management realm persistence

   See `cfxdb <https://github.com/crossbario/cfxdb>`_ for the database layer built on zlmdb.

**pydefi**
   Cryptocurrency data integration platform using zlmdb for:

   - Real-time market data (trades, order books, candles)
   - Exchange and market metadata
   - Blockchain block and transaction data
   - Time-series storage with composite keys

Quick Comparison
----------------

How zlmdb compares to alternatives:

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * - Feature
     - zlmdb
     - SQLite
     - Redis
     - MongoDB
   * - Embedded
     - ✅ Yes
     - ✅ Yes
     - ❌ Server
     - ❌ Server
   * - ACID
     - ✅ Full
     - ✅ Full
     - ⚠️ Partial
     - ⚠️ Partial
   * - Memory-mapped
     - ✅ Yes
     - ❌ No
     - ❌ No
     - ❌ No
   * - Reads/sec
     - Millions
     - Thousands
     - Millions
     - Thousands
   * - Multi-process
     - ✅ Yes
     - ⚠️ Locks
     - ✅ Yes
     - ✅ Yes
   * - Schema
     - Optional (ORM)
     - Required (SQL)
     - None
     - None
   * - Query language
     - Python API
     - SQL
     - Commands
     - MQL
   * - Dependencies
     - None
     - None
     - Server
     - Server

See :doc:`performance` for detailed benchmark comparisons.

Getting Started
---------------

Choose your starting point based on your needs:

**New to zlmdb?**
   Start with the :doc:`installation` guide, then:

   - **Want simple key-value storage?** → :doc:`lmdb/quickstart`
   - **Want object persistence with schemas?** → :doc:`orm/quickstart`

**Coming from py-lmdb?**
   zlmdb's low-level API is a drop-in replacement:

   - See :doc:`lmdb/index` for the compatibility layer
   - Your existing py-lmdb code should work unchanged

**Building a production application?**
   Study the ORM patterns from real projects:

   - :doc:`orm/schema-design` - Schema architecture patterns
   - :doc:`orm/indexes` - Efficient lookups and queries
   - :doc:`orm/time-series` - Time-series data modeling
   - :doc:`orm/best-practices` - Production-proven patterns

Next Steps
----------

.. toctree::
   :maxdepth: 1

   installation
   lmdb/index
   orm/index
   performance
   reference

**Additional Resources:**

- `GitHub Repository <https://github.com/crossbario/zlmdb>`_
- `Issue Tracker <https://github.com/crossbario/zlmdb/issues>`_
- `PyPI Package <https://pypi.org/project/zlmdb/>`_
- `LMDB Documentation <https://lmdb.readthedocs.io/>`_
