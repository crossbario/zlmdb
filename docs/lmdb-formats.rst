LMDB Formats (0.9 and 1.0)
==========================

zLMDB bundles **two LMDB engines**, and every zLMDB wheel contains both:

.. list-table::
   :header-rows: 1

   * - ``lib_version``
     - LMDB release line
     - on-disk data format
     - readable by
   * - ``"1.0"``
     - LMDB 1.0.x (bundled: 1.0.2)
     - v3
     - zLMDB 26.10.1 and later, LMDB 1.0 tools, py-lmdb 3.0 and later
   * - ``"0.9"``
     - LMDB 0.9.x (bundled: 0.9.36)
     - v1
     - every zLMDB version, LMDB 0.9 tools, every py-lmdb version

The two formats are not compatible: an LMDB 0.9 engine cannot open a 1.0 format
file, and the other way round. zLMDB picks the right engine for each database
file automatically.

Choosing the format: ``zlmdb.Database(lib_version=...)``
--------------------------------------------------------

.. code-block:: python

    import zlmdb

    # a new database: created in LMDB 1.0 format
    db = zlmdb.Database("/data/mydb")

    # a new database in LMDB 0.9 format, e.g. for older tools
    db = zlmdb.Database("/data/legacy", lib_version="0.9")

    # the format in use
    print(db.lib_version)       # "1.0" or "0.9"

``lib_version`` is ``None`` (not given), ``"1.0"`` or ``"0.9"``:

* **A new database** is created in ``"1.0"`` format unless ``lib_version="0.9"``
  is given.
* **An existing database** opens in its own format when ``lib_version`` is not
  given. zLMDB reads the format from the data file; it never converts a file.
* **An explicit** ``lib_version`` **that does not match an existing database**
  raises :class:`ValueError`, naming the path, the file's format and the
  requested one. Use this when your code depends on a specific format.
* Any other value (for example ``"1"``, ``1`` or ``"2.0"``) raises
  :class:`ValueError`.

.. note::

    **Changed in 26.10.1:** new databases are created in LMDB 1.0 format. Before,
    zLMDB created them in LMDB 0.9 format. Existing databases are not affected:
    they keep their format and open as before. If a new database must stay
    readable by older zLMDB versions or LMDB 0.9 tools, pass ``lib_version="0.9"``.

``Database.stats()`` reports the format as ``"lib_version"`` and the LMDB library
servicing the database as ``"lmdb_version"`` (for example ``"1.0.2"``).

The low-level API
-----------------

The low-level API, ``zlmdb.lmdb`` (the bundled py-lmdb binding), has the same
choice with py-lmdb's own convention: ``lmdb.open(path, lib_version=1)`` for LMDB
1.0, ``lib_version=0`` for LMDB 0.9. Unlike ``zlmdb.Database``, it creates new
environments in LMDB 0.9 format by default, as py-lmdb does, unless the
environment variable ``LMDB_DEFAULT_LIB_VERSION`` names another engine.
``Environment.lib_version()`` returns the engine's ``(major, minor, patch)``.

Inspecting a database: ``zlmdb info``
-------------------------------------

.. code-block:: console

    $ zlmdb info /data/mydb
    ...
    lib_version: 1.0
    lmdb_version: 1.0.2
    ...

``zlmdb info DBPATH`` opens the database read-only and prints every key of
``Database.stats()``. It never creates a database. With
``--lib-version 1.0`` or ``--lib-version 0.9`` it also checks the format.

Exit codes: ``0`` if the database was opened (and has the required format),
``1`` if there is no database at ``DBPATH`` or it has another format than
``--lib-version``, ``2`` for an invalid command line.

Converting a database
---------------------

zLMDB never converts a database by itself. To move a database created with
``zlmdb.Database`` to the other format, copy it into a new file. zLMDB stores all
its tables in LMDB's main database (each table is a key prefix), so copying the
main database copies everything:

.. code-block:: python

    from zlmdb import lmdb

    def convert(src: str, dst: str, lib_version: int = 1) -> None:
        """Copy the zLMDB database at src into a new database at dst.

        lib_version: 1 for LMDB 1.0 format, 0 for LMDB 0.9 format.
        """
        src_env = lmdb.open(src, readonly=True)  # opens in its own format
        dst_env = lmdb.open(dst, lib_version=lib_version, map_size=src_env.info()["map_size"])
        with src_env.begin() as rtxn, dst_env.begin(write=True) as wtxn:
            for key, value in rtxn.cursor():
                wtxn.put(key, value, append=True)  # keys arrive sorted
        dst_env.close()
        src_env.close()

Stop all writers of the source database first, check the result with
``zlmdb info``, and keep the source until the new database is in use.

This recipe covers databases created with ``zlmdb.Database``. An environment
created with the low-level API that uses **named databases** (``max_dbs`` and
``open_db``) needs each named database opened and copied as well, with the same
flags (for example ``dupsort``).
