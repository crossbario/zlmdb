# Copyright 2013-2025 The py-lmdb authors, all rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted only as authorized by the OpenLDAP
# Public License.
#
# A copy of this license is available in the file LICENSE in the
# top-level directory of the distribution or, alternatively, at
# <http://www.OpenLDAP.org/license.html>.
#
# OpenLDAP is a registered trademark of the OpenLDAP Foundation.
#
# Individual files and/or contributed packages may be copyright by
# other parties and/or subject to additional restrictions.
#
# This work also contains materials derived from public sources.
#
# Additional information about OpenLDAP can be obtained at
# <http://www.openldap.org/>.

"""
Parallel LMDB benchmark - tests concurrent read performance.

Usage:
    python parabench.py [nproc] [duration]

Arguments:
    nproc    - Number of parallel processes (default: min(4, cpu_count()))
    duration - Benchmark duration in seconds (default: 30)

Examples:
    python parabench.py           # 4 processes, 30 seconds
    python parabench.py 8         # 8 processes, 30 seconds
    python parabench.py 8 60      # 8 processes, 60 seconds
"""

# Roughly approximates some of Symas microbenchmark.

import multiprocessing
import os
import random
import shutil
import sys
import tempfile
import time

try:
    import affinity
except:
    affinity = False
import zlmdb.lmdb as lmdb


USE_SPARSE_FILES = sys.platform != "darwin"
DB_PATH = "/ram/dbtest"
MAX_KEYS = int(4e6)

if os.path.exists("/ram"):
    DB_PATH = "/ram/dbtest"
else:
    DB_PATH = tempfile.mktemp(prefix="parabench")


def open_env():
    return lmdb.open(
        DB_PATH,
        map_size=1048576 * 1024,
        metasync=False,
        sync=False,
        map_async=True,
        writemap=USE_SPARSE_FILES,
    )


def make_keys():
    t0 = time.time()
    urandom = open("/dev/urandom", "rb", 1048576).read

    keys = set()
    while len(keys) < MAX_KEYS:
        for _ in range(min(1000, MAX_KEYS - len(keys))):
            keys.add(urandom(16))

    print("make %d keys in %.2fsec" % (len(keys), time.time() - t0))
    keys = list(keys)

    nextkey = iter(keys).__next__
    run = True
    val = b" " * 100
    env = open_env()
    while run:
        with env.begin(write=True) as txn:
            try:
                for _ in range(10000):
                    txn.put(nextkey(), val)
            except StopIteration:
                run = False

    d = time.time() - t0
    env.sync(True)
    env.close()
    print("insert %d keys in %.2fsec (%d/sec)" % (len(keys), d, len(keys) / d))


# Global variables that will be initialized in main and shared with workers
keys = None
arr = None


def run(idx):
    """Worker function that runs in child processes."""
    if affinity:
        affinity.set_process_affinity_mask(os.getpid(), 1 << idx)

    env = open_env()
    k = list(keys)
    random.shuffle(k)
    k = k[:1000]

    while 1:
        with env.begin() as txn:
            nextkey = iter(k).__next__
            try:
                while 1:
                    hash(txn.get(nextkey()))
            except StopIteration:
                pass
            arr[idx] += len(k)


def main():
    """Main function - must be called from if __name__ == '__main__' block."""
    global keys, arr

    # Handle drop argument
    if "drop" in sys.argv and os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)

    # Create database if it doesn't exist
    if not os.path.exists(DB_PATH):
        make_keys()

    # Load keys from database
    env = open_env()
    with env.begin() as txn:
        keys = list(txn.cursor().iternext(values=False))
    env.close()

    # Parse arguments
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else min(4, multiprocessing.cpu_count())
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30  # Default 30 seconds
    print(f"Using {nproc} parallel processes for {duration} seconds")

    # Create shared array for results
    arr = multiprocessing.Array("L", range(nproc))
    for x in range(nproc):
        arr[x] = 0

    # Start worker processes
    procs = [multiprocessing.Process(target=run, args=(x,)) for x in range(nproc)]
    [p.start() for p in procs]

    t0 = time.time()
    try:
        while True:
            time.sleep(2)
            d = time.time() - t0
            if d >= duration:
                break
            lk = sum(arr)
            print("lookup %d keys in %.2fsec (%d/sec)" % (lk, d, lk / d))
    finally:
        # Cleanup: terminate all processes
        print("\nStopping benchmark...")
        for p in procs:
            p.terminate()
        for p in procs:
            p.join(timeout=1)

        # Print final statistics
        d = time.time() - t0
        lk = sum(arr)
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)
        print("Duration:       %.2f seconds" % d)
        print("Total lookups:  %d" % lk)
        print("Throughput:     %d lookups/sec" % (lk / d))
        print("Per process:    %d lookups/sec" % ((lk / d) / nproc))
        print("=" * 70)


if __name__ == "__main__":
    # Use 'fork' start method for this benchmark as it relies on shared memory
    # and global variable inheritance. Python 3.14+ defaults to 'forkserver' on Linux.
    # See: https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    multiprocessing.set_start_method("fork")
    main()
