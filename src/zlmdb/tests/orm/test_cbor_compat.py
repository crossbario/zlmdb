###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) typedef int GmbH
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
"""
CBOR at rest is identical on CPython and PyPy (#177).

zlmdb's CBOR tables store ``cbor2.dumps(marshal(value))``. CPython uses cbor2 6.x (Rust),
PyPy cbor2 5.9.0 (pure Python, the last release without the Rust extension). A database
written on one interpreter must read the same on the other, so both cbor2 lines must encode
the plain types zlmdb stores to identical bytes, and decode each other's bytes to equal
values.

``cbor_vectors.json`` holds the CBOR bytes of ``CORPUS``, as produced by cbor2 6.x (zlib
compressed and base64 encoded, to keep the long values small in the repository). This test
runs on every interpreter, so on PyPy it checks cbor2 5.9.0 against bytes cbor2 6.x wrote.
Regenerate (only when ``CORPUS`` changes, on CPython with cbor2 6.x):

    python src/zlmdb/tests/orm/test_cbor_compat.py
"""

import base64
import json
import os
import platform
import uuid
import zlib
from importlib.metadata import version

import cbor2
import pytest

import zlmdb

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory  # type:ignore

VECTORS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cbor_vectors.json")

# The plain types a marshal() of a zlmdb / cfxdb object produces: str-keyed maps, lists,
# str (incl. non-ASCII), bytes (e.g. UUIDs, hashes, keys), ints across all CBOR length
# classes and beyond 64 bits (bignums), floats, bools and None, nested.
CORPUS = {
    "none": None,
    "true": True,
    "false": False,
    "int_0": 0,
    "int_small": 23,
    "int_1byte": 24,
    "int_2byte": 1000,
    "int_4byte": 2**31 - 1,
    "int_8byte": 2**63 - 1,
    "int_uint64_max": 2**64 - 1,
    "int_neg": -1,
    "int_neg_8byte": -(2**63),
    "int_bignum": 2**64,
    "int_neg_bignum": -(2**64) - 1,
    "float_zero": 0.0,
    "float_half": 0.5,
    "float_pi": 3.141592653589793,
    "float_tiny": 5e-324,
    "float_huge": 1.7976931348623157e308,
    "float_neg": -273.15,
    "str_empty": "",
    "str_ascii": "com.example.procedure",
    "str_unicode": "Grüße, 世界 🚀",
    "str_long": "x" * 70000,
    "bytes_empty": b"",
    "bytes_uuid": uuid.UUID("2c8bf60f-1ba7-4d9b-bf9e-55c4c1b0e0a7").bytes,
    "bytes_long": bytes(range(256)) * 300,
    "list_empty": [],
    "list_mixed": [1, "two", 3.0, None, True, b"\x00\xff"],
    "map_empty": {},
    "map_record": {
        "oid": 2**53 + 1,
        "authid": "user-0001",
        "realm_oid": 42,
        "email": "user@example.com",
        "registered": 1760500000123456789,
        "roles": ["admin", "user"],
        "pubkey": bytes.fromhex("8b" * 32),
        "ratio": 0.25,
        "active": True,
        "meta": None,
    },
    "map_nested": {"a": {"b": {"c": [{"d": [1, [2, [3, {"e": "f"}]]]}]}}},
    "list_of_maps": [
        {"i": i, "s": str(i), "b": i.to_bytes(4, "big")} for i in range(50)
    ],
}


def _vectors():
    """The vector bytes, by corpus name."""
    with open(VECTORS) as f:
        return {
            k: zlib.decompress(base64.b64decode(v)) for k, v in json.load(f).items()
        }


def test_vectors_cover_corpus():
    assert sorted(_vectors()) == sorted(CORPUS)


@pytest.mark.parametrize("name", sorted(CORPUS))
def test_encode_matches_vector(name):
    """This interpreter's cbor2 encodes each value to exactly the bytes cbor2 6.x wrote."""
    assert cbor2.dumps(CORPUS[name]) == _vectors()[name]


@pytest.mark.parametrize("name", sorted(CORPUS))
def test_decode_vector(name):
    """This interpreter's cbor2 decodes the bytes cbor2 6.x wrote to the original value."""
    assert cbor2.loads(_vectors()[name]) == CORPUS[name]


def test_cbor_table_stores_vector_bytes():
    """A zlmdb CBOR table stores exactly the vector bytes, and reads them back."""
    tab = zlmdb.MapUuidCbor(slot=1, marshal=lambda o: o, unmarshal=lambda o: o)
    vectors = _vectors()
    with TemporaryDirectory() as dbpath:
        with zlmdb.Database(dbpath) as db:
            with db.begin(write=True) as txn:
                for name in sorted(CORPUS):
                    assert tab._serialize_value(CORPUS[name]) == vectors[name]
                    tab[txn, uuid.uuid5(uuid.NAMESPACE_URL, name)] = CORPUS[name]
        with zlmdb.Database(dbpath) as db:
            with db.begin() as txn:
                for name in sorted(CORPUS):
                    assert (
                        tab[txn, uuid.uuid5(uuid.NAMESPACE_URL, name)] == CORPUS[name]
                    )


def test_cbor2_line():
    """The interpreter runs the cbor2 line it is pinned to (pyproject.toml)."""
    major = int(version("cbor2").split(".")[0])
    if platform.python_implementation() == "PyPy":
        assert major == 5
    else:
        assert major >= 6


if __name__ == "__main__":
    vectors = {
        k: base64.b64encode(zlib.compress(cbor2.dumps(v), 9)).decode("ascii")
        for k, v in sorted(CORPUS.items())
    }
    with open(VECTORS, "w") as f:
        json.dump(vectors, f, indent=1)
        f.write("\n")
    print("wrote", VECTORS)
