###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import

from zlmdb._pmap import PersistentMap


class Slot(object):
    """
    LMDB database slot. A slot is defined just by the convention of using
    the first 2 bytes of keys in a LMDB database as the "slot index".

    The 2 bytes are interpreted as an uint16 in big endian byte order.
    """

    def __init__(self, slot, name, pmap):
        """

        :param slot:
        :param name:
        :param pmap:
        """
        self.slot = slot
        self.name = name
        self.pmap = pmap


class Schema(object):
    """
    ZLMDB database schema definition.
    """

    SLOT_DATA_EMPTY = 0
    """
    Database slot is empty (unused, not necessarily zero'ed, but uninitialized).
    """

    SLOT_DATA_METADATA = 1
    """
    FIXME.
    """

    SLOT_DATA_TYPE = 2
    """
    FIXME.
    """

    SLOT_DATA_SEQUENCE = 3
    """
    FIXME.
    """

    SLOT_DATA_TABLE = 4
    """
    Database slot contains a persistent map, for example a map of type OID to Pickle.
    """

    SLOT_DATA_INDEX = 5
    """
    FIXME.
    """

    SLOT_DATA_REPLICATION = 6
    """
    FIXME.
    """

    SLOT_DATA_MATERIALIZATION = 7
    """
    FIXME.
    """

    def __init__(self):
        self._index_to_slot = {}
        self._name_to_slot = {}

    def slot(self, slot_index, marshal=None, unmarshal=None, build=None, cast=None, compress=False):
        """
        Decorator for use on classes derived from zlmdb.PersistentMap. The decorator define slots
        in a LMDB database schema based on persistent maps, and slot configuration.

        :param slot_index:
        :param marshal:
        :param unmarshal:
        :param build:
        :param cast:
        :param compress:
        :return:
        """

        def decorate(o):
            assert isinstance(o, PersistentMap)
            name = o.__class__.__name__
            assert slot_index not in self._index_to_slot
            assert name not in self._name_to_slot
            o._zlmdb_slot = slot_index
            o._zlmdb_marshal = marshal
            o._zlmdb_unmarshal = unmarshal
            o._zlmdb_build = build
            o._zlmdb_cast = cast
            o._zlmdb_compress = compress
            _slot = Slot(slot_index, name, o)
            self._index_to_slot[slot_index] = _slot
            self._name_to_slot[name] = _slot
            return o

        return decorate
