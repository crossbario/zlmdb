"""
Hatchling custom build hook for CFFI extension modules.

This builds the vendored LMDB CFFI extension by:
1. Capturing git version of deps/flatbuffers submodule
2. Running build_lmdb.py to prepare LMDB sources (patches from git submodule)
3. Running build_cffi_lmdb.py to compile the CFFI extension

See: https://hatch.pypa.io/latest/plugins/build-hook/custom/
"""

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LmdbCffiBuildHook(BuildHookInterface):
    """Build hook for compiling LMDB CFFI extension module."""

    PLUGIN_NAME = "lmdb-cffi"

    def initialize(self, version, build_data):
        """
        Called before each build.

        For wheel builds, compile the CFFI modules.
        For sdist builds, just ensure source files are included.
        """
        # Always capture flatbuffers git version (for both wheel and sdist)
        self._update_flatbuffers_git_version()

        if self.target_name != "wheel":
            # Only compile for wheel builds, sdist just includes source
            return

        # Build CFFI module
        built_extension = self._build_lmdb_cffi(build_data)

        # If we built extension, mark this as a platform-specific wheel
        if built_extension:
            build_data["infer_tag"] = True
            build_data["pure_python"] = False

    def _build_lmdb_cffi(self, build_data):
        """Build the LMDB CFFI extension module.

        Returns True if extension was successfully built.
        """
        # Get the extension suffix for current Python to filter artifacts
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
        print(f"Building LMDB CFFI for Python with extension suffix: {ext_suffix}")

        # Step 1: Run build_lmdb.py to prepare LMDB sources
        print("=" * 70)
        print("Step 1: Preparing LMDB sources (build_lmdb.py)")
        print("=" * 70)

        build_lmdb_script = Path(self.root) / "build_lmdb.py"
        if not build_lmdb_script.exists():
            print(f"ERROR: {build_lmdb_script} not found")
            return False

        result = subprocess.run(
            [sys.executable, str(build_lmdb_script)],
            cwd=self.root,
            capture_output=False,
        )
        if result.returncode != 0:
            print("ERROR: build_lmdb.py failed!")
            return False

        # Step 2: Run build_cffi_lmdb.py to compile CFFI extension
        print("\n" + "=" * 70)
        print("Step 2: Compiling CFFI extension (build_cffi_lmdb.py)")
        print("=" * 70)

        build_cffi_script = Path(self.root) / "build_cffi_lmdb.py"
        if not build_cffi_script.exists():
            print(f"ERROR: {build_cffi_script} not found")
            return False

        result = subprocess.run(
            [sys.executable, str(build_cffi_script)],
            cwd=self.root,
            capture_output=False,
        )
        if result.returncode != 0:
            print("ERROR: build_cffi_lmdb.py failed!")
            return False

        # Step 3: Find the compiled artifact and add to wheel
        print("\n" + "=" * 70)
        print("Step 3: Adding compiled extension to wheel")
        print("=" * 70)

        vendor_dir = Path(self.root) / "src" / "zlmdb" / "_lmdb_vendor"
        expected_so = vendor_dir / f"_lmdb_cffi{ext_suffix}"

        if expected_so.exists():
            src_file = str(expected_so)
            dest_path = f"zlmdb/_lmdb_vendor/{expected_so.name}"
            build_data["force_include"][src_file] = dest_path
            print(f"  -> Added artifact: {expected_so.name} -> {dest_path}")
            return True
        else:
            print(f"WARNING: Expected CFFI extension not found: {expected_so}")
            # Check what .so files exist
            for so_file in vendor_dir.glob("_lmdb_cffi*.so"):
                print(f"  Found: {so_file.name}")
            return False

    def _update_flatbuffers_git_version(self):
        """
        Capture the git describe version of deps/flatbuffers submodule.

        This writes the version to _flatbuffers_vendor/_git_version.py so that
        zlmdb.flatbuffers.version() returns the exact git version at runtime.
        """
        print("=" * 70)
        print("Capturing FlatBuffers git version from deps/flatbuffers")
        print("=" * 70)

        flatbuffers_dir = Path(self.root) / "deps" / "flatbuffers"
        git_version_file = (
            Path(self.root)
            / "src"
            / "zlmdb"
            / "_flatbuffers_vendor"
            / "_git_version.py"
        )

        # Default version if git is not available or submodule not initialized
        git_version = "unknown"

        if flatbuffers_dir.exists() and (flatbuffers_dir / ".git").exists():
            try:
                result = subprocess.run(
                    ["git", "describe", "--tags", "--always"],
                    cwd=flatbuffers_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    git_version = result.stdout.strip()
                    print(f"  -> Git version: {git_version}")
                else:
                    print(f"  -> git describe failed: {result.stderr}")
            except FileNotFoundError:
                print("  -> git command not found, using existing version")
                # Keep existing version in file if git not available
                return
            except subprocess.TimeoutExpired:
                print("  -> git describe timed out, using existing version")
                return
            except Exception as e:
                print(f"  -> Error getting git version: {e}")
                return
        else:
            print("  -> deps/flatbuffers not found or not a git repo")
            print(f"  -> Using existing version in {git_version_file.name}")
            return

        # Write the version file
        content = """\
# Copyright 2014 Google Inc. All rights reserved.
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

# Git version from deps/flatbuffers submodule.
# This file is regenerated at build time by hatch_build.py.
# The version is captured via `git describe --tags` in the submodule.
#
# Format: "v25.9.23" (tagged release) or "v25.9.23-2-g95053e6a" (post-tag)
#
# If building from sdist without git, this will retain the version
# from when the sdist was created.

__git_version__ = "{version}"
""".format(version=git_version)

        git_version_file.write_text(content)
        print(f"  -> Updated {git_version_file.name}")
