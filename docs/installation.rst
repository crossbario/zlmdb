Installation
============

This guide covers how to install **zLMDB**.

Requirements
------------

zLMDB supports:

* Python 3.9+
* CPython and PyPy
* Linux, macOS, Windows

Installing from PyPI
--------------------

The recommended way to install zLMDB is from PyPI using pip:

.. code-block:: bash

    pip install zlmdb

This will install zLMDB with its core dependencies.

Installing with All Features
----------------------------

To install with all optional dependencies:

.. code-block:: bash

    pip install zlmdb[all]

Installing from Source
----------------------

To install from source:

.. code-block:: bash

    git clone https://github.com/crossbario/zlmdb.git
    cd zlmdb
    pip install -e .

Dependencies
------------

zLMDB depends on:

* `lmdb <https://lmdb.readthedocs.io/>`__ - The LMDB Python bindings
* `flatbuffers <https://google.github.io/flatbuffers/>`__ - For serialization
* `txaio <https://txaio.readthedocs.io/>`__ - For async framework abstraction

Verifying Installation
----------------------

To verify zLMDB is installed correctly:

.. code-block:: python

    import zlmdb
    print(zlmdb.__version__)
