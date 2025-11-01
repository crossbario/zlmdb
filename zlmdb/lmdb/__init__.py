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

def _reading_docs():
    """Return True if Sphinx is currently parsing this file."""
    return 'sphinx' in __import__('sys').modules

# CFFI-only mode (bundled with zlmdb)
from zlmdb.lmdb.cffi import *
from zlmdb.lmdb.cffi import open
from zlmdb.lmdb.cffi import __all__
from zlmdb.lmdb.cffi import __doc__
