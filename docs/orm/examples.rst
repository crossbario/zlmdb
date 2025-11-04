ORM Examples
============

Real-world ORM usage patterns from production zlmdb applications.

Overview
--------

This guide demonstrates zlmdb ORM patterns drawn from production codebases:

- **Crossbar.io** via `cfxdb <https://github.com/crossbario/cfxdb>`_ - Session management, event history, authentication
- **pydefi** - Cryptocurrency market data persistence

All examples shown are from real production code, demonstrating battle-tested patterns.

Schema Architecture
-------------------

**Pattern from:** `cfxdb.cookiestore <https://github.com/crossbario/cfxdb/blob/master/cfxdb/cookiestore/cookiestore.py>`_

zlmdb ORM uses a **Schema** class to organize related tables:

.. code-block:: python

   from zlmdb import Schema

   class CookieStore(Schema):
       """
       Schema for HTTP cookie-based authentication.

       Used in Crossbar.io for web transport authentication.
       """

       def attach(self, db):
           """Attach tables to database environment"""
           # Define main tables
           self.cookies_by_authid = ...
           self.cookies_by_cookie_id = ...

           # Define index tables
           self.idx_cookies_by_modified = ...

**Key Concepts:**

1. **Schema class** organizes related tables
2. **``attach()`` method** binds tables to LMDB environment
3. **Table attributes** use type hints for IDE support
4. **Index tables** created alongside main tables

Table Definition with @table Decorator
---------------------------------------

**Pattern from:** `cfxdb.globalschema <https://github.com/crossbario/cfxdb/blob/master/cfxdb/globalschema/globalschema.py>`_

The ``@table`` decorator defines tables with UUID-based identifiers:

.. code-block:: python

   from zlmdb import table, MapUuidCbor, MapUuidFlatBuffers

   @table('e56ca7df-4cf2-4f38-a0ac-34d9be1ce9c3')
   class User:
       """User entity with CBOR serialization"""
       pass

   @table('a739ff38-d3ed-43c0-8a06-090ba7198c39',
          marshal=lambda obj: obj.build(),
          unmarshal=lambda data: User.cast(data))
   class Market:
       """Market entity with FlatBuffers serialization"""
       pass

**In schema class:**

.. code-block:: python

   class GlobalSchema(Schema):
       def attach(self, db):
           # Simple table with CBOR serialization
           self.users = MapUuidCbor(User)

           # Table with FlatBuffers (for performance)
           self.markets = MapUuidFlatBuffers(Market)

**Key Concepts:**

1. **UUID table identifiers** enable schema versioning
2. **``@table`` decorator** marks persistent classes
3. **Serialization strategies** chosen per table (CBOR vs FlatBuffers)
4. **``marshal``/``unmarshal``** customize serialization

Serialization Strategies
-------------------------

**From production usage analysis:**

CBOR Serialization (Simple Data)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**When to use:**

- Simple data structures (dicts, lists, primitives)
- Rapid development
- Schema flexibility
- Human-readable debugging

**Example from cfxdb:**

.. code-block:: python

   from zlmdb import MapUuidCbor

   # Cookie authentication data (simple dict)
   self.cookies = MapUuidCbor(1,
                              marshal=lambda obj: obj.__dict__,
                              unmarshal=lambda data: Cookie(**data))

**Characteristics:**

- ✅ Easy to use (automatic serialization)
- ✅ Handles Python types naturally
- ✅ Good for development/prototyping
- ⚠️ Slower than FlatBuffers for complex objects

FlatBuffers Serialization (Complex/Performance-Critical)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**When to use:**

- Complex nested structures
- Performance-critical paths
- Large datasets
- Type safety required

**Example from pydefi:**

.. code-block:: python

   from zlmdb import MapUuidFlatBuffers

   # Market data with complex schema
   self.markets = MapUuidFlatBuffers(2,
                                     build=Market.build,
                                     cast=Market.cast)

**Characteristics:**

- ✅ Zero-copy deserialization
- ✅ Strong type safety (schema evolution)
- ✅ Excellent performance
- ⚠️ Requires FlatBuffers schema definition

**Production guideline:** Start with CBOR for development, migrate to FlatBuffers when performance matters.

Index Patterns
--------------

**Pattern from:** `pydefi.database <https://github.com/pydefi/pydefi/tree/master/pydefi/database>`_

Indexes enable efficient lookups beyond primary keys:

Simple Index (One-to-Many)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from zlmdb import MapUuidUuidSet

   class MarketSchema(Schema):
       def attach(self, db):
           # Main table: market_id -> Market object
           self.markets = MapUuidFlatBuffers(1, ...)

           # Index: exchange_id -> set of market_ids
           self.markets_by_exchange = MapUuidUuidSet(2)

**Usage:**

.. code-block:: python

   # Write: insert market and update index
   with db.begin(write=True) as txn:
       # Insert main record
       schema.markets[txn, market.oid] = market

       # Update index
       schema.markets_by_exchange[txn, market.exchange_oid].add(market.oid)

   # Read: find all markets for an exchange
   with db.begin() as txn:
       market_ids = schema.markets_by_exchange[txn, exchange_id]
       for market_id in market_ids:
           market = schema.markets[txn, market_id]
           process(market)

Composite Index (Time-Series)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Pattern from pydefi for time-series data:**

.. code-block:: python

   from zlmdb import MapTimestampUuidCbor

   class TickerSchema(Schema):
       def attach(self, db):
           # Composite key: (timestamp, market_id) -> ticker data
           self.tickers = MapTimestampUuidCbor(3)

**Usage:**

.. code-block:: python

   # Write time-series data
   with db.begin(write=True) as txn:
       key = (ticker.timestamp, ticker.market_oid)
       schema.tickers[txn, key] = ticker.data

   # Range query: get all tickers for market in time range
   with db.begin() as txn:
       from_key = (start_time, market_id)
       to_key = (end_time, market_id)

       for (ts, mid), data in schema.tickers.select(txn,
                                                     from_key=from_key,
                                                     to_key=to_key):
           process(ts, data)

**Key Concepts:**

1. **Index tables** separate from main tables
2. **``MapUuidUuidSet``** for one-to-many relationships
3. **Composite keys** for time-series patterns
4. **Manual index maintenance** (application responsibility)

Foreign Key Relationships
--------------------------

**Pattern from:** pydefi market hierarchy

zlmdb uses **UUID-based foreign keys** for relationships:

.. code-block:: python

   from uuid import uuid4

   # Entity definitions
   @table('uuid-1')
   class Exchange:
       oid: UUID        # Primary key
       name: str

   @table('uuid-2')
   class Market:
       oid: UUID        # Primary key
       exchange_oid: UUID  # Foreign key to Exchange
       pair_oid: UUID      # Foreign key to Pair
       symbol: str

   # Schema with relationships
   class TradingSchema(Schema):
       def attach(self, db):
           self.exchanges = MapUuidCbor(1)
           self.markets = MapUuidCbor(2)
           self.pairs = MapUuidCbor(3)

           # Indexes for foreign key lookups
           self.markets_by_exchange = MapUuidUuidSet(10)
           self.markets_by_pair = MapUuidUuidSet(11)

**Usage:**

.. code-block:: python

   # Create related entities
   with db.begin(write=True) as txn:
       # Create exchange
       exchange = Exchange(oid=uuid4(), name="Binance")
       schema.exchanges[txn, exchange.oid] = exchange

       # Create market with foreign keys
       market = Market(
           oid=uuid4(),
           exchange_oid=exchange.oid,  # FK to exchange
           pair_oid=pair.oid,          # FK to pair
           symbol="BTC/USDT"
       )
       schema.markets[txn, market.oid] = market

       # Maintain indexes
       schema.markets_by_exchange[txn, exchange.oid].add(market.oid)
       schema.markets_by_pair[txn, pair.oid].add(market.oid)

   # Navigate relationships
   with db.begin() as txn:
       # Get market
       market = schema.markets[txn, market_id]

       # Follow FK to exchange
       exchange = schema.exchanges[txn, market.exchange_oid]

       # Find all markets for exchange (using index)
       market_ids = schema.markets_by_exchange[txn, exchange.oid]

**Key Concepts:**

1. **UUIDs for all primary keys**
2. **Foreign keys stored as UUID fields**
3. **No automatic cascade** (application manages)
4. **Indexes enable reverse lookups** (FK → PK)

Multi-Table Schemas
-------------------

**Pattern from:** `cfxdb.globalschema <https://github.com/crossbario/cfxdb/blob/master/cfxdb/globalschema/globalschema.py>`_

Large applications organize 20+ tables in a single schema:

.. code-block:: python

   class GlobalSchema(Schema):
       """
       Crossbar.io management realm schema (20+ tables).

       Organizes:
       - User/authentication tables
       - Node/worker management
       - Router realm configuration
       - Application deployment
       """

       def attach(self, db):
           # User management
           self.users = MapUuidCbor(1)
           self.credentials = MapUuidCbor(2)
           self.activations = MapUuidCbor(3)

           # Node management
           self.nodes = MapUuidCbor(10)
           self.workers = MapUuidCbor(11)
           self.controllers = MapUuidCbor(12)

           # Router configuration
           self.router_realms = MapUuidCbor(20)
           self.router_realm_roles = MapUuidCbor(21)

           # Indexes
           self.idx_users_by_email = MapStringUuid(100)
           self.idx_nodes_by_pubkey = MapBytesUuid(101)
           # ... 20 more tables

**Organizational Patterns:**

1. **Table ID ranges** by functional area (1-9: users, 10-19: nodes, etc.)
2. **Main tables** use low IDs (1-99)
3. **Index tables** use high IDs (100+)
4. **Type hints** on schema class for IDE support

Real-World Example: Cookie Authentication
------------------------------------------

**From:** `cfxdb.cookiestore module <https://github.com/crossbario/cfxdb/blob/master/cfxdb/cookiestore>`_

Complete example of Crossbar.io's HTTP cookie authentication:

**Schema:**

.. code-block:: python

   class CookieStore(Schema):
       """HTTP cookie-based authentication storage"""

       def attach(self, db):
           # Main table: authid -> cookie data
           self.cookies_by_authid = MapStringCbor(1)

           # Alternate lookup: cookie_id -> authid
           self.cookies_by_cookie_id = MapStringString(2)

           # Time-based index: modified timestamp -> authid
           self.idx_cookies_by_modified = MapTimestampString(3)

**Usage in Crossbar.io:**

.. code-block:: python

   # Store cookie on login
   def store_cookie(self, cookie_id, authid, authrole, max_age):
       with self.db.begin(write=True) as txn:
           cookie = {
               'cookie_id': cookie_id,
               'authid': authid,
               'authrole': authrole,
               'created': now,
               'max_age': max_age
           }

           # Store in main tables
           self.cookies_by_authid[txn, authid] = cookie
           self.cookies_by_cookie_id[txn, cookie_id] = authid

           # Update time index
           self.idx_cookies_by_modified[txn, now] = authid

   # Validate cookie on request
   def lookup_cookie(self, cookie_id):
       with self.db.begin() as txn:
           authid = self.cookies_by_cookie_id[txn, cookie_id]
           if authid:
               return self.cookies_by_authid[txn, authid]

   # Cleanup expired cookies
   def purge_expired(self):
       cutoff = time.time() - max_age
       with self.db.begin(write=True) as txn:
           # Use time index to find old cookies
           for ts, authid in self.idx_cookies_by_modified.select(
               txn, to_key=cutoff
           ):
               cookie = self.cookies_by_authid[txn, authid]

               # Delete from all tables
               del self.cookies_by_authid[txn, authid]
               del self.cookies_by_cookie_id[txn, cookie['cookie_id']]
               del self.idx_cookies_by_modified[txn, ts]

**Patterns Demonstrated:**

1. **Multiple access paths** (by authid, by cookie_id, by timestamp)
2. **Consistent updates** across all tables
3. **Time-based cleanup** using timestamp index
4. **CBOR serialization** for dict-based data

Real-World Example: Market Data (pydefi)
-----------------------------------------

**From:** `pydefi project <https://github.com/pydefi/pydefi>`_

Cryptocurrency market data persistence patterns:

**Schema:**

.. code-block:: python

   class PyDefiSchema(Schema):
       """Cryptocurrency market data (exchanges, markets, trades, tickers)"""

       def attach(self, db):
           # Entities (FlatBuffers for performance)
           self.exchanges = MapUuidFlatBuffers(1, ...)
           self.markets = MapUuidFlatBuffers(2, ...)
           self.pairs = MapUuidFlatBuffers(3, ...)

           # Time-series data (composite keys)
           self.trades = MapTimestampUuidFlatBuffers(10, ...)
           self.tickers = MapTimestampUuidFlatBuffers(11, ...)

           # Indexes
           self.markets_by_exchange = MapUuidUuidSet(100)
           self.markets_by_pair = MapUuidUuidSet(101)

**Usage:**

.. code-block:: python

   # Store market tick
   def store_ticker(self, market_id, timestamp, data):
       with self.db.begin(write=True) as txn:
           key = (timestamp, market_id)
           self.tickers[txn, key] = data

   # Query time-series data
   def get_tickers(self, market_id, start_time, end_time):
       with self.db.begin() as txn:
           from_key = (start_time, market_id)
           to_key = (end_time, market_id)

           tickers = []
           for (ts, mid), data in self.tickers.select(
               txn, from_key=from_key, to_key=to_key
           ):
               tickers.append((ts, data))
           return tickers

**Patterns Demonstrated:**

1. **FlatBuffers** for high-performance market data
2. **Composite keys** (timestamp, market_id) for time-series
3. **Range queries** using ``select()``
4. **Entity-relationship model** (Exchange → Market → Pair)

Best Practices from Production
-------------------------------

**1. Schema Organization**

- Group related tables in Schema classes
- Use UUID table identifiers (enables versioning)
- Reserve ID ranges for functional areas
- Document table purposes

**2. Serialization Choice**

- **CBOR:** Simple data, rapid development, dict-based
- **FlatBuffers:** Complex schemas, performance-critical, type safety
- **NumPy:** Numerical arrays, scientific data

**3. Index Strategy**

- Create indexes for frequent lookups
- Maintain indexes manually (no automatic cascades)
- Use ``MapUuidUuidSet`` for one-to-many
- Use composite keys for time-series

**4. Transaction Patterns**

- Keep transactions short
- Batch related operations
- Use read transactions by default
- Minimize write transaction duration

**5. Foreign Keys**

- Always use UUIDs for primary keys
- Store foreign keys as UUID fields
- Create indexes for reverse lookups
- Document relationships in schema class

Complete Schema Example
------------------------

Putting it all together:

.. code-block:: python

   from zlmdb import Schema, table
   from zlmdb import MapUuidCbor, MapUuidUuidSet, MapStringUuid
   from uuid import UUID

   @table('550e8400-e29b-41d4-a716-446655440001')
   class Company:
       oid: UUID
       name: str
       country: str

   @table('550e8400-e29b-41d4-a716-446655440002')
   class Employee:
       oid: UUID
       company_oid: UUID  # FK to Company
       email: str
       name: str

   class HRSchema(Schema):
       """Human resources database schema"""

       def attach(self, db):
           # Main tables
           self.companies = MapUuidCbor(1,
               marshal=lambda obj: obj.__dict__,
               unmarshal=lambda data: Company(**data))

           self.employees = MapUuidCbor(2,
               marshal=lambda obj: obj.__dict__,
               unmarshal=lambda data: Employee(**data))

           # Indexes
           self.employees_by_company = MapUuidUuidSet(10)
           self.employees_by_email = MapStringUuid(11)

   # Usage
   db = zlmdb.Database('/tmp/hr.db')
   schema = HRSchema.attach(db)

   # Insert company and employees
   with db.begin(write=True) as txn:
       company = Company(oid=uuid4(), name="Acme", country="US")
       schema.companies[txn, company.oid] = company

       for email in ["alice@acme.com", "bob@acme.com"]:
           employee = Employee(
               oid=uuid4(),
               company_oid=company.oid,
               email=email,
               name=email.split("@")[0]
           )
           schema.employees[txn, employee.oid] = employee
           schema.employees_by_company[txn, company.oid].add(employee.oid)
           schema.employees_by_email[txn, email] = employee.oid

   # Query: find all employees of a company
   with db.begin() as txn:
       company = schema.companies[txn, company_id]
       employee_ids = schema.employees_by_company[txn, company_id]

       for emp_id in employee_ids:
           employee = schema.employees[txn, emp_id]
           print(f"{employee.name} works at {company.name}")

See Also
--------

- :doc:`index` - ORM overview
- :doc:`quickstart` - Getting started
- :doc:`schema-design` - Schema design patterns
- :doc:`indexes` - Index management
- :doc:`serialization` - Serialization strategies
- `cfxdb repository <https://github.com/crossbario/cfxdb>`_ - Full source code
- `pydefi repository <https://github.com/pydefi/pydefi>`_ - Market data patterns
