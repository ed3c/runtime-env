#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "${SCRATCH}"' EXIT

PREFIX="${SCRATCH}/prefix"
OUTPUT="$(bash "${ROOT}/scripts/install-consumer-cli.sh" --prefix "${PREFIX}")"

test -x "${PREFIX}/bin/runtime-env"
test -f "${PREFIX}/lib/runtime-env/$(git -C "${ROOT}" rev-parse HEAD)/INSTALL-RECEIPT.json"
grep -Fq "${PREFIX}/bin/runtime-env" <<<"${OUTPUT}"
"${PREFIX}/bin/runtime-env" validate | grep -Fq 'OK catalog:'

# Reinstalling the same immutable revision is idempotent.
bash "${ROOT}/scripts/install-consumer-cli.sh" --prefix "${PREFIX}" >/dev/null
"${PREFIX}/bin/runtime-env" verify-consumer --help >/dev/null

echo 'PASS: consumer CLI installs immutable committed bytes behind a stable launcher'
