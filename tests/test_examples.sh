#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

compare_example() {
  local profile="$1"
  local path="${ROOT}/examples/${profile}.dotenv.example"
  diff -u "${path}" <("${ROOT}/runtime-env" render --profile "${profile}" --format dotenv)
}

compare_example skill-bettor-e2b
compare_example skill-bettor-local
compare_example skill-bettor-sandbox-browser-cloud
compare_example forgejo-delivery-local-password
compare_example forgejo-delivery-local-api

echo "PASS: committed examples match catalog projections"
