#!/usr/bin/env python
"""
Minimal setup.py shim for zlmdb.

IMPORTANT: Why does this file still exist?

This setup.py is ONLY needed for CFFI extension module building (LMDB).
All other package configuration is in pyproject.toml.

This file exists to:
1. Run build_lmdb.py to prepare LMDB sources before building
2. Build the CFFI extension module for LMDB
3. Ensure compatibility with tools that expect setup.py
4. Delegate to pyproject.toml for all modern packaging configuration

For modern builds, use:
    python -m build

For editable installs:
    pip install -e .

If CFFI ever gets pyproject.toml support, this file can be removed.
See: https://cffi.readthedocs.io/en/latest/cdef.html#ffi-set-source-preparing-out-of-line-modules
"""

import sys
import os
import subprocess
import shutil
import glob
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.dist import Distribution


# Run build_lmdb.py at module import time to prepare LMDB sources
print("=" * 70)
print("zlmdb setup.py - Preparing LMDB sources")
print("=" * 70)
result = subprocess.run([sys.executable, 'build_lmdb.py'], capture_output=False)
if result.returncode != 0:
    print("\nERROR: build_lmdb.py failed!")
    sys.exit(1)

# Compile CFFI extension at module-level (before setup() call)
# This ensures the .so file exists when setuptools packages the wheel
# Always compile for the current Python interpreter (don't reuse cached .so from other versions)
print("\n" + "=" * 70)
print("zlmdb setup.py - Compiling CFFI extension")
print("=" * 70)
print(f"Building CFFI extension for {sys.version.split()[0]}...")
result = subprocess.run([sys.executable, 'build_cffi_lmdb.py'], capture_output=False)
if result.returncode != 0:
    print("\nERROR: build_cffi_lmdb.py failed!")
    sys.exit(1)
print("OK: CFFI extension compiled successfully")

# Clean up old .so files from other Python versions to prevent cross-contamination
import sysconfig
ext_suffix = sysconfig.get_config_var('EXT_SUFFIX') or sysconfig.get_config_var('SO')
current_so = f'src/zlmdb/_lmdb_vendor/_lmdb_cffi{ext_suffix}'
print(f"\nCleaning up .so files from other Python versions (keeping {os.path.basename(current_so)})...")
for so_file in glob.glob('src/zlmdb/_lmdb_vendor/_lmdb_cffi*.so') + glob.glob('src/zlmdb/_lmdb_vendor/_lmdb_cffi*.pyd'):
    if so_file != current_so:
        print(f"  Removing: {os.path.basename(so_file)}")
        os.remove(so_file)
print("=" * 70 + "\n")


class BuildPyWithCFFI(_build_py):
    """Custom build_py that compiles CFFI extension and copies it to build dir."""

    def run(self):
        # Run standard build_py first
        print("\nRunning standard build_py...")
        _build_py.run(self)

        # Copy compiled CFFI extension for CURRENT Python version to build directory
        print("\nLooking for CFFI extension for current Python version...")

        # Get the expected extension filename for the current Python
        import sysconfig
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX') or sysconfig.get_config_var('SO')
        expected_file = f'src/zlmdb/_lmdb_vendor/_lmdb_cffi{ext_suffix}'

        if os.path.exists(expected_file):
            dest_dir = os.path.join(self.build_lib, 'zlmdb', '_lmdb_vendor')
            dest_file = os.path.join(dest_dir, os.path.basename(expected_file))
            print(f"OK: Copying: {os.path.basename(expected_file)} -> {dest_file}")
            shutil.copy2(expected_file, dest_file)
        else:
            print(f"WARNING: Expected CFFI extension not found: {expected_file}")
        print("=" * 70 + "\n")


class BinaryDistribution(Distribution):
    """Force setuptools to recognize this as a binary (platform-specific) package.

    This ensures wheels are tagged correctly (e.g., cp311-cp311-linux_x86_64)
    instead of pure Python tags (py3-none-any).
    """
    def has_ext_modules(self):
        return True


# Configure setuptools with custom build command
setup(
    cmdclass={
        'build_py': BuildPyWithCFFI,
    },
    distclass=BinaryDistribution,
)
