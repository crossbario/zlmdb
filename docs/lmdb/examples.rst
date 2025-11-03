LMDB Examples
=============

.. note::
   **Status:** This page is under development.

Complete working examples demonstrating LMDB API usage patterns.

Overview
--------

zlmdb includes several example programs in ``examples/lmdb/`` that demonstrate real-world usage patterns:

- ``address-book.py`` - Basic CRUD operations with multiple databases
- ``dirtybench.py`` - Write performance benchmarking
- ``dirtybench-gdbm.py`` - Comparison with GDBM
- ``nastybench.py`` - Stress testing and edge cases
- ``parabench.py`` - Parallel access patterns

Coming Soon
-----------

This page will provide detailed documentation for each example:

1. **address-book.py: Basic Operations**
   - Multi-database setup (home/business contacts)
   - CRUD operations (Create, Read, Update, Delete)
   - Iteration with cursors
   - Transaction management

2. **dirtybench.py: Write Performance**
   - Batch write operations
   - Transaction batching strategies
   - Performance measurement
   - Comparison methodology

3. **dirtybench-gdbm.py: Database Comparison**
   - LMDB vs GDBM performance
   - Write throughput comparison
   - Use case analysis

4. **nastybench.py: Stress Testing**
   - High-volume operations
   - Edge case handling
   - Robustness testing
   - Error recovery

5. **parabench.py: Parallel Access**
   - Multi-process access patterns
   - Reader/writer coordination
   - Lock-free read performance
   - Write serialization

Running the Examples
--------------------

Each example can be run directly::

   python examples/lmdb/address-book.py

See the justfile for convenience recipes::

   just test-examples-lmdb-addressbook
   just test-examples-lmdb-dirtybench
   just test-examples-lmdb-nastybench
   just test-examples-lmdb-parabench

See Also
--------

- :doc:`index` - LMDB API overview
- :doc:`quickstart` - Getting started guide
- :doc:`performance` - Performance benchmarks
