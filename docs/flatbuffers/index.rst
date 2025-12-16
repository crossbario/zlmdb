FlatBuffers Integration
=======================

zLMDB integrates `FlatBuffers <https://flatbuffers.dev/>`__ as a core component
for high-performance, zero-copy data serialization. This section documents
the architecture, design decisions, and technical implementation details.

.. toctree::
   :maxdepth: 2

   wamp-zerocopy-dataplane
   vendoring-design-and-technology

Overview
--------

FlatBuffers is central to zLMDB's design, not incidental. The key insight is:

   **FlatBuffers schemas serve as the single source of truth for data
   representation — across both storage (data-at-rest) and transport
   (data-in-transit).**

This enables a unified data model where:

* **zLMDB** handles persistent storage with memory-mapped access
* **Autobahn|Python** handles WAMP messaging and transport
* Both operate on the **same FlatBuffers data model**

The result is a schema-first, zero-copy, end-to-end data plane for WAMP
applications.

Why FlatBuffers?
----------------

FlatBuffers was chosen for several key properties:

1. **Zero-copy access** — Read structured data directly from memory without
   deserialization overhead

2. **Schema evolution** — Forward and backward compatibility without breaking
   existing data

3. **Cross-language support** — Same schema works in Python, C++, JavaScript,
   and other languages

4. **Memory efficiency** — No intermediate representation; data is accessed
   in-place

5. **Reflection support** — Runtime schema introspection via ``.bfbs`` files
   enables dynamic tooling

Documentation Pages
-------------------

:doc:`wamp-zerocopy-dataplane`
   Architecture and design of the FlatBuffers-based zero-copy data plane
   for WAMP, explaining how data flows from storage through transport
   without serialization overhead.

:doc:`vendoring-design-and-technology`
   Technical details on native binaries, manylinux compliance, ISA
   compatibility, and PyPy support — explaining *how* and *why* FlatBuffers
   and flatc are bundled in Python wheels.
