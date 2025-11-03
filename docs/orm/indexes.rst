Indexes and Lookups
===================

.. note::
   **Status:** This page is under development.

Guide to creating and using indexes for efficient data retrieval.

Overview
--------

zlmdb's ORM supports:

- **Simple indexes** (string → UUID, UUID → UUID)
- **Composite indexes** ((UUID, string) → UUID)
- **Nullable indexes** (optional index keys)
- **Automatic index maintenance**

Coming Soon
-----------

This page will cover:

1. **Index Basics**
   - What indexes are and why they matter
   - Index tables vs main tables
   - Automatic index updates

2. **Creating Indexes**
   - Defining index tables with ``@table``
   - Index table types (MapStringUuid, MapUuidStringUuid, etc.)
   - Attaching indexes to main tables

3. **Simple Indexes**
   - Name → ID lookups
   - Example: IndexExchangeByName
   - Usage pattern from Crossbar.io

4. **Composite Indexes**
   - Multi-component keys
   - Example: IndexMarketByName (endpoint_oid, name) → market_oid
   - Usage pattern from pydefi

5. **Nullable Indexes**
   - Optional index keys
   - Example: IndexUsersByPubkey (nullable=True)
   - Usage pattern from Crossbar.io GlobalSchema

6. **Index Lookups**
   - Primary key lookups
   - Secondary index lookups
   - Lookup patterns (check then fetch)

7. **Compound String Indexes**
   - Concatenated string keys
   - Example: email + pubkey index
   - Use cases

Real-World Patterns
-------------------

Examples from production code:

- **Crossbar.io**: Cookie value → cookie OID
- **Crossbar.io**: User email/pubkey indexes (nullable)
- **pydefi**: Market name lookups (composite: endpoint + name)
- **pydefi**: Exchange name → exchange OID

See Also
--------

- :doc:`schema-design` - Schema patterns
- :doc:`index` - ORM overview
- :doc:`best-practices` - Index optimization tips
