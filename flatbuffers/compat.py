# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" A tiny version of `six` to help with backwards compability. Also includes
 compatibility helpers for numpy. """

import struct
import sys

PY2 = sys.version_info[0] == 2
PY26 = sys.version_info[0:2] == (2, 6)
PY27 = sys.version_info[0:2] == (2, 7)
PY275 = sys.version_info[0:3] >= (2, 7, 5)
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

if PY3:
    import importlib.machinery
    string_types = (str,)
    binary_types = (bytes,bytearray)
    range_func = range
    memoryview_type = memoryview
    struct_bool_decl = "?"
else:
    import imp
    string_types = (unicode,)
    if PY26 or PY27:
        binary_types = (str,bytearray)
    else:
        binary_types = (str,)
    range_func = xrange
    if PY26 or (PY27 and not PY275):
        memoryview_type = buffer
        struct_bool_decl = "<b"
    else:
        memoryview_type = memoryview
        struct_bool_decl = "?"

# Helper functions to facilitate making numpy optional instead of required

class NumpyCompat:

    class datetime64:
        def __init__(self, time, unit='ns'):
            assert isinstance(time, int)
            assert unit == 'ns'
            self._value = time

        def __int__(self):
            return self._value

        def __add__(self, other):
            self._value += int(other)
            return self

        def __eq__(self, other):
            return self._value == int(other)

        def __lt__(self, other):
            return self._value < int(other)

        def __gt__(self, other):
            return self._value > int(other)

        def __hash__(self):
            return hash(self._value)

        def tobytes(self):
            return struct.pack('<q', self._value)

    @classmethod
    def frombuffer(cls, buffer, dtype='datetime64[ns]'):
        assert dtype == 'datetime64[ns]'
        ret = []
        for dateint in struct.unpack('<q', buffer):
            ret.append(cls.datetime64(dateint))
        return ret

    class timedelta64:
        def __init__(self, time, unit):
            assert isinstance(time, int)
            assert unit == 's'
            self._value = time * 1000000000

        def __int__(self):
            return self._value

        def __add__(self, other):
            return other + self._value


def import_numpy():
    """
    Returns the numpy module if it exists on the system,
    otherwise returns None.
    """
    if PY3:
        numpy_exists = (
            importlib.machinery.PathFinder.find_spec('numpy') is not None)
    else:
        try:
            imp.find_module('numpy')
            numpy_exists = True
        except ImportError:
            numpy_exists = False

    if numpy_exists:
        # We do this outside of try/except block in case numpy exists
        # but is not installed correctly. We do not want to catch an
        # incorrect installation which would manifest as an
        # ImportError.
        import numpy as np
    else:
        np = NumpyCompat

    return np


class NumpyRequiredForThisFeature(RuntimeError):
    """
    Error raised when user tries to use a feature that
    requires numpy without having numpy installed.
    """
    pass


# NOTE: Future Jython support may require code here (look at `six`).
