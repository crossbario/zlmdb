#!/usr/bin/env python
"""
Build script for vendored LMDB with CFFI.

This script:
1. Copies LMDB C sources from lmdb-upstream/ submodule to build directory
2. Applies patches from lmdb-patches/
3. Generates zlmdb/lmdb/_config.py for CFFI compilation
4. Configures CFFI to build the LMDB extension

Based on py-lmdb setup.py patch application logic.
"""

import os
import sys
import shutil
import subprocess
import platform


# The bundled LMDB release lines (#170). Each is copied from its submodule into its own
# build directory and patched there; build_cffi_lmdb.py compiles one CFFI module per
# engine. LMDB 0.9.x writes data format v1, LMDB 1.0.x data format v3.
#
# Both patch series are vendored from py-lmdb 3.0.0 (jnwatson/py-lmdb, lib/py-lmdb/ and
# lib1/py-lmdb/; see the PATCH-STATUS.md in each patch directory), and the lists below
# mirror py-lmdb's setup.py (engines v09 / v10). Order is significant: each patch's line
# numbers reflect the state after all preceding patches have been applied.
ENGINES = [
    {
        'name': 'lmdb',   # LMDB 0.9.x -> zlmdb._lmdb_vendor._lmdb_cffi
        'src': os.path.join('lmdb-upstream', 'libraries', 'liblmdb'),
        'build_dir': os.path.join('build', 'lmdb-src'),
        'patches_dir': 'lmdb-patches',
        # Note: the previous its-10346.patch was dropped - that fix is
        # incorporated upstream since LMDB 0.9.35.
        'patch_files': [
        'env-copy-txn.patch',
        'cursor-next-prev-uninitialized.patch',
        'cve-2019-16224-validate-db-flags.patch',
        'cve-2019-16225-reject-dirty-pages.patch',
        'cve-2019-16226-validate-node-del-size.patch',
        'cve-2019-16227-guard-xcursor-null.patch',
        'cve-2019-16228-validate-psize.patch',
        'validate-page-bounds.patch',
        'validate-node-read-size.patch',
        'validate-subpage-bounds.patch',
        'validate-xcursor-nodedsz.patch',
        'validate-leaf2-keysize.patch',
        'guard-xcursor-null-d3d4.patch',
        'validate-nodedsz-page-split.patch',
        'validate-node-shrink-delta.patch',
        'validate-overflow-pages.patch',
        'validate-nodedsz-cursor-put.patch',
        'validate-md-depth.patch',
        'validate-md-root.patch',
        'win32-sparse-file.patch',
        'fix-large-write.patch',
        'fix-overflow-page-size-mul.patch',
        # Appended, not slotted in with the other validate-* patches: each
        # patch's line numbers reflect the state after all preceding ones.
        'validate-md-pad.patch',
        'validate-ovpage-free.patch',
        'validate-freedb-record.patch',
        ],
    },
    {
        'name': 'lmdb1',  # LMDB 1.0.x -> zlmdb._lmdb_vendor._lmdb1_cffi
        'src': os.path.join('lmdb-upstream-1.0', 'libraries', 'liblmdb'),
        'build_dir': os.path.join('build', 'lmdb1-src'),
        'patches_dir': 'lmdb-patches-1.0',
        # The 1.0 series omits two patches carried for 0.9: fix-large-write's
        # remaining hunk landed upstream as ITS#9223, and win32-sparse-file's
        # defect was designed away by 1.0's incremental file growth. A third,
        # cve-2019-16225-reject-dirty-pages, keys on the P_DIRTY page flag, which
        # 1.0 removed; cve-2019-16225-validate-mp-txnid carries the protection
        # forward. rename.h (in lmdb-patches-1.0/) is only needed to link both
        # trees into one module, which this CFFI-only build never does.
        'patch_files': [
            'env-copy-txn.patch',
            'cursor-next-prev-uninitialized.patch',
            'cve-2019-16224-validate-db-flags.patch',
            'cve-2019-16226-validate-node-del-size.patch',
            'cve-2019-16227-guard-xcursor-null.patch',
            'cve-2019-16228-validate-psize.patch',
            'validate-page-bounds.patch',
            'validate-node-read-size.patch',
            'validate-subpage-bounds.patch',
            'validate-xcursor-nodedsz.patch',
            'validate-leaf2-keysize.patch',
            'guard-xcursor-null-d3d4.patch',
            'validate-nodedsz-page-split.patch',
            'validate-node-shrink-delta.patch',
            'validate-overflow-pages.patch',
            'validate-nodedsz-cursor-put.patch',
            'validate-md-depth.patch',
            'validate-md-root.patch',
            'fix-overflow-page-size-mul.patch',
            # Appended for the same reason as in the 0.9 series.
            'validate-md-pad.patch',
            'validate-ovpage-free.patch',
            # 1.0 only: 0.9 gets this protection from
            # cve-2019-16225-reject-dirty-pages, which keys on P_DIRTY.
            'cve-2019-16225-validate-mp-txnid.patch',
            'validate-freedb-record.patch',
        ],
    },
]


def apply_patches(engine):
    """Copy one engine's LMDB sources to its build directory and apply its patches."""
    print("=" * 70)
    print("Building vendored LMDB with CFFI")
    print("=" * 70)

    # Source and destination paths
    lmdb_src = engine['src']
    build_dir = engine['build_dir']
    patches_dir = engine['patches_dir']

    if not os.path.exists(lmdb_src):
        print(f"ERROR: LMDB source not found at {lmdb_src}")
        print("Did you initialize git submodules?")
        print("Run: git submodule update --init --recursive")
        sys.exit(1)

    # Create build directory
    os.makedirs('build', exist_ok=True)

    # Clean old build directory
    if os.path.exists(build_dir):
        print(f"Removing old build directory: {build_dir}")
        shutil.rmtree(build_dir)

    # Copy LMDB sources to build directory
    print(f"Copying LMDB sources from {lmdb_src} to {build_dir}")
    shutil.copytree(lmdb_src, build_dir)

    # Apply patches (see ENGINES for the series and why its order matters)
    patch_files = engine['patch_files']

    for patch_file in patch_files:
        patch_path = os.path.join(patches_dir, patch_file)
        if not os.path.exists(patch_path):
            print(f"WARNING: Patch file not found: {patch_path}")
            continue

        print(f"Applying patch: {patch_file}")

        # The patches are from py-lmdb which has structure:
        # libraries/liblmdb/...
        # We need to apply with -p3 to strip those path components

        if sys.platform.startswith('win'):
            try:
                import patch_ng as patch

                # Use absolute paths for patch-ng
                abs_patch_path = os.path.abspath(patch_path)
                abs_build_dir = os.path.abspath(build_dir)

                # Debug info
                print(f"  Patch file: {abs_patch_path}")
                print(f"  Build directory: {abs_build_dir}")
                print(f"  Build directory exists: {os.path.exists(abs_build_dir)}")
                if os.path.exists(abs_build_dir):
                    print(f"  Files in build dir: {os.listdir(abs_build_dir)[:5]}")

                patchset = patch.fromfile(abs_patch_path)
                if not patchset:
                    print(f"ERROR: Failed to parse patch file {patch_file}")
                    sys.exit(1)

                print(f"  Parsed {len(patchset.items)} patch items")

                # Debug: show what we're trying to patch
                for item in patchset.items:
                    target = item.target if isinstance(item.target, str) else item.target.decode('utf-8', errors='replace')
                    print(f"    Patch item target (raw): {target}")

                # List files in build directory to verify they exist
                print(f"  Files in {abs_build_dir}:")
                for f in os.listdir(abs_build_dir)[:10]:
                    print(f"    - {f}")

                # Apply patch - try strip=3 first, fallback to auto-detect
                # The patches have paths like: a/libraries/liblmdb/lmdb.h
                # We need to strip 3 levels: a/, libraries/, liblmdb/
                # to get: lmdb.h (which is directly in build/lmdb-src/)
                print("  Attempting to apply with strip=3...")
                success = False

                # Try strip levels 0-4 until one works
                for strip_level in [3, 2, 4, 1, 0]:
                    print(f"  Trying strip={strip_level}...")
                    try:
                        # patch-ng.PatchSet.apply(strip=N, root=path)
                        result = patchset.apply(strip_level, abs_build_dir)
                        if result:
                            print(f"  [OK] Successfully applied with strip={strip_level}")
                            success = True
                            break
                        else:
                            print(f"  [FAIL] strip={strip_level} did not work")
                    except Exception as e:
                        print(f"  [ERROR] strip={strip_level} raised: {e}")
                        continue

                if not success:
                    # None of the strip levels worked
                    print(f"  [FAIL] Failed to apply patch {patch_file} with any strip level")
                    print(f"ERROR: Failed to apply patch {patch_file}")
                    sys.exit(1)
            except ImportError:
                print("ERROR: patch-ng module required on Windows")
                print("Install with: pip install patch-ng")
                sys.exit(1)
            except Exception as e:
                print(f"ERROR: Exception while applying patch {patch_file}: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            # Unix: use patch command
            cmd = ['patch', '-N', '-p3', '-d', build_dir, '-i',
                   os.path.abspath(patch_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # patch returns non-zero if already applied, check output
                if 'Reversed (or previously applied) patch detected' in result.stdout:
                    print("  (already applied)")
                else:
                    print(f"ERROR: Failed to apply patch {patch_file}")
                    print(result.stdout)
                    print(result.stderr)
                    sys.exit(1)
            else:
                print("  [OK] Applied successfully")

    return build_dir


def generate_config(build_dirs):
    """Generate src/zlmdb/_lmdb_vendor/_config.py with build configuration."""
    print("\nGenerating src/zlmdb/_lmdb_vendor/_config.py")

    # Per engine: the sources to compile and the include directories. The top-level
    # extra_sources / extra_include_dirs below are the first engine's (LMDB 0.9),
    # which the single-engine ffi.verify() fallback in cffi.py uses.
    engines = [
        {
            'name': engine['name'],
            'sources': [
                os.path.join(build_dirs[engine['name']], 'mdb.c'),
                os.path.join(build_dirs[engine['name']], 'midl.c'),
            ],
            'include_dirs': [
                build_dirs[engine['name']],
                'lmdb-patches',  # for preload.h
            ],
        }
        for engine in ENGINES
    ]

    # Source files to compile
    extra_sources = engines[0]['sources']

    # Include directories
    extra_include_dirs = list(engines[0]['include_dirs'])

    # Compile args
    extra_compile_args = [
        '-UNDEBUG',  # Disable NDEBUG
        '-DHAVE_PATCHED_LMDB=1',  # Mark as patched version
    ]

    # Disable warnings unless maintainer mode
    if not os.getenv('LMDB_MAINTAINER'):
        extra_compile_args.append('-w')

    # Windows-specific configuration
    libraries = []
    if sys.platform.startswith('win'):
        # Add Windows-specific includes for MSVC compatibility
        extra_include_dirs.append('lmdb-patches')
        libraries.append('Advapi32')

        # MSVC version detection
        p = sys.version.find('MSC v.')
        msvc_ver = int(sys.version[p + 6: p + 10]) if p != -1 else None
        if msvc_ver and not msvc_ver >= 1600:
            # Visual Studio <= 2010 needs stdint.h emulation
            print("  (adding stdint.h emulation for old MSVC)")

    # Write configuration
    config = {
        'extra_compile_args': extra_compile_args,
        'extra_sources': extra_sources,
        'extra_library_dirs': [],
        'extra_include_dirs': extra_include_dirs,
        'libraries': libraries,
        'engines': engines,
    }

    config_file = os.path.join('src', 'zlmdb', '_lmdb_vendor', '_config.py')
    print(f"  Writing to {config_file}")

    with open(config_file, 'w') as f:
        f.write('# Auto-generated by build_lmdb.py\n')
        f.write('# DO NOT EDIT - regenerated on each build\n\n')
        f.write('CONFIG = {\n')
        for key, value in config.items():
            f.write(f'    {key!r}: {value!r},\n')
        f.write('}\n')

    print("  [OK] Configuration written")
    return config


def main():
    """Main build entry point."""
    print("\n" + "=" * 70)
    print("zlmdb LMDB build script")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Working directory: {os.getcwd()}")
    print()

    # Step 1: Apply patches, per engine
    build_dirs = {engine['name']: apply_patches(engine) for engine in ENGINES}

    # Step 2: Generate config
    config = generate_config(build_dirs)

    print("\n" + "=" * 70)
    print("LMDB build preparation complete")
    print("=" * 70)
    print("\nCFFI will now compile the patched LMDB sources.")
    print("This happens automatically during 'pip install' or 'python -m build'")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
