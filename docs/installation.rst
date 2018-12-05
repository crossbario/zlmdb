.. highlight:: shell

============
Installation
============


Stable release
--------------

To install ZLMDB, run this command in your terminal:

.. code-block:: console

    $ pip install zlmdb

This is the preferred method to install ZLMDB, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for ZLMDB can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/crossbario/zlmdb

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/crossbario/zlmdb/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/crossbario/zlmdb
.. _tarball: https://github.com/crossbario/zlmdb/tarball/master


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


flatc
-----

To build the flatbuffers compiler (`flatc`) from sources:

.. code:: console

    sudo apt install cmake

    git clone https://github.com/google/flatbuffers.git
    cd flatbuffers

    git checkout master
    git checkout v1.9.0

    cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release
    make

To check:

.. code:: console

    oberstet@crossbar1:~/scm/3rdparty/flatbuffers$ ./flatc --version
    flatc version 1.9.0 (Sep 20 2018 16:29:50)
