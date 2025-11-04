LMDB Examples
=============

Complete working examples demonstrating LMDB API usage patterns and performance characteristics.

Overview
--------

zlmdb includes five example programs in ``examples/lmdb/`` that demonstrate real-world usage patterns:

- **address-book.py** - Basic CRUD operations with multiple databases
- **dirtybench.py** - Comprehensive write performance benchmarking
- **nastybench.py** - High-volume stress testing (1M+ keys)
- **parabench.py** - Parallel read performance testing
- **dirtybench-gdbm.py** - GDBM comparison benchmark

All examples use ``zlmdb.lmdb`` which provides py-lmdb compatible API.

address-book.py: Basic CRUD Operations
---------------------------------------

**Purpose:** Demonstrates fundamental LMDB operations with multiple named databases (subdbs).

**What it demonstrates:**

- Opening an environment with multiple databases
- Creating named subdatabases
- CRUD operations (Create, Read, Update, Delete)
- Transaction context managers
- Cursor-based iteration
- Database-scoped transactions

**Key Code Patterns:**

.. code-block:: python

   import zlmdb.lmdb as lmdb

   # Open environment with multiple databases
   env = lmdb.open("/tmp/address-book.lmdb", max_dbs=10)

   # Create named subdatabases
   home_db = env.open_db(b"home")
   business_db = env.open_db(b"business")

   # Write transaction
   with env.begin(write=True) as txn:
       txn.put(b"mum", b"012345678", db=home_db)
       txn.put(b"dad", b"011232211", db=home_db)

   # Read and iterate with cursor
   with env.begin() as txn:
       for key, value in txn.cursor(db=home_db):
           print(key, value)

   # Update operations
   with env.begin(write=True, db=home_db) as txn:
       txn.put(b"dentist", b"099991231")  # Update
       txn.delete(b"hospital")             # Delete

   # Drop all keys from a database
   with env.begin(write=True) as txn:
       txn.drop(business_db, delete=False)

**Running:**

.. code-block:: bash

   python examples/lmdb/address-book.py

   # Or using justfile:
   just test-examples-lmdb-addressbook

**Output:**

The example prints the contents of both databases, showing:

- Keys are automatically sorted (LMDB B+tree property)
- Cursor iteration works seamlessly
- Updates and deletes work as expected

**Learning Points:**

1. **Multiple databases:** Use ``max_dbs`` parameter when opening environment
2. **Context managers:** ``with env.begin()`` handles commit/abort automatically
3. **Default database:** Can specify ``db=`` parameter in ``begin()`` to avoid passing it to each operation
4. **Cursor iteration:** Efficient way to traverse keys in sorted order

dirtybench.py: Write Performance Benchmarking
----------------------------------------------

**Purpose:** Comprehensive benchmarking of LMDB write and read operations using real dictionary words.

**What it demonstrates:**

- Insert performance (random vs sequential keys)
- Lookup performance (various methods)
- Cursor operations (putmulti, iteration)
- Write-optimized operations (append mode)
- Buffer-based operations for reduced copying
- Database statistics and space efficiency

**Key Operations Benchmarked:**

1. **Write Operations:**

   - Random insert with transaction put
   - Sequential insert (pre-sorted keys)
   - Cursor-based insert (reused cursor)
   - Bulk insert with ``putmulti()``
   - Append mode (for pre-sorted data)

2. **Read Operations:**

   - Random lookups
   - Per-transaction lookups (overhead comparison)
   - Buffer-based lookups (zero-copy)
   - Sequential enumeration (forward/reverse)

**Key Code Patterns:**

.. code-block:: python

   import zlmdb.lmdb as lmdb

   # Open with writemap for better write performance (Linux)
   env = lmdb.open(DB_PATH, map_size=MAP_SIZE, writemap=USE_SPARSE_FILES)

   # Bulk insert with putmulti (fastest for batch operations)
   with env.begin(write=True) as txn:
       txn.cursor().putmulti([(word, value) for word in words])

   # Append mode for pre-sorted data (even faster)
   with env.begin(write=True) as txn:
       for word in sorted_words:
           txn.put(word, value, append=True)

   # Buffer-based reads (zero-copy, no Python object allocation)
   with env.begin(buffers=True) as txn:
       for word in words:
           data = txn.get(word)  # Returns buffer, not bytes

**Running:**

.. code-block:: bash

   python examples/lmdb/dirtybench.py

   # Or using justfile:
   just test-examples-lmdb-dirtybench

**Typical Results:**

Example output on modern hardware::

                                      insert:  0.523s   350000/sec
                     enum (key, value) pairs:  0.045s  4000000/sec
             reverse enum (key, value) pairs:  0.048s  3800000/sec
                               rand lookup:  0.092s  1980000/sec
                       per txn rand lookup:  1.823s   100000/sec
                          rand lookup+hash:  0.112s  1630000/sec
                               insert (rand):  0.534s   340000/sec
                                insert (seq):  0.421s   430000/sec
                  insert (rand), reuse cursor:  0.312s   580000/sec
                  insert (seq), reuse cursor:  0.287s   630000/sec
                           insert, putmulti:  0.156s  1160000/sec
                                     append:  0.234s   770000/sec

**Learning Points:**

1. **putmulti is fastest** for bulk inserts (1M+ ops/sec)
2. **Reusing cursors** improves write performance significantly
3. **Sequential inserts** faster than random (better B+tree splits)
4. **Append mode** excellent for pre-sorted data
5. **Per-transaction overhead** matters: keep transactions open when doing multiple operations
6. **Buffer mode** reduces memory allocation overhead

nastybench.py: High-Volume Stress Testing
------------------------------------------

**Purpose:** Stress test LMDB with 1 million random keys to validate robustness and measure raw throughput.

**What it demonstrates:**

- Large-scale data handling (1M+ keys)
- Random key generation from ``/dev/urandom``
- Batch transaction strategy (10K writes per transaction)
- Async write modes for maximum throughput
- Random lookup performance on large datasets

**Key Code Patterns:**

.. code-block:: python

   import zlmdb.lmdb as lmdb

   # Generate 1M random keys
   urandom = open("/dev/urandom", "rb", 1048576).read
   keys = set()
   while len(keys) < MAX_KEYS:
       keys.add(urandom(16))

   # Open with async write modes for maximum throughput
   env = lmdb.open(DB_PATH,
                   map_size=1048576 * 1024,
                   metasync=False,  # Don't fsync metadata
                   sync=False,       # Don't fsync data
                   map_async=True)   # OS-managed writeback

   # Batch writes: 10K per transaction
   nextkey = iter(keys).__next__
   while run:
       with env.begin(write=True) as txn:
           try:
               for _ in range(10000):
                   txn.put(nextkey(), val)
           except StopIteration:
               run = False

   # Explicit sync at end
   env.sync(True)

   # Buffer-based random lookups
   with env.begin(buffers=True) as txn:
       while True:
           txn.get(nextkey())

**Running:**

.. code-block:: bash

   python examples/lmdb/nastybench.py

   # Or using justfile (with 30-second timeout):
   timeout 30 just test-examples-lmdb-nastybench

**Typical Results:**

Example output::

   make 1000000 keys in 2.34sec
   insert 1000000 keys in 4.21sec (237529/sec)
   random lookup 1000000 keys in 1.87sec (534759/sec)
   random lookup 1000000 buffers in 1.45sec (689655/sec)
   random lookup+hash 1000000 buffers in 1.92sec (520833/sec)
   seq read 1000000 buffers in 0.34sec (2941176/sec)

**Learning Points:**

1. **Batching transactions** essential for write throughput (10K ops/txn sweet spot)
2. **Async modes** sacrifice durability for speed (fine for benchmarks, careful in production)
3. **Random 16-byte keys** realistic for UUID-based schemas
4. **Sequential reads** 5-10x faster than random lookups
5. **Buffer mode** provides 20-30% speedup on reads

**Performance Note:**

This benchmark uses ``metasync=False`` and ``sync=False`` which provide maximum throughput
but risk data loss on system crash. For production, see :doc:`transactions` for durable
configuration options.

parabench.py: Parallel Read Performance
----------------------------------------

**Purpose:** Demonstrate LMDB's lock-free concurrent read performance with multiple processes.

**What it demonstrates:**

- Multi-process concurrent reads
- Lock-free reader scalability
- CPU affinity pinning (optional)
- Sustained read throughput measurement
- Real-world concurrent access patterns

**Key Code Patterns:**

.. code-block:: python

   import multiprocessing
   import zlmdb.lmdb as lmdb

   def run(idx):
       # Each process opens its own environment handle
       env = lmdb.open(DB_PATH, ...)

       # Continuous random lookups
       while True:
           with env.begin() as txn:
               for key in random_keys:
                   hash(txn.get(key))
               counter[idx] += len(random_keys)

   # Create N parallel processes
   nproc = 4
   counter = multiprocessing.Array('L', nproc)
   procs = [multiprocessing.Process(target=run, args=(i,))
            for i in range(nproc)]
   [p.start() for p in procs]

   # Monitor aggregate throughput
   while duration < 30:
       time.sleep(2)
       total = sum(counter)
       print("lookup %d keys in %.2fs (%d/sec)" % (total, elapsed, total/elapsed))

**Running:**

.. code-block:: bash

   # Default: 4 processes, 30 seconds
   python examples/lmdb/parabench.py

   # Custom: 8 processes, 60 seconds
   python examples/lmdb/parabench.py 8 60

   # Using justfile (with timeout):
   timeout 30 just test-examples-lmdb-parabench

**Arguments:**

- ``nproc`` (optional): Number of parallel processes (default: min(4, cpu_count()))
- ``duration`` (optional): Benchmark duration in seconds (default: 30)

**Typical Results:**

Example output on 4-core system::

   Using 4 parallel processes for 30 seconds
   make 4000000 keys in 8.23sec
   insert 4000000 keys in 16.45sec (243189/sec)
   lookup 2000000 keys in 2.01sec (995024/sec)
   lookup 4200000 keys in 4.03sec (1042183/sec)
   lookup 6400000 keys in 6.05sec (1057851/sec)
   ...
   ======================================================================
   FINAL RESULTS
   ======================================================================
   Duration:       30.02 seconds
   Total lookups:  15600000
   Throughput:     519654 lookups/sec
   Per process:    129913 lookups/sec
   ======================================================================

**Learning Points:**

1. **Linear read scaling** - LMDB readers don't block each other
2. **No read locks** - Each reader gets consistent snapshot
3. **Memory-mapped I/O** - Data shared across processes, not copied
4. **Per-process handles** - Each process opens its own environment
5. **Aggregate throughput** scales with CPU cores (up to memory/IO limits)

**CPU Affinity:**

The benchmark optionally uses CPU affinity pinning (if ``affinity`` module installed)
to reduce context switching and improve cache locality.

dirtybench-gdbm.py: GDBM Comparison Benchmark
----------------------------------------------

**Purpose:** Compare LMDB performance against Python's built-in GDBM database.

**What it demonstrates:**

- Side-by-side performance comparison
- GDBM API patterns vs LMDB
- Write and read throughput differences
- When to choose LMDB over GDBM

**Requirements:**

.. code-block:: bash

   # Install GDBM support (optional)
   # Debian/Ubuntu:
   apt-get install python3-gdbm

**Note:** This benchmark is optional. If GDBM is not available, the script exits gracefully.
Some Python distributions (like uv) deliberately exclude GDBM due to GPL licensing.

**Key Code Patterns:**

.. code-block:: python

   import gdbm

   # GDBM API (dict-like interface)
   env = gdbm.open(DB_PATH, 'c')

   # Write operation
   env[key] = value

   # Read operation
   value = env[key]

   # Iteration
   for key in env.keys():
       value = env[key]

**Running:**

.. code-block:: bash

   python examples/lmdb/dirtybench-gdbm.py

   # Or using justfile:
   just test-examples-lmdb-dirtybench-gdbm

**Typical Comparison:**

========================  ==============  ==============
Operation                 LMDB            GDBM
========================  ==============  ==============
Random Insert             350K ops/sec    45K ops/sec
Sequential Insert         580K ops/sec    48K ops/sec
Random Lookup             2M ops/sec      180K ops/sec
Sequential Read           4M ops/sec      200K ops/sec
Bulk Insert (putmulti)    1.2M ops/sec    N/A
========================  ==============  ==============

**When to Choose LMDB:**

- Need ACID transactions
- High read concurrency required
- Multi-process access patterns
- Large datasets (GB to TB)
- Performance critical
- Memory-mapped I/O benefits

**When GDBM Might Suffice:**

- Single-process, single-threaded access
- Small datasets (MB range)
- Simple key-value storage
- No transaction requirements
- GPL licensing acceptable

Running All Examples
--------------------

You can run all examples using the justfile recipes:

.. code-block:: bash

   # Individual examples
   just test-examples-lmdb-addressbook
   just test-examples-lmdb-dirtybench
   just test-examples-lmdb-nastybench
   just test-examples-lmdb-parabench
   just test-examples-lmdb-dirtybench-gdbm

   # Or run specific example directly
   python examples/lmdb/address-book.py

Common Patterns Across Examples
--------------------------------

**1. Environment Setup:**

All examples follow the pattern:

.. code-block:: python

   import zlmdb.lmdb as lmdb

   env = lmdb.open(path, map_size=..., **options)

**2. Transaction Context Managers:**

Safe transaction handling:

.. code-block:: python

   # Read transaction
   with env.begin() as txn:
       value = txn.get(key)

   # Write transaction
   with env.begin(write=True) as txn:
       txn.put(key, value)

**3. Cursor Iteration:**

Efficient traversal:

.. code-block:: python

   with env.begin() as txn:
       for key, value in txn.cursor():
           process(key, value)

**4. Cleanup:**

All benchmarks handle cleanup:

.. code-block:: python

   import atexit
   import shutil

   @atexit.register
   def cleanup():
       if env:
           env.close()
       if os.path.exists(DB_PATH):
           shutil.rmtree(DB_PATH)

See Also
--------

- :doc:`index` - LMDB API overview
- :doc:`quickstart` - Getting started guide
- :doc:`transactions` - Transaction patterns
- :doc:`cursors` - Cursor operations
- :doc:`performance` - Performance tuning
