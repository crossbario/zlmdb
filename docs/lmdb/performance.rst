LMDB API Performance
====================

.. note::
   **Status:** This page is under development.

Performance characteristics and optimization techniques specific to the LMDB API.

Overview
--------

This page focuses on performance aspects of the **low-level LMDB API**, including:

- Read and write throughput
- Transaction overhead
- Cursor performance
- Memory usage patterns

For overall zlmdb performance comparisons, see :doc:`../performance`.

Coming Soon
-----------

This page will cover:

1. **Read Performance**
   - Lock-free MVCC reads
   - Memory-mapped I/O benefits
   - Zero-copy operations
   - Cursor iteration speed
   - Benchmarks: reads per second

2. **Write Performance**
   - Transaction overhead
   - Batch write strategies
   - Sync vs async modes
   - fsync impact
   - Benchmarks: writes per second

3. **Transaction Overhead**
   - Transaction begin/commit cost
   - Optimal transaction sizes
   - Long-lived transaction impact
   - MVCC snapshot management

4. **Cursor Performance**
   - Sequential vs random access
   - Forward vs reverse iteration
   - Key positioning strategies
   - Range query optimization

5. **Memory Usage**
   - Memory-mapped file behavior
   - Page cache utilization
   - Working set considerations
   - Multi-process memory sharing

6. **Optimization Techniques**
   - Batching strategies
   - Transaction sizing
   - Database configuration (map_size, max_dbs)
   - Key design for performance

7. **Platform-Specific Notes**
   - Linux performance characteristics
   - macOS differences
   - Windows performance
   - ARM64 vs x86-64

Benchmark Results
-----------------

*(Benchmarks from dirtybench.py, nastybench.py, parabench.py to be added)*

See Also
--------

- :doc:`../performance` - Overall performance comparison
- :doc:`../orm/performance` - ORM API performance
- :doc:`examples` - Performance benchmark examples
