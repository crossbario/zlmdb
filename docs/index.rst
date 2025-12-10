zLMDB Python/LMDB Database Library
==================================

|PyPI| |Python| |CI| |CD-wheels| |CD-wheels-arm64| |CD-wheels-docker| |Docs| |License| |Downloads|

.. |PyPI| image:: https://img.shields.io/pypi/v/zlmdb.svg
   :target: https://pypi.python.org/pypi/zlmdb
.. |Python| image:: https://img.shields.io/pypi/pyversions/zlmdb.svg
   :target: https://pypi.python.org/pypi/zlmdb
.. |CI| image:: https://github.com/crossbario/zlmdb/workflows/main/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Amain
.. |CD-wheels| image:: https://github.com/crossbario/zlmdb/workflows/wheels/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels
.. |CD-wheels-arm64| image:: https://github.com/crossbario/zlmdb/workflows/wheels-arm64/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels-arm64
.. |CD-wheels-docker| image:: https://github.com/crossbario/zlmdb/workflows/wheels-docker/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Awheels-docker
.. |Docs| image:: https://readthedocs.org/projects/zlmdb/badge/?version=latest
   :target: https://zlmdb.readthedocs.io/en/latest/
.. |License| image:: https://img.shields.io/pypi/l/zlmdb.svg
   :target: https://github.com/crossbario/zlmdb/blob/master/LICENSE
.. |Downloads| image:: https://img.shields.io/pypi/dm/zlmdb.svg
   :target: https://pypi.python.org/pypi/zlmdb

--------------

**zLMDB** is an object-relational in-memory database layer built on top of
`LMDB <http://www.intelsolution.in/blog/lmdb-lightning-memory-mapped-database-a-detailed-overview>`__,
the lightning memory-mapped database.

zLMDB provides:

* High-performance, ACID-compliant embedded database
* Object-relational mapping (ORM) layer for Python
* FlatBuffers-based serialization for efficient storage
* Support for both Twisted and asyncio async frameworks

Contents
--------

.. toctree::
   :maxdepth: 2

   overview
   installation
   getting-started
   programming-guide/index
   releases
   changelog
   contributing
   OVERVIEW.md
   ai/index

--------------

*Copyright (c) typedef int GmbH. Licensed under the* `MIT License <https://github.com/crossbario/zlmdb/blob/master/LICENSE>`__.
*WAMP, Autobahn, Crossbar.io and XBR are trademarks of typedef int GmbH (Germany).*
