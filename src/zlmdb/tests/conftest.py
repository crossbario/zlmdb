# conftest.py - pytest configuration for zlmdb tests
#
# This file is loaded by pytest before any test collection happens.
# It ensures txaio framework is selected before any zlmdb imports,
# which is required because zlmdb uses txaio for logging internally.

import txaio

txaio.use_twisted()
