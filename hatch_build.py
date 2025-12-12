"""
Hatchling custom build hook for CFFI extension modules and flatc compiler.

This builds:
1. The vendored LMDB CFFI extension (patches from git submodule)
2. The FlatBuffers compiler (flatc) from deps/flatbuffers
3. The reflection.bfbs binary schema for runtime introspection

See: https://hatch.pypa.io/latest/plugins/build-hook/custom/
"""

import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class LmdbCffiBuildHook(BuildHookInterface):
    """Build hook for compiling LMDB CFFI extension and flatc compiler."""

    PLUGIN_NAME = "lmdb-cffi"

    def initialize(self, version, build_data):
        """
        Called before each build.

        For wheel builds, compile the CFFI modules and flatc.
        For sdist builds, just ensure source files are included.
        """
        # Always capture flatbuffers git version (for both wheel and sdist)
        self._update_flatbuffers_git_version()

        if self.target_name != "wheel":
            # Only compile for wheel builds, sdist just includes source
            return

        # Build LMDB CFFI module
        built_lmdb = self._build_lmdb_cffi(build_data)

        # Build flatc compiler
        built_flatc = self._build_flatc(build_data)

        # Generate reflection.bfbs using the built flatc
        if built_flatc:
            self._generate_reflection_bfbs(build_data)

        # If we built any extensions, mark this as a platform-specific wheel
        if built_lmdb or built_flatc:
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

    def _build_flatc(self, build_data):
        """Build the FlatBuffers compiler (flatc) from deps/flatbuffers.

        Returns True if flatc was successfully built.
        """
        print("\n" + "=" * 70)
        print("Building FlatBuffers compiler (flatc)")
        print("=" * 70)

        flatbuffers_dir = Path(self.root) / "deps" / "flatbuffers"
        build_dir = flatbuffers_dir / "build"
        flatc_bin_dir = Path(self.root) / "src" / "zlmdb" / "_flatc" / "bin"

        # Determine executable name based on platform
        exe_name = "flatc.exe" if os.name == "nt" else "flatc"

        # Check if cmake is available
        cmake_path = shutil.which("cmake")
        if not cmake_path:
            print("WARNING: cmake not found, skipping flatc build")
            print("  -> Install cmake to enable flatc bundling")
            return False

        # Check if flatbuffers source exists
        if not flatbuffers_dir.exists():
            print(f"WARNING: {flatbuffers_dir} not found")
            print("  -> Initialize git submodule: git submodule update --init")
            return False

        # Clean and create build directory (remove any cached cmake config)
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Configure with cmake
        print("  -> Configuring with cmake...")
        cmake_args = [
            cmake_path,
            "..",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DFLATBUFFERS_BUILD_TESTS=OFF",
            "-DFLATBUFFERS_BUILD_FLATLIB=OFF",
            "-DFLATBUFFERS_BUILD_FLATHASH=OFF",
            "-DFLATBUFFERS_BUILD_GRPCTEST=OFF",
            "-DFLATBUFFERS_BUILD_SHAREDLIB=OFF",
        ]

        # ====================================================================
        # Manylinux compatibility flags for Linux builds
        # ====================================================================
        # Goal: Produce an auditwheel-safe binary that only uses baseline ISA
        #
        # Without these flags, the resulting flatc binary may contain x86_64_v2
        # instructions (SSE4.2, POPCNT, etc.) either from:
        #   1. Our compiled code (compiler auto-vectorization)
        #   2. Dynamically linked libstdc++/libgcc from system toolchain
        #
        # auditwheel rejects wheels with x86_64_v2+ instructions because they
        # won't run on older CPUs that manylinux wheels are supposed to support.
        #
        # The solution:
        #   - Use baseline ISA flags (-march=x86-64) for portable code
        #   - Static link C++ runtime to avoid v2 instructions from system libs
        #   - Clear FlatBuffers' own CXX flags to prevent it adding extras
        #   - Keep glibc dynamic (required for manylinux compatibility)
        # ====================================================================
        if sys.platform.startswith("linux") and os.uname().machine == "x86_64":
            print("==================================================================")
            print("  -> Using baseline x86-64 flags for manylinux compatibility")
            print("  -> Static linking libstdc++/libgcc to avoid v2 instructions")
            print("==================================================================")
            cmake_args.extend([
                # Baseline x86-64 ISA (no SSE4.2, AVX, etc.) - ensures portable code
                "-DCMAKE_C_FLAGS_INIT=-march=x86-64 -mtune=generic",
                "-DCMAKE_CXX_FLAGS_INIT=-march=x86-64 -mtune=generic",
                # Clear FlatBuffers' own CXX flags to prevent it adding extras
                "-DFLATBUFFERS_CXX_FLAGS=",
                # Static link C++ runtime - avoids x86_64_v2 from system libstdc++
                # Note: glibc remains dynamic (required for manylinux)
                "-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc",
            ])
        elif sys.platform.startswith("linux") and os.uname().machine in (
            "aarch64",
            "arm64",
        ):
            print("==================================================================")
            print("  -> Using baseline arm64 flags for manylinux compatibility")
            print("  -> Static linking libstdc++/libgcc")
            print("==================================================================")
            cmake_args.extend([
                # Baseline ARMv8-A ISA - ensures portable code
                "-DCMAKE_C_FLAGS_INIT=-march=armv8-a",
                "-DCMAKE_CXX_FLAGS_INIT=-march=armv8-a",
                # Clear FlatBuffers' own CXX flags
                "-DFLATBUFFERS_CXX_FLAGS=",
                # Static link C++ runtime - avoids ISA issues from system libs
                # Note: glibc remains dynamic (required for manylinux)
                "-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc",
            ])

        result = subprocess.run(
            cmake_args,
            cwd=build_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: cmake configure failed:\n{result.stderr}")
            return False

        # Step 2: Build flatc
        print("  -> Building flatc...")
        build_args = [
            cmake_path,
            "--build",
            ".",
            "--config",
            "Release",
            "--target",
            "flatc",
        ]

        result = subprocess.run(
            build_args,
            cwd=build_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: cmake build failed:\n{result.stderr}")
            return False

        # Step 3: Find and copy the built flatc
        # flatc might be in different locations depending on platform/generator
        possible_locations = [
            build_dir / exe_name,
            build_dir / "Release" / exe_name,  # Windows/MSVC
            build_dir / "Debug" / exe_name,
        ]

        flatc_src = None
        for loc in possible_locations:
            if loc.exists():
                flatc_src = loc
                break

        if not flatc_src:
            print(f"ERROR: Built flatc not found in {build_dir}")
            for loc in possible_locations:
                print(f"  Checked: {loc}")
            return False

        # Copy flatc to package bin directory
        flatc_bin_dir.mkdir(parents=True, exist_ok=True)
        flatc_dest = flatc_bin_dir / exe_name
        shutil.copy2(flatc_src, flatc_dest)

        # Make executable on Unix
        if os.name != "nt":
            flatc_dest.chmod(0o755)

        print(f"  -> Built flatc: {flatc_dest}")

        # Verify ISA level on Linux (check for x86_64_v2 instructions)
        if sys.platform.startswith("linux"):
            print("  -> Verifying ISA level...")
            readelf_result = subprocess.run(
                ["readelf", "-A", str(flatc_dest)],
                capture_output=True,
                text=True,
            )
            if readelf_result.returncode == 0:
                # Look for ISA info in output
                for line in readelf_result.stdout.splitlines():
                    if "ISA" in line or "x86" in line.lower():
                        print(f"     {line.strip()}")
            # Also check file command for architecture info
            file_result = subprocess.run(
                ["file", str(flatc_dest)],
                capture_output=True,
                text=True,
            )
            if file_result.returncode == 0:
                print(f"     {file_result.stdout.strip()}")

        # Add flatc to wheel
        src_file = str(flatc_dest)
        dest_path = f"zlmdb/_flatc/bin/{exe_name}"
        build_data["force_include"][src_file] = dest_path
        print(f"  -> Added to wheel: {dest_path}")

        # Store flatc path for later use (reflection.bfbs generation)
        self._flatc_path = flatc_dest
        return True

    def _generate_reflection_bfbs(self, build_data):
        """Generate reflection.bfbs using the built flatc.

        This creates the binary FlatBuffers schema that allows runtime
        schema introspection.
        """
        print("\n" + "=" * 70)
        print("Generating reflection.bfbs")
        print("=" * 70)

        if not hasattr(self, "_flatc_path") or not self._flatc_path.exists():
            print("WARNING: flatc not available, skipping reflection.bfbs generation")
            return False

        flatbuffers_dir = Path(self.root) / "deps" / "flatbuffers"
        reflection_fbs = flatbuffers_dir / "reflection" / "reflection.fbs"
        output_dir = Path(self.root) / "src" / "zlmdb" / "flatbuffers"

        if not reflection_fbs.exists():
            print(f"WARNING: {reflection_fbs} not found")
            return False

        # Generate reflection.bfbs
        result = subprocess.run(
            [
                str(self._flatc_path),
                "--binary",
                "--schema",
                "--bfbs-comments",
                "--bfbs-builtins",
                "-o",
                str(output_dir),
                str(reflection_fbs),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"ERROR: flatc failed:\n{result.stderr}")
            return False

        reflection_bfbs = output_dir / "reflection.bfbs"
        if reflection_bfbs.exists():
            print(f"  -> Generated: {reflection_bfbs}")

            # Add to wheel
            src_file = str(reflection_bfbs)
            dest_path = "zlmdb/flatbuffers/reflection.bfbs"
            build_data["force_include"][src_file] = dest_path
            print(f"  -> Added to wheel: {dest_path}")
            return True
        else:
            print("WARNING: reflection.bfbs not generated")
            return False

    def _update_flatbuffers_git_version(self):
        """
        Capture the git describe version of deps/flatbuffers submodule.

        This writes the version to flatbuffers/_git_version.py so that
        zlmdb.flatbuffers.version() returns the exact git version at runtime.
        """
        print("=" * 70)
        print("Capturing FlatBuffers git version from deps/flatbuffers")
        print("=" * 70)

        flatbuffers_dir = Path(self.root) / "deps" / "flatbuffers"
        git_version_file = (
            Path(self.root) / "src" / "zlmdb" / "flatbuffers" / "_git_version.py"
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
