LMDB Cursors
=============

.. note::
   **Status:** This page is under development.

Guide to using LMDB cursors for efficient iteration and positioning within databases.

Overview
--------

Cursors provide fine-grained control over database traversal:

- Efficient iteration over key ranges
- Positioning at specific keys
- Forward and reverse traversal
- Duplicate key handling

Coming Soon
-----------

This page will cover:

1. **Creating Cursors**
   - Opening cursors within transactions
   - Cursor lifecycle
   - Context managers

2. **Navigation Methods**
   - ``first()``, ``last()``
   - ``next()``, ``prev()``
   - ``set_key()``, ``set_range()``

3. **Iteration Patterns**
   - Forward iteration
   - Reverse iteration
   - Range queries
   - Key prefix matching

4. **Cursor Operations**
   - Reading key/value pairs
   - Updating at cursor position
   - Deleting at cursor position

5. **Advanced Features**
   - Duplicate keys (dupsort)
   - Cursor positioning strategies
   - Performance optimization

See Also
--------

- :doc:`index` - LMDB API overview
- :doc:`transactions` - Transaction management
- :doc:`quickstart` - Basic cursor usage
