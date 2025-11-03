Schema Design Patterns
======================

.. note::
   **Status:** This page is under development.

Learn schema design patterns from production zlmdb applications.

Overview
--------

This guide covers:

- The ``@table`` decorator pattern
- Schema class architecture
- Table attachment with ``Schema.attach()``
- Foreign key relationships
- Schema versioning with UUIDs

Coming Soon
-----------

This page will cover patterns from **Crossbar.io** (cfxdb) and **pydefi**:

1. **The Schema Class Pattern**
   - Schema class definition
   - Table type hints
   - ``Schema.attach()`` factory method
   - Example from cfxdb.cookiestore

2. **Table Definitions with @table**
   - UUID-based table identifiers
   - Serialization parameter binding
   - Main tables vs index tables
   - Example from pydefi.database.exchange

3. **Object Classes**
   - Lazy loading from FlatBuffers
   - Property decorators with type hints
   - ``marshal()`` and ``parse()`` methods
   - ``build()`` and ``cast()`` for FlatBuffers

4. **Foreign Key Relationships**
   - UUID-based references
   - Hierarchical data modeling
   - Example: Market → Exchange, Market → Pair
   - Lookup patterns

5. **Schema Versioning**
   - UUID table identifiers for versioning
   - Schema evolution strategies
   - Backward compatibility

6. **Multi-Table Schemas**
   - Organizing related tables
   - GlobalSchema example (Crossbar.io)
   - PyDefi schema (20+ tables)

Real-World Examples
-------------------

Examples will be drawn from:

- **cfxdb.cookiestore**: Cookie authentication (Crossbar.io)
- **cfxdb.globalschema**: Management realm (20+ tables)
- **pydefi.database**: Cryptocurrency data (exchanges, markets, trades)

See Also
--------

- :doc:`index` - ORM overview
- :doc:`indexes` - Index patterns
- :doc:`serialization` - Serialization choices
