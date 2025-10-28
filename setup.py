#!/usr/bin/env python
"""
Minimal setup.py shim for zlmdb.

This file exists to:
1. Run build_lmdb.py to prepare LMDB sources before building
2. Build the CFFI extension module for LMDB
3. Ensure compatibility with tools that expect setup.py
4. Delegate to pyproject.toml for all modern packaging configuration

For modern builds, use:
    python -m build

For editable installs:
    pip install -e .
"""

import sys
import os
import subprocess
import shutil
import glob
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


# Run build_lmdb.py at module import time to prepare LMDB sources
print("=" * 70)
print("zlmdb setup.py - Preparing LMDB sources")
print("=" * 70)
result = subprocess.run([sys.executable, 'build_lmdb.py'], capture_output=False)
if result.returncode != 0:
    print("\nERROR: build_lmdb.py failed!")
    sys.exit(1)


class BuildPyWithCFFI(_build_py):
    """Custom build_py that compiles CFFI extension and copies it to build dir."""

    def run(self):
        # Build CFFI extension if not already built
        print("\n" + "=" * 70)
        print("BuildPyWithCFFI: Checking for CFFI extension...")
        print("=" * 70)

        if not glob.glob('lmdb/_lmdb_cffi*.so') and not glob.glob('lmdb/_lmdb_cffi*.pyd'):
            print("Building CFFI extension...")
            result = subprocess.run([sys.executable, 'build_cffi_lmdb.py'],
                                    capture_output=False)
            if result.returncode != 0:
                raise RuntimeError("CFFI build failed!")
        else:
            print("CFFI extension already exists")

        # Run standard build_py first
        print("\nRunning standard build_py...")
        _build_py.run(self)

        # Copy compiled CFFI extension to build directory
        print("\nLooking for CFFI extension files...")
        extensions = (glob.glob('lmdb/_lmdb_cffi*.so') +
                     glob.glob('lmdb/_lmdb_cffi*.pyd') +
                     glob.glob('lmdb/_lmdb_cffi*.dll'))

        if not extensions:
            print("WARNING: No CFFI extension files found!")
        else:
            for so_file in extensions:
                dest_dir = os.path.join(self.build_lib, 'lmdb')
                dest_file = os.path.join(dest_dir, os.path.basename(so_file))
                print(f"✓ Copying: {os.path.basename(so_file)} -> {dest_file}")
                shutil.copy2(so_file, dest_file)
        print("=" * 70 + "\n")


# Configure setuptools with custom build command
setup(
    cmdclass={
        'build_py': BuildPyWithCFFI,
    },
)
