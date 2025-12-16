WAMP Zero-Copy Data Plane
=========================

.. note::

   This document explains the architecture and design rationale for
   the FlatBuffers-based zero-copy data plane shared between zLMDB
   and Autobahn|Python.

Architecture Overview
---------------------

Both **zLMDB** and **Autobahn|Python** implement a shared architectural vision:

   A **schema-first, zero-copy, end-to-end data plane for WAMP**, using
   **FlatBuffers** as the single source of truth for data representation —
   across *storage* and *transport*, or *data-at-rest* and *data-in-transit*.

This design is intentional and spans multiple layers of the system.

Data Flow
---------

At a conceptual level, data flows through the system like this:

.. code-block:: text

   LMDB (data-at-rest)
      ↓ zero-copy
   FlatBuffers object graph
      ↓ zero-copy
   WAMP RPC / PubSub (data-in-transit)
      ↓ zero-copy
   WebSocket (or other WAMP transport)

Key properties:

* **FlatBuffers schemas are the single source of truth**
* The *same schema* is used for:

  * Persistent storage (zLMDB)
  * Network transport (Autobahn|Python)

* No intermediate serialization formats are introduced
* No JSON / MsgPack / Protobuf translation layers
* Memory layouts are shared as much as possible

Single Source of Truth
----------------------

Using FlatBuffers schemas for both storage (zLMDB) and transport
(Autobahn|Python) eliminates the "impedance mismatch" problem that
plagues most systems with separate persistence and messaging models.

Traditional systems often have:

* One data model for the database (SQL, ORM classes)
* Another for API/messaging (JSON schemas, Protobuf)
* Translation layers between them
* Version drift and compatibility issues

With the unified FlatBuffers approach:

* Schema changes propagate automatically
* No translation code to maintain
* Type safety from storage to wire
* Schema evolution rules apply consistently

Design Principles
-----------------

Schema-First Development
^^^^^^^^^^^^^^^^^^^^^^^^

FlatBuffers schemas define:

* Data structure and field types
* Evolution rules (field IDs, deprecation)
* Compatibility guarantees

Code generation is derived from schemas — not vice versa.

Reflection (``reflection.fbs`` / ``.bfbs``) enables:

* Dynamic schema introspection
* Runtime tooling and validation
* Schema-driven code generation

Zero-Copy by Design
^^^^^^^^^^^^^^^^^^^

The zero-copy property is achieved through:

1. **LMDB memory-mapping** — Data is accessed directly from disk-backed
   memory without copying into application buffers

2. **FlatBuffers in-place access** — Structured data can be read directly
   from the memory-mapped region without deserialization

3. **Direct transmission** — WAMP messages can be transmitted without
   re-encoding the payload

Goal: **Avoid deserialize → reserialize cycles**

This is especially important for:

* Large payloads (binary data, arrays)
* High-throughput scenarios
* Latency-sensitive applications

Unified Data Model
^^^^^^^^^^^^^^^^^^

The relationship between the projects:

* **zLMDB** — Focuses on *data-at-rest*

  * Memory-mapped LMDB storage
  * FlatBuffers serialization
  * ORM-style Python API

* **Autobahn|Python** — Focuses on *data-in-transit*

  * WAMP protocol implementation
  * WebSocket transport
  * FlatBuffers payload support

Both operate on the **same FlatBuffers data model**, enabling patterns like:

.. code-block:: python

   # Read a database record
   record = db.get(key)

   # Return it directly as a WAMP RPC result
   # (no serialization/deserialization needed)
   return record.flatbuffer_bytes()

Hermetic Tooling
^^^^^^^^^^^^^^^^

FlatBuffers is vendored to ensure:

* **Deterministic builds** — Same compiler version everywhere
* **Version consistency** — Schema and compiler always match
* **Reproducibility** — No external dependency drift

The ``flatc`` compiler is bundled inside wheels:

* Avoids system dependencies
* Avoids PATH issues
* Ensures schema/compiler compatibility
* Works identically on CPython and PyPy

Version synchronization is explicitly checked at runtime between
zLMDB and Autobahn|Python.

Use Cases
---------

High-Performance WAMP Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The zero-copy data plane enables WAMP applications that:

* Handle large payloads efficiently
* Minimize memory allocations
* Reduce CPU overhead from serialization
* Scale to high message rates

Persistent Pub/Sub
^^^^^^^^^^^^^^^^^^

Combine zLMDB storage with WAMP Pub/Sub:

* Store events durably in LMDB
* Replay events without re-serialization
* Event history queries return FlatBuffers directly

RPC with Database-Backed Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Implement RPC procedures that:

* Query zLMDB for data
* Return results as FlatBuffers
* No intermediate JSON/dict conversion

Schema-Driven Development
^^^^^^^^^^^^^^^^^^^^^^^^^

Use FlatBuffers schemas as the contract between:

* Database layer
* Application logic
* Network API
* Client applications

Changes to the schema automatically propagate through all layers.

Related Documentation
---------------------

* :doc:`vendoring-design-and-technology` — How native components are built
  and distributed
* `FlatBuffers Documentation <https://flatbuffers.dev/>`__
* `LMDB Documentation <http://www.lmdb.tech/doc/>`__
* `Autobahn|Python Documentation <https://autobahn.readthedocs.io/>`__
