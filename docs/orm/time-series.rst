Time-Series Data Patterns
=========================

.. note::
   **Status:** This page is under development.

Advanced patterns for storing and querying time-series data with zlmdb ORM.

Overview
--------

zlmdb excels at time-series data through:

- **Composite primary keys** with timestamps
- **Time partitioning** for efficient queries
- **Range queries** via ``select()``
- **NumPy array storage** for OHLCV data

Coming Soon
-----------

This page will cover patterns from **pydefi** (cryptocurrency data platform):

1. **Composite Key Design**
   - (market_oid, timestamp, trade_id) pattern
   - (period_dur, market_oid, timestamp) pattern
   - Key ordering for efficient queries

2. **Time Partitioning**
   - Using period_dur as first key component
   - PeriodDuration enum (NOW, SECOND, MINUTE, HOUR, DAY)
   - Efficient pruning of old data

3. **Trade Storage**
   - MapUuidTimestampUuidFlatBuffers
   - Composite key: (market_oid, txn_ts, oid)
   - Example from pydefi.database.trade

4. **OHLCV Candles**
   - Time-aggregated trade data
   - Composite key: (period_dur, start_ts, market_oid)
   - Example from pydefi.database.candle

5. **Order Book Snapshots**
   - MapUint16UuidTimestampFlatBuffers
   - NumPy arrays for price/size levels
   - Background persistence thread pattern
   - Example from pydefi LOB replica

6. **Range Queries**
   - Querying time ranges with select()
   - from_key/to_key construction
   - Forward vs reverse iteration
   - Getting "most recent" efficiently

7. **Integer Scaling for Precision**
   - Avoiding floating-point issues
   - Tick size and step size
   - uint32 storage for prices/sizes
   - Example: 0.0005 USD tick → 2000 scale factor

8. **Background Writer Pattern**
   - Deque-based write queue
   - Foreground capture, background persistence
   - Maintaining real-time responsiveness
   - Example from pydefi._lob2replica

Real-World Example
------------------

**pydefi Architecture**:

- Real-time WebSocket → in-memory order book
- Clock tick (100ms) → snapshot
- Background thread → database write
- Query historical states → range query

Performance Characteristics
---------------------------

*Benchmarks and optimization tips to be added*

See Also
--------

- :doc:`schema-design` - Composite key patterns
- :doc:`performance` - Time-series performance
- :doc:`best-practices` - Production patterns
