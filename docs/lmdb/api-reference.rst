LMDB API Reference
==================

.. note::
   **Status:** This page is under development.

Complete API reference for the low-level LMDB API (``zlmdb.lmdb``).

Overview
--------

This reference documents all classes, methods, and functions in the ``zlmdb.lmdb`` module.

Coming Soon
-----------

This page will provide detailed API documentation for:

1. **Module Functions**
   - ``lmdb.open()`` - Open an LMDB environment
   - ``lmdb.version()`` - Get LMDB library version

2. **Environment Class**
   - Constructor parameters
   - ``begin()`` - Start a transaction
   - ``open_db()`` - Open/create a database
   - ``close()`` - Close the environment
   - ``sync()`` - Flush buffers to disk
   - ``stat()`` - Get environment statistics
   - ``info()`` - Get environment information
   - ``copy()`` - Backup operations

3. **Transaction Class**
   - ``get()`` - Retrieve a value
   - ``put()`` - Store a value
   - ``delete()`` - Remove a key
   - ``cursor()`` - Open a cursor
   - ``commit()`` - Commit changes
   - ``abort()`` - Discard changes
   - ``drop()`` - Clear database

4. **Cursor Class**
   - Navigation methods (``first()``, ``last()``, ``next()``, ``prev()``)
   - Positioning methods (``set_key()``, ``set_range()``)
   - Data access (``item()``, ``key()``, ``value()``)
   - Modification methods (``put()``, ``delete()``)
   - Iteration support

5. **Database Handle**
   - Database flags
   - Statistics methods

6. **Exceptions**
   - ``Error`` - Base exception
   - ``KeyNotFoundError``
   - ``MapFullError``
   - Other LMDB errors

For now, see the main :doc:`../reference` for auto-generated API documentation.

See Also
--------

- :doc:`index` - LMDB API overview
- :doc:`quickstart` - Getting started
- `py-lmdb documentation <https://lmdb.readthedocs.io/>`_ - Compatible API reference
