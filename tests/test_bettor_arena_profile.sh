#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

actual="$(${ROOT}/runtime-env list --profile bettor-arena-local)"
expected=$'optional\tnon-secret\tOLLAMA_URL\thttp://localhost:11434'

[[ "${actual}" == "${expected}" ]] || {
  echo "FAIL: bettor-arena-local must describe its real bootstrap OLLAMA_URL seam" >&2
  printf 'expected:\n%s\nactual:\n%s\n' "${expected}" "${actual}" >&2
  exit 1
}

echo "PASS: bettor-arena runtime profile"
