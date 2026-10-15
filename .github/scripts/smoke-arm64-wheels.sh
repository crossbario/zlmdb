#!/bin/bash
# Smoke-test ARM64 wheels inside Docker container on a native ARM64 runner
# This script runs INSIDE the same ARM64 container image that built the wheels
# (see build-arm64-wheel.sh): every wheel in /io/wheelhouse is installed in its
# own fresh venv and smoke-tested, including both bundled LMDB engines (#171).
set -ex

# Install required tools if not present (dependencies without a binary wheel
# for the platform are built from source during the wheel install)
if ! command -v curl &> /dev/null || ! command -v gcc &> /dev/null; then
  if command -v yum &> /dev/null; then
    # RHEL/CentOS based manylinux images (CPython)
    yum install -y curl git gcc gcc-c++ make libffi-devel
  elif command -v apt-get &> /dev/null; then
    # Debian based images (PyPy)
    apt-get update
    apt-get install -y curl git build-essential libffi-dev
  fi
fi

# Install Just (task runner)
curl --proto "=https" --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin
just --version

# Install uv (required by justfile as script interpreter)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
uv --version

# For manylinux CPython: Add all Python versions to PATH
if [ -d "/opt/python" ]; then
  for pyver in /opt/python/*/bin; do
    if [ -d "$pyver" ]; then
      export PATH="$pyver:$PATH"
    fi
  done
fi

echo "==> Smoke test environment:"
echo "Platform: $(uname -m)"
echo "Just: $(just --version)"
echo "uv: $(uv --version)"

just test-wheels-install /io/wheelhouse
