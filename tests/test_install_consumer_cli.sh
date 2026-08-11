#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRATCH="$(mktemp -d)"
cleanup() {
  chmod -R u+w "${SCRATCH}" 2>/dev/null || true
  rm -rf "${SCRATCH}"
}
trap cleanup EXIT

PREFIX="${SCRATCH}/prefix"
OUTPUT="$(bash "${ROOT}/scripts/install-consumer-cli.sh" --prefix "${PREFIX}")"

test -x "${PREFIX}/bin/runtime-env"
test -f "${PREFIX}/lib/runtime-env/$(git -C "${ROOT}" rev-parse HEAD)/INSTALL-RECEIPT.json"
grep -Fq "${PREFIX}/bin/runtime-env" <<<"${OUTPUT}"
"${PREFIX}/bin/runtime-env" validate | grep -Fq 'OK catalog:'

# Reinstalling the same immutable revision is idempotent.
bash "${ROOT}/scripts/install-consumer-cli.sh" --prefix "${PREFIX}" >/dev/null
"${PREFIX}/bin/runtime-env" verify-consumer --help >/dev/null

installed="${PREFIX}/lib/runtime-env/$(git -C "${ROOT}" rev-parse HEAD)/runtime-env"
chmod u+w "${installed}"
printf '\n# tampered\n' >> "${installed}"
if bash "${ROOT}/scripts/install-consumer-cli.sh" --prefix "${PREFIX}" >/dev/null 2>&1; then
  echo 'FAIL: installer accepted a modified immutable revision directory' >&2
  exit 1
fi

echo 'PASS: consumer CLI installs immutable committed bytes behind a stable launcher'
