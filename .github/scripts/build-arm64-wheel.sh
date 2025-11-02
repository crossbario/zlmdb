#!/bin/bash
# Build ARM64 wheels inside Docker container with QEMU emulation
# This script runs INSIDE the manylinux ARM64 container
set -ex

# Install required tools and build dependencies if not present
if ! command -v curl &> /dev/null || ! command -v gcc &> /dev/null; then
  if command -v yum &> /dev/null; then
    # RHEL/CentOS based manylinux images
    yum install -y curl git gcc gcc-c++ make libffi-devel
  elif command -v apt-get &> /dev/null; then
    # Debian based images (used for PyPy)
    apt-get update
    apt-get install -y curl git build-essential libssl-dev libffi-dev \
      libunwind-dev libreadline-dev zlib1g-dev libbz2-dev libsqlite3-dev \
      libncurses5-dev libsnappy-dev
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

# Verify environment
echo "==> Build environment:"
echo "Platform: $(uname -m)"
echo "glibc: $(ldd --version 2>/dev/null | head -1 || echo 'N/A')"
echo "Python: $(python3 --version 2>/dev/null || echo 'not available')"
echo "Just: $(just --version)"
echo "uv: $(uv --version)"
echo "auditwheel: $(auditwheel --version || echo 'not available')"

# Clean up any stale venvs from previous runs (Docker volume persistence issue)
# This is especially important for PyPy where the venv directory might exist but be broken
if [ -d "/io/.venvs" ]; then
  echo "==> Cleaning up stale virtual environments..."
  rm -rf /io/.venvs
  echo "[OK] Cleaned up /io/.venvs"
fi

# Build binary wheels with LMDB CFFI extensions
# Uses install-build-tools (not install-tools) to avoid problematic dependencies under QEMU

# Build only specified Python versions (or all if not specified)
if [ -n "$PYTHON_VERSIONS" ]; then
  echo "==> Building wheels for specific Python versions: $PYTHON_VERSIONS"
  for venv in $PYTHON_VERSIONS; do
    echo "Building for $venv..."
    just build "$venv"
  done
else
  echo "==> Building wheels for all Python versions (PYTHON_VERSIONS not set)"
  just build-all
fi

# Repair/convert wheels to manylinux format if auditwheel is available
if command -v auditwheel &> /dev/null; then
  echo ""
  echo "==> Converting wheels to manylinux format..."
  mkdir -p /io/wheelhouse

  for wheel in dist/*.whl; do
    if [[ "$wheel" == *"linux_aarch64"* ]]; then
      echo "Converting: $(basename $wheel)"
      # auditwheel show is diagnostic only - don't fail if it segfaults
      auditwheel show "$wheel" || echo "WARNING: auditwheel show failed (non-fatal)"
      # auditwheel repair is what actually matters
      auditwheel repair "$wheel" -w /io/wheelhouse/
    else
      echo "Copying non-linux wheel: $(basename $wheel)"
      cp "$wheel" /io/wheelhouse/
    fi
  done

  echo ""
  echo "==> Final wheel inventory after manylinux conversion:"
  ls -la /io/wheelhouse/
  for wheel in /io/wheelhouse/*.whl; do
    # Diagnostic only - don't fail build if auditwheel segfaults
    auditwheel show "$wheel" 2>/dev/null || echo "WARNING: Could not inspect $(basename $wheel) (non-fatal)"
  done
else
  echo "WARNING: auditwheel not available, copying wheels as-is"
  mkdir -p /io/wheelhouse
  cp dist/*.whl /io/wheelhouse/
fi

# Copy source distribution (only if available)
if ls dist/*.tar.gz 1> /dev/null 2>&1; then
  echo "Copying source distribution"
  cp dist/*.tar.gz /io/wheelhouse/
fi
