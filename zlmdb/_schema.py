import six


class Registration(object):
    """

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
        """

        """
        self._slot_to_reg = {}
        self._name_to_reg = {}

    def open(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        from zlmdb._database import Database

        db = Database(*args, **kwargs)
        return db

    def register(self, slot, name, pmap):
        """

        :param slot:
        :param name:
        :param pmap:
        :return:
        """
        if slot in self._slot_to_reg:
            raise Exception('pmap slot "{}" already registered'.format(slot))
        if name in self._name_to_reg:
            raise Exception('pmap name "{}" already registered'.format(name))

        reg = Registration(slot, name, pmap)
        self._slot_to_reg[slot] = reg
        self._name_to_reg[name] = reg
        return pmap

    def unregister(self, key):
        """

        :param key:
        :return:
        """
        if type(key) == six.text_type:
            if key in self._name_to_reg:
                reg = self._name_to_reg[key]
                del self._slot_to_reg[reg.slot]
                del self._name_to_reg[reg.name]
            else:
                raise KeyError('no pmap registered for name "{}"'.format(key))
        elif type(key) in six.integer_types:
            if key in self._slot_to_reg:
                reg = self._slot_to_reg[key]
                del self._slot_to_reg[reg.slot]
                del self._name_to_reg[reg.name]
            else:
                raise KeyError('no pmap registered for slot "{}"'.format(key))

    def __getattr__(self, key):
        if type(key) == six.text_type:
            if key in self._name_to_reg:
                return self._name_to_reg[key]
            else:
                raise KeyError('no pmap registered for name "{}"'.format(key))
        elif type(key) in six.integer_types:
            if key in self._slot_to_reg:
                return self._slot_to_reg[key]
            else:
                raise KeyError('no pmap registered for slot "{}"'.format(key))
