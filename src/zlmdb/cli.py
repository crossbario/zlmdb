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
"""Console script for zlmdb."""

import os
import sys

import click

from zlmdb._database import Database


@click.group()
def main():
    """zlmdb command line tool."""


@main.command()
@click.argument("dbpath", type=click.Path(file_okay=False))
@click.option(
    "--lib-version",
    type=click.Choice(["1.0", "0.9"]),
    default=None,
    help="Require this LMDB format; exit with 1 if the database has the other one.",
)
def info(dbpath, lib_version):
    """Show the LMDB format, LMDB version and statistics of the database at DBPATH.

    The database is opened read-only, and nothing is created. Exit code 0 if the
    database was opened, 1 if there is none or it has another format than --lib-version.
    """
    if not os.path.exists(os.path.join(dbpath, "data.mdb")):
        click.echo('error: no database at "{}"'.format(dbpath), err=True)
        sys.exit(1)
    try:
        with Database(
            dbpath, readonly=True, create=False, lib_version=lib_version
        ) as db:
            stats = db.stats()
    except ValueError as e:
        click.echo("error: {}".format(e), err=True)
        sys.exit(1)
    for key in sorted(stats):
        click.echo("{}: {}".format(key, stats[key]))


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
