Introduction to zLMDB
=====================

.. image:: https://img.shields.io/pypi/v/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: PyPI

.. image:: https://github.com/crossbario/zlmdb/workflows/main/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Amain
   :alt: Build

.. image:: https://readthedocs.org/projects/zlmdb/badge/?version=latest
    :target: https://zlmdb.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation

.. image:: https://github.com/crossbario/zlmdb/workflows/deploy/badge.svg
   :target: https://github.com/crossbario/zlmdb/actions?query=workflow%3Adeploy
   :alt: Deploy

Object-relational in-memory database layer based on LMDB:

* High-performance (see below)
* Supports multiple serializers (JSON, CBOR, Pickle, Flatbuffers)
* Supports export/import from/to Apache Arrow
* Support native Numpy arrays and Pandas data frames
* Automatic indexes
* Free software (MIT license)
