#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 tests/dual_agent_runtime_docs_selftest.py
printf '%s\n' 'PASS: dual-agent runtime docs and Stack trace'
