ZLMDB
=====

.. image:: https://img.shields.io/pypi/v/zlmdb.svg
    :target: https://pypi.python.org/pypi/zlmdb
    :alt: PyPI

.. image:: https://readthedocs.org/projects/zlmdb/badge/?version=latest
    :target: https://zlmdb.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation

.. image:: https://img.shields.io/travis/crossbario/zlmdb.svg
    :target: https://travis-ci.org/crossbario/zlmdb
    :alt: TravisCI

.. image:: https://codecov.io/gh/crossbario/zlmdb/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/crossbario/zlmdb
    :alt: Coverage

Object-relational in-memory database layer based on LMDB:

* High-performance (see below)
* Supports multiple serializers (JSON, CBOR, Pickle, Flatbuffers)
* Supports export/import from/to Apache Arrow
* Support native Numpy arrays and Pandas data frames
* Automatic indexes
* Free software (MIT license)


Apache Arrow
------------

https://arrow.apache.org/install/


.. code:: console

    sudo apt install -y -V apt-transport-https
    sudo apt install -y -V lsb-release
    cat <<APT_LINE | sudo tee /etc/apt/sources.list.d/red-data-tools.list
    deb https://packages.red-data-tools.org/ubuntu/ $(lsb_release --codename --short) universe
    deb-src https://packages.red-data-tools.org/ubuntu/ $(lsb_release --codename --short) universe
    APT_LINE
    sudo apt update --allow-insecure-repositories || sudo apt update
    sudo apt install -y -V --allow-unauthenticated red-data-tools-keyring
    sudo apt update

.. code:: console

    sudo apt install -y -V libarrow-dev         # For C++
    sudo apt install -y -V libparquet-dev       # For Apache Parquet C++

    sudo apt install -y -V libarrow-glib-dev    # For GLib (C)
    sudo apt install -y -V libparquet-glib-dev  # For Parquet GLib (C)

.. code:: console

    pip install -r requirements-test.txt
