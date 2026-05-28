#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export REPO_ROOT
export LD_LIBRARY_PATH="${REPO_ROOT}/../raisim/linux/lib:${LD_LIBRARY_PATH:-}"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate cms
fi

cd "${REPO_ROOT}"
echo "eval env ready: REPO_ROOT=${REPO_ROOT}"
