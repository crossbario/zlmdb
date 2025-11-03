Serialization Strategies
========================

.. note::
   **Status:** This page is under development.

Choose the right serialization format for your use case.

Overview
--------

zlmdb ORM supports multiple serialization formats:

- **JSON**: Human-readable, debugging-friendly
- **CBOR**: Compact binary, good balance
- **FlatBuffers**: Zero-copy, maximum performance
- **NumPy**: Direct array storage
- **Custom**: Roll your own marshal/parse

Coming Soon
-----------

This page will cover:

1. **Serialization Format Comparison**
   - JSON vs CBOR vs FlatBuffers vs NumPy
   - Performance characteristics
   - Use case guidance
   - Trade-offs table

2. **JSON Serialization**
   - When to use JSON
   - MapStringJson, MapUuidJson types
   - Limitations and gotchas

3. **CBOR Serialization**
   - Advantages over JSON
   - MapUuidCbor pattern
   - marshal/parse functions
   - Example from Crossbar.io GlobalSchema

4. **FlatBuffers Serialization**
   - Zero-copy deserialization
   - Schema definition (.fbs files)
   - build() and cast() methods
   - Lazy loading pattern
   - Examples from Crossbar.io and pydefi

5. **NumPy Array Storage**
   - Direct NumPy array persistence
   - Zero-copy access
   - Time-series and scientific data
   - Example from pydefi order books

6. **Mixed Strategies**
   - Using different formats for different tables
   - FlatBuffers for hot path, CBOR for config
   - Example: Crossbar.io architecture

7. **Custom Serialization**
   - Implementing custom marshal/parse
   - When to roll your own
   - Examples

Decision Guide
--------------

*Table comparing formats by: speed, size, flexibility, debugging*

Real-World Usage
----------------

**Crossbar.io**:
   - FlatBuffers: Events, sessions, publications (high throughput)
   - CBOR: Management realms, users, configuration

**pydefi**:
   - FlatBuffers: Trades, order books, candles (performance-critical)
   - CBOR: Exchange/market metadata
   - NumPy: Order book price/size arrays

See Also
--------

- :doc:`schema-design` - Schema patterns
- :doc:`performance` - Performance impact
- :doc:`../performance` - Overall benchmarks
