#!/usr/bin/env python
"""
Minimal setup.py shim for zlmdb.

This file exists to:
1. Run build_lmdb.py to prepare LMDB sources before building
2. Ensure compatibility with tools that expect setup.py
3. Delegate to pyproject.toml for all modern packaging configuration

For modern builds, use:
    python -m build

For editable installs:
    pip install -e .
"""

import sys
import subprocess


def main():
    """Run build_lmdb.py before setuptools build."""
    print("=" * 70)
    print("zlmdb setup.py shim")
    print("=" * 70)

    # Step 1: Run build_lmdb.py to prepare LMDB sources
    print("\nStep 1: Preparing vendored LMDB sources...")
    result = subprocess.run([sys.executable, 'build_lmdb.py'],
                            capture_output=False)
    if result.returncode != 0:
        print("\nERROR: build_lmdb.py failed!")
        sys.exit(1)

    # Step 2: Let setuptools handle the rest (via pyproject.toml)
    print("\nStep 2: Running setuptools build...")
    from setuptools import setup
    setup()


if __name__ == '__main__':
    main()
