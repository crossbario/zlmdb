Deployment: Storage and Concurrency Topologies
==============================================

zLMDB uses LMDB, an embedded, memory-mapped database. Several processes can open
the same database at the same time: any number of readers run concurrently, and
write transactions are serialized.

Whether a deployment is supported depends on more than whether the processes can
reach the same files. The operating system and the filesystem must provide the
memory-mapping, locking and durability semantics LMDB relies on. This page says
which topologies are supported, which are not, and why.

.. contents::
   :local:
   :depth: 2

The rule
--------

**All processes that share a zLMDB database must run under one operating-system
kernel, on a filesystem that kernel owns.**

LMDB coordinates processes through its lock file, ``lock.mdb``, which every process
maps into memory (``mmap`` with ``MAP_SHARED``):

- The writer lock and the reader-table lock are process-shared, robust POSIX
  mutexes stored *inside* that mapping. A POSIX mutex is a futex, and futexes exist
  only within one kernel.
- Every process registers its read transactions in the reader table, which also
  lives in that mapping. Writers use it to decide which old pages are still in use.
- Every process marks itself as a live reader with an ``fcntl`` lock on the byte at
  offset = its process ID in ``lock.mdb``.

The data file, ``data.mdb``, is read through a memory map as well. All of this works
between processes of one kernel, which share one page cache. It does not extend
across kernels.

Requirements
------------

Within one kernel, processes sharing a database must also meet these requirements.

**A shared PID namespace.** Processes in different PID namespaces, for example in
different containers, can have the same process ID: every container's main process
is PID 1. Two such processes collide on LMDB's reader lock (the byte at offset = PID
in ``lock.mdb``), and the second cannot open the database. zLMDB then raises a
``RuntimeError`` that names this cause (#196). LMDB also records readers by PID in
its reader table, so a shared PID namespace protects correctness, not only
availability. Run the processes in one PID namespace, for example
``docker run --pid=host``, ``--pid=container:<name>``, or one Kubernetes pod with
``shareProcessNamespace: true``.

**One C library family.** The mutexes in ``lock.mdb`` are laid out by the C library
of the process that created the lock file. glibc and musl use different layouts of
the same size (40 bytes on x86-64), so LMDB's lock-format check cannot tell them
apart. In tests with zLMDB's bundled LMDB 0.9.36 and 1.0.2 on Linux x86-64, a process
built against the other C library **hung in its first write transaction and never
recovered**, even after the other process had exited. Do not share a database
between, for example, a Debian-based and an Alpine-based container. Treat it as
undefined behaviour: a hang was observed, corruption is not ruled out.

**The same files.** In containers, the database directory must be a bind mount or a
volume shared by the containers, not a directory inside the container's own image
layer, where each container has its own copy.

**One environment per process, and not across ``fork()``.** A process must not open
the same database twice; ``zlmdb.Database`` refuses this. An open database must not
be used in a child process after ``fork()``: the child must open it again.

**Durable storage.** LMDB's crash safety relies on ``fsync`` ordering: data pages
first, then the meta page. Every layer below the filesystem must honour flushes.

Topologies
----------

Several processes on one host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Supported.** This is LMDB's normal multi-process model: one kernel, one page
cache, local ``fcntl`` locks. Readers run concurrently; writers are serialized.

Several containers on one host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Supported with a shared PID namespace**, and with the other requirements above:
the same C library family, and a shared bind mount or volume.

Containers share the host kernel, so the mutexes and the memory map work across
container boundaries. Separate mount, network or IPC namespaces do not matter. A
separate *PID* namespace does: see the requirements above.

.. note::

    With Docker Desktop on macOS or Windows, containers run inside one Linux virtual
    machine. Containers of that machine share its kernel, so sharing a database
    between them is the case above. A process on the macOS or Windows host and a
    process in a container are under two different kernels: that is not supported.

One host, ext4 (or another local filesystem) on a network block device
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Supported.** An iSCSI LUN (or another network block device) holding an ext4
filesystem that one host mounts read-write is local storage to that kernel. Several
processes on that host can share a database on it.

The block device's remote location does not matter to LMDB; the flush path does.
The filesystem's flushes must reach the device; the iSCSI target must not
acknowledge them from a volatile write-back cache; and the backing volume must honour
synchronous writes (for a ZFS zvol: not ``sync=disabled``). Otherwise a power loss on
the storage side can lose committed transactions or corrupt the database.

One host, NFS
^^^^^^^^^^^^^

**Not supported by LMDB, though likely to work.** All processes share one NFS
client's page cache, so the mapping and the mutexes are coherent, and Linux NFS
supports ``fcntl`` locks. But LMDB's documentation says: "Do not use LMDB databases
on remote filesystems, even between processes on the same host." The remaining
risks concern locks and recovery: an NFSv4 lease that expires, or locks that are not
reclaimed after a server restart, can silently drop the reader locks. This has not
been tested.

Several virtual machines on one host, sharing a host directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Not supported.** Each virtual machine has its own kernel. A directory shared into
the guests (virtiofs, 9p or similar) does not give them a common page cache or
common futexes, so LMDB's locking and memory protocol does not hold between them.

Several kernels mounting one ext4 filesystem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Not supported**, independently of LMDB. ext4 is not a cluster filesystem: mounting
one filesystem read-write from several kernels (virtual machines or hosts sharing a
LUN) corrupts the filesystem's metadata. That the device is an iSCSI LUN does not
change this.

Several hosts sharing a database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Not supported**, on any shared storage, even a fully POSIX-compliant network
filesystem. POSIX promises shared memory mappings and process-shared mutexes only
between processes of one machine. Each host has its own page cache of ``lock.mdb``,
so its own copy of the mutexes and the reader table: two hosts can hold the "same"
writer lock at once. Network filesystems such as NFS guarantee close-to-open
consistency, not a coherent memory map across clients.

Summary
-------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Topology
     - Status
     - Main consideration
   * - Several processes, one host
     - Supported
     - LMDB's normal model
   * - Several containers, one host
     - Supported with a shared PID namespace
     - PID namespace, C library family, shared bind mount or volume
   * - One host, local filesystem on a network block device (e.g. ext4 on iSCSI)
     - Supported
     - Flushes must reach stable storage
   * - One host, NFS
     - Not supported by LMDB; likely to work
     - Lock leases and recovery
   * - Several virtual machines, shared host directory
     - Not supported
     - Separate kernels
   * - Several kernels mounting one ext4 filesystem
     - Not supported
     - ext4 is not a cluster filesystem
   * - Several hosts, shared storage
     - Not supported
     - Separate kernels; no coherent shared memory

Whether the files are physically shared is not the question. The whole storage and
synchronization stack must preserve the assumptions LMDB's correctness depends on.

Appendix: beyond one kernel
---------------------------

This appendix discusses what it would take to run LMDB across kernels. None of it is
implemented in zLMDB; it explains why the boundary above lies where it does.

Is cross-kernel LMDB impossible?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No. LMDB's concurrency model needs no database server and no distributed
transaction coordinator. But its implementation relies on operating-system
mechanisms whose semantics stop at the kernel boundary. Running it across kernels
would mean providing equivalent guarantees by other means, changing LMDB, or
building a suitable shared-memory abstraction.

The difficulty is not only a mutex. LMDB must also ensure that readers see
consistent snapshots, that writers publish committed transactions correctly, and
that pages are not reused while a reader may still read them.

Shared physical memory between virtual machines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Suppose several virtual machines on one physical machine can map the same physical
memory. That alone is not enough. A correct implementation would also need:

1. **Visibility:** changes made by one machine become visible to the others under
   well-defined memory-ordering rules.
2. **Atomic operations** that are atomic across all participating machines.
3. **Synchronization** that works although each kernel has its own futex wait queues.
4. **Transaction visibility:** readers see committed transactions and consistent
   snapshots.
5. **Reader registration:** writers can reliably tell which readers still use older
   transaction versions.
6. **Page reclamation:** pages are not reused while any reader may still access them.
7. **Crash recovery:** a crashed machine leaves neither a corrupt database nor a
   permanently blocked one.
8. **Durability:** committed changes survive the failures LMDB's guarantees cover.

A spinlock in shared memory could provide basic mutual exclusion, if the hardware
and the hypervisor guarantee the required atomicity and ordering. It would not, by
itself, implement LMDB's synchronization protocol.

Coherent distributed shared memory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Distributed shared memory provides a shared-memory abstraction across separate
machines or memory domains, through hardware coherence, software-managed coherence,
explicit remote-memory operations, or a mix. The question for LMDB is whether that
abstraction behaves enough like the shared memory LMDB expects.

Cache coherence helps: participants see consistent values of individual memory
locations. But it does not make a group of updates visible atomically, and it does
not implement transaction isolation. Seeing a new value in a lock word does not mean
that all related page updates are visible yet, in the right order.

An implementation suitable for LMDB would need to provide, or let LMDB implement:

- **Memory visibility and ordering** between page updates, metadata updates and the
  publication of a commit: no reader may see a transaction as committed while seeing
  database state inconsistent with it.
- **Atomic synchronization** for writer serialization, reader registration and
  shared metadata, atomic across all participants, not only within one kernel or
  one coherence domain.
- **Reader registration** visible to writers, without concluding that a reader has
  finished merely because it is temporarily unreachable.
- **Safe page reclamation:** LMDB updates copy-on-write and reuses pages no longer
  needed. A page may be reused only when no active reader can still reference its old
  version. That needs a protocol across all participants, not merely a distributed
  mutex around writes.
- **Failure handling** that distinguishes a participant that has terminated from one
  that is unreachable. Reclaiming a page still used by a live but partitioned reader
  corrupts data. A failed writer must not allow conflicting writers or expose an
  incomplete transaction.
- **Durability and recovery** across failures between writing pages, publishing
  metadata and making the commit durable.
- **Coordinated map growth:** changes of the map size, so that no participant keeps
  working with an incompatible view of the environment.

None of these is necessarily a research problem on its own. The challenge is
meeting them together, correctly, efficiently and recoverably.

RDMA
^^^^

RDMA offers building blocks for such an implementation: remote reads and writes,
remote atomic compare-and-swap and fetch-and-add, completion notifications, and
access to registered remote memory without involving the remote CPU in every
operation.

But RDMA is not coherent distributed shared memory. Remote operations and local CPU
accesses have different ordering and visibility rules. A design based on RDMA needs
an explicit synchronization protocol, and hardware guarantees that support it. One
direction would keep database pages in remotely accessible memory, coordinate
writers and publish commits through remote atomics, and have readers register their
transaction IDs so that their pages are not reclaimed. That is plausible for a
specialized implementation, but it changes LMDB's assumptions about memory access
and synchronization substantially. Placing ``data.mdb`` in registered memory and
letting remote hosts access it would not be enough.

A distributed transaction coordinator?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not necessarily. LMDB already has a single writer, and a distributed implementation
could keep that, coordinating through shared atomic state or a purpose-built lock
protocol. But removing a coordinator does not remove the need for coordination: a
single active writer, correct publication of commits, consistent reader snapshots,
safe page reclamation, recovery from failed participants, and defined behaviour
under network partitions.

Conclusion
^^^^^^^^^^

A theoretically possible architecture is not the same as a topology the existing
LMDB implementation supports. For zLMDB:

- **One kernel:** LMDB's normal multi-process model applies, with the requirements
  on this page.
- **Several kernels:** shared files or shared storage do not make it correct.
- **Cross-kernel shared memory or RDMA:** possibly viable with a deliberately
  designed synchronization and memory-access architecture that preserves all of
  LMDB's invariants.

Until an implementation provides and validates those guarantees, cross-kernel and
shared-storage deployments are unsupported.
