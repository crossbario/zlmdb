ORM Best Practices
==================

.. note::
   **Status:** This page is under development.

Production-proven patterns and best practices from real zlmdb applications.

Overview
--------

Learn from production deployments:

- **Crossbar.io**: High-throughput event storage
- **pydefi**: Real-time cryptocurrency data
- **crossbar-examples**: Benchmark patterns

Coming Soon
-----------

This page will compile best practices from real-world usage:

1. **Schema Design**
   - UUID-based table identifiers for versioning
   - Foreign key documentation in docstrings
   - Type hints throughout
   - marshal() methods for debugging

2. **Transaction Patterns**
   - Always use context managers
   - Check before access pattern
   - Batch writes for throughput
   - Short-lived write transactions

3. **Index Usage**
   - Use indexes for lookups (never scan)
   - Composite indexes for multi-field lookups
   - Nullable indexes for optional fields
   - Index update performance considerations

4. **Serialization Choices**
   - FlatBuffers for hot path
   - CBOR for configuration
   - NumPy for time-series
   - JSON for debugging only

5. **Error Handling**
   - Check index lookups return values
   - Handle missing keys gracefully
   - Transaction retry patterns
   - MapFullError handling

6. **Performance Patterns**
   - Buffered writes (Crossbar.io realmstore pattern)
   - Background persistence threads (pydefi pattern)
   - Lazy loading (FlatBuffers pattern)
   - Integer scaling (pydefi precision pattern)

7. **Testing Strategies**
   - Temporary databases for tests
   - Database scratching (purge)
   - Verification steps
   - Integration testing

8. **Deployment Considerations**
   - Database sizing (map_size)
   - Backup strategies
   - Multi-process access
   - PyPy for performance

9. **Monitoring and Debugging**
   - Database statistics (db.stats())
   - Count operations
   - marshal() for inspection
   - Logging patterns

10. **Common Anti-Patterns to Avoid**
    - Don't scan full tables (use indexes!)
    - Don't commit after every write (batch!)
    - Don't store large blobs directly (use pointers)
    - Don't use long-lived write transactions

Code Examples from Production
------------------------------

Each best practice will include real code examples from:

- Crossbar.io (cfxdb)
- pydefi
- crossbar-examples

Migration Patterns
------------------

Migrating from other databases or storage systems.

See Also
--------

- :doc:`schema-design` - Schema patterns
- :doc:`performance` - Performance optimization
- :doc:`time-series` - Advanced patterns
