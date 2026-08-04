#!/usr/bin/env bash
# ==============================================================================
# Script Name: rebuild_python_with_ssl.sh
# Description: Download, compile, and install CPython with SSL enabled
# Scope/Safety: High risk / Requires sudo to install dependencies and run make install
# Dependencies: curl, tar, make, sudo, dnf (on Fedora)
# ==============================================================================

set -euo pipefail

# Configuration-driven settings
PY_VER=3.13.14
PREFIX=/home/cable/local
if [ -f ".devin/hooks.json" ] && command -v jq &> /dev/null; then
  PY_VER=$(jq -r '.environment.pythonInstallVersion // "3.13.14"' .devin/hooks.json)
  PREFIX=$(jq -r '.environment.installPrefix // "/home/cable/local"' .devin/hooks.json)
fi

NUMJOBS=$(nproc || echo 1)

# Check dependencies
for cmd in curl tar make sudo; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: Required dependency '$cmd' is not installed or not in PATH." >&2
    exit 1
  fi
done

echo "Detected OS: $(. /etc/os-release && echo $NAME $VERSION_ID)"

# Install build dependencies (Fedora 43)
sudo dnf install -y @development-tools \
  openssl-devel bzip2-devel xz-devel readline-devel sqlite-devel gdbm-devel libffi-devel libuuid-devel zlib-devel wget curl

# Download and build
cd /tmp
if [ ! -f Python-${PY_VER}.tgz ]; then
  curl -LO https://www.python.org/ftp/python/${PY_VER}/Python-${PY_VER}.tgz
fi
rm -rf Python-${PY_VER}
tar xzf Python-${PY_VER}.tgz
cd Python-${PY_VER}

# Configure
./configure --prefix=${PREFIX} --enable-optimizations --with-ensurepip=install
make -j"${NUMJOBS}"
# Install (may write to ${PREFIX})
sudo make install

# Post-install guidance
cat <<EOF
Python ${PY_VER} installed to ${PREFIX}.
Next steps (operator):
  - Recreate or point virtualenvs to ${PREFIX}/bin/python3.13
  - Reinstall project dependencies in a fresh venv:
      ${PREFIX}/bin/python3.13 -m venv /home/cable/venv
      /home/cable/venv/bin/pip install -U pip
      /home/cable/venv/bin/pip install -r requirements.txt
  - Verify SSL:
      /home/cable/venv/bin/python -c "import ssl; print(ssl.OPENSSL_VERSION)"
EOF

exit 0
