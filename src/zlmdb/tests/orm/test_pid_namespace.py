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
Processes in different PID namespaces with the same PID cannot share a database (#196).

LMDB marks a live reader by an fcntl lock on the byte at offset = its PID in
``lock.mdb``. Two processes with the same PID in different PID namespaces (e.g. PID 1
in two containers) collide on that byte, and the second one cannot open the database.
That is a deployment error, not a transient one: ``zlmdb.Database`` must say so, and
name the remedy (a shared PID namespace), instead of only "giving up after 3 retries".

``unshare -Urpf`` gives each process its own user and PID namespace, where it is PID 1.
The tests are skipped where unprivileged user namespaces are not available.
"""

import shutil
import subprocess
import sys

import pytest

HOLDER = (
    "import sys, zlmdb; "
    "db = zlmdb.Database(dbpath=sys.argv[1], maxsize=16 * 1024 * 1024, lib_version=sys.argv[2]); "
    "db.__enter__(); "
    "txn = db.begin(); "
    "print('ready', flush=True); "
    "sys.stdin.readline()"
)

OPENER = (
    "import sys, zlmdb\n"
    "try:\n"
    "    with zlmdb.Database(dbpath=sys.argv[1], maxsize=16 * 1024 * 1024) as db:\n"
    "        pass\n"
    "    print('OK')\n"
    "except Exception as e:\n"
    "    print('{}: {}'.format(type(e).__name__, e))\n"
)

UNSHARE = ["unshare", "-Urpf"]


def _unshare_available() -> bool:
    if not sys.platform.startswith("linux") or shutil.which("unshare") is None:
        return False
    return subprocess.run(UNSHARE + ["true"], capture_output=True).returncode == 0


pytestmark = pytest.mark.skipif(
    not _unshare_available(),
    reason="needs Linux with unprivileged user and PID namespaces (unshare -Urpf)",
)


def _open_while_held(dbpath: str, lib_version: str, prefix: list) -> str:
    """Hold the database open (with a reader) in one process, open it from another,
    both started with ``prefix``. Returns the opener's one-line result."""
    holder = subprocess.Popen(
        prefix + [sys.executable, "-c", HOLDER, dbpath, lib_version],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout.readline().strip() == "ready"
        opener = subprocess.run(
            prefix + [sys.executable, "-c", OPENER, dbpath],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert opener.returncode == 0, opener.stderr
        return opener.stdout.strip()
    finally:
        holder.stdin.close()
        holder.wait(timeout=60)


@pytest.mark.parametrize("lib_version", ["0.9", "1.0"])
def test_same_pid_in_two_namespaces_is_explained(tmp_path, lib_version):
    result = _open_while_held(str(tmp_path), lib_version, UNSHARE)
    assert result.startswith("RuntimeError: "), result
    assert "PID namespace" in result, result


@pytest.mark.parametrize("lib_version", ["0.9", "1.0"])
def test_distinct_pids_share_the_database(tmp_path, lib_version):
    """The control: the same processes without namespaces have distinct PIDs."""
    assert _open_while_held(str(tmp_path), lib_version, []) == "OK"
