#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/activate_eval_env.sh"

CONFIG="${1:-eval_suite/config/eval_full.yaml}"

python -m eval_suite.morphology.build_variant_pool --mode symmetric --num_variants "${POOL_SIZE:-64}" --seed 42
python -m eval_suite.morphology.build_variant_pool --mode full_asym --num_variants "${POOL_SIZE:-64}" --seed 42
python -m eval_suite.runners.run_all --config "${CONFIG}"
