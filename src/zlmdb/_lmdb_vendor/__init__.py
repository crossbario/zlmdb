# Copyright 2013-2025 The py-lmdb authors, all rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted only as authorized by the OpenLDAP
# Public License.
#
# A copy of this license is available in the file LICENSE in the
# top-level directory of the distribution or, alternatively, at
# <http://www.OpenLDAP.org/license.html>.
#
# OpenLDAP is a registered trademark of the OpenLDAP Foundation.
#
# Individual files and/or contributed packages may be copyright by
# other parties and/or subject to additional restrictions.
#
# This work also contains materials derived from public sources.
#
# Additional information about OpenLDAP can be obtained at
# <http://www.openldap.org/>.

"""
Python wrapper for OpenLDAP's "Lightning" MDB database.

Please see https://lmdb.readthedocs.io/
"""

import os
import sys

def _reading_docs():
    # Hack: disable speedups while testing or reading docstrings. Don't check
    # for basename for embedded python - variable 'argv' does not exists there or is empty.
    if os.environ.get('READTHEDOCS'):
        return True

    if not(hasattr(sys, 'argv')) or not sys.argv:
        return False

    basename = os.path.basename(sys.argv[0])
    return any(x in basename for x in ('sphinx-build', 'pydoc'))

# zlmdb fork: CFFI-only. Unlike upstream py-lmdb, this fork never ships or
# imports the CPython C-extension backend (cpython.c / CPyExt). This is a
# deliberate, load-bearing invariant: it guarantees first-class PyPy support
# and clean, modern binary wheels (x86-64, ARM64, ...). The upstream
# LMDB_FORCE_CFFI / LMDB_FORCE_CPYTHON environment switches are therefore not
# honored — there is only ever the CFFI backend.
from zlmdb._lmdb_vendor.cffi import *
from zlmdb._lmdb_vendor.cffi import open
from zlmdb._lmdb_vendor.cffi import __all__
from zlmdb._lmdb_vendor.cffi import __doc__

# Upstream py-lmdb version this fork was last synced from. Bump this whenever
# re-forking against a newer py-lmdb release (see zlmdb issue #111).
__version__ = '2.2.1'
__forked_from__ = 'py-lmdb 2.2.1'
