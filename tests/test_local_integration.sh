#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${ROOT}/docs/local-integration.md"
REQUIREMENTS="${ROOT}/docs/integration-requirements.md"

grep -Fq 'docs/local-integration.md' "${ROOT}/AGENTS.md" || {
  echo "FAIL: AGENTS.md does not route agents to the local integration contract" >&2
  exit 1
}

[[ -f "${DOC}" ]] || {
  echo "FAIL: local integration contract is absent" >&2
  exit 1
}

grep -Fq 'docs/integration-requirements.md' "${DOC}" || {
  echo "FAIL: local integration contract does not route agents to completion requirements" >&2
  exit 1
}

[[ -f "${REQUIREMENTS}" ]] || {
  echo "FAIL: integration completion requirements are absent" >&2
  exit 1
}

for required in \
  'Integration maturity levels' \
  'Consumer repository acceptance' \
  'Live acceptance matrix' \
  'consumer repository must not create its own `.env`' \
  'BLOCKED'; do
  grep -Fq "${required}" "${REQUIREMENTS}" || {
    echo "FAIL: integration completion requirements omitted ${required}" >&2
    exit 1
  }
done

for required in \
  '/Users/neon/runtime-env' \
  '/Users/neon/runtime-env/.env' \
  './runtime-env local-env doctor' \
  '~/.config/runtime-env/secrets/forgejo-local.env' \
  'scripts/verify-local-runtime.sh' \
  '`AGENTS.md` is loaded only when a new chat starts' \
  'must not print credential values'; do
  grep -Fq "${required}" "${DOC}" || {
    echo "FAIL: local integration contract omitted ${required}" >&2
    exit 1
  }
done

[[ -x "${ROOT}/scripts/verify-local-runtime.sh" ]] || {
  echo "FAIL: local runtime verifier is absent or not executable" >&2
  exit 1
}

scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT
fake_bin="${scratch}/bin"
mkdir -p "${fake_bin}" "${scratch}/home"
ln -s "${ROOT}" "${scratch}/canonical"

cat > "${fake_bin}/git" <<'FAKEGIT'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == "credential fill" ]]; then
  cat >/dev/null
  [[ "${FAKE_GIT_MODE:-present}" != missing ]] || exit 1
  printf 'protocol=http\nhost=localhost:3000\nusername=fixture-user\npassword=%s\n' "${FAKE_SECRET}"
  exit 0
fi
if [[ "$*" == "config --get-all credential.http://localhost:3000.helper" ]]; then
  if [[ "${FAKE_HELPER_MODE:-keychain}" == store ]]; then
    printf '%s\n' store
  else
    printf '\n%s\n' osxkeychain
  fi
  exit 0
fi
echo "unexpected fake git invocation: $*" >&2
exit 2
FAKEGIT
chmod 755 "${fake_bin}/git"

cat > "${fake_bin}/curl" <<'FAKECURL'
#!/usr/bin/env bash
set -euo pipefail
[[ $# -ge 3 && "$1" == "-q" && "$2" == "--noproxy" && "$3" == "*" ]] || {
  echo "curl canary did not disable curlrc/proxy" >&2
  exit 2
}
if [[ "$*" == *"/api/v1/version"* ]]; then
  [[ "${FAKE_VERSION_MODE:-reachable}" != unreachable ]] || exit 7
  printf '%s\n' '{"version":"9.0.3-fixture"}'
  exit 0
fi
if [[ "${4:-}" == "--config" && "${5:-}" == "-" ]]; then
  config="$(cat)"
  [[ "${config}" == *"${FAKE_SECRET}"* ]] || {
    echo "credential did not reach authenticated canary" >&2
    exit 2
  }
  [[ "${FAKE_AUTH_MODE:-accepted}" != refused ]] || exit 22
  printf '%s\n' '{"login":"fixture-user"}'
  exit 0
fi
echo "unexpected fake curl invocation: $*" >&2
exit 2
FAKECURL
chmod 755 "${fake_bin}/curl"

sentinel='fixture-secret-DO-NOT-LEAK'
mkdir -p "${scratch}/different-root"
set +e
HOME="${scratch}/home" bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/absent" \
  >"${scratch}/canonical-absent.out" 2>"${scratch}/canonical-absent.err"
canonical_absent_status=$?
HOME="${scratch}/home" bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/different-root" \
  >"${scratch}/canonical-drift.out" 2>"${scratch}/canonical-drift.err"
canonical_drift_status=$?
set -e
[[ ${canonical_absent_status} -eq 3 ]]
[[ ${canonical_drift_status} -eq 2 ]]
grep -q "ABSENT canonical runtime checkout" "${scratch}/canonical-absent.err"
grep -q "DRIFT verifier root" "${scratch}/canonical-drift.err"

set +e
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  bash -x "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" \
  >"${scratch}/helper.out" 2>"${scratch}/helper.err"
helper_status=$?
set -e
[[ ${helper_status} -eq 0 ]]
grep -q "AUTHENTICATED Forgejo credential via git credential helper" "${scratch}/helper.out"
grep -q "LOCAL-RUNTIME GREEN" "${scratch}/helper.out"
if grep -Fq "${sentinel}" "${scratch}/helper.out" "${scratch}/helper.err"; then
  echo "FAIL: verifier leaked helper credential under bash -x" >&2
  exit 1
fi

HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" --credential-helper-only \
  >"${scratch}/helper-only.out" 2>"${scratch}/helper-only.err"
grep -q "AUTHENTICATED Forgejo credential via git credential helper" \
  "${scratch}/helper-only.out"

set +e
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_HELPER_MODE=store bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" --credential-helper-only \
  >"${scratch}/store-helper.out" 2>"${scratch}/store-helper.err"
store_helper_status=$?
set -e
[[ ${store_helper_status} -eq 2 ]]
grep -q "REFUSED Forgejo helper chain is not URL-scoped osxkeychain" \
  "${scratch}/store-helper.err"

set +e
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_GIT_MODE=missing bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" \
  >"${scratch}/missing.out" 2>"${scratch}/missing.err"
missing_status=$?
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_VERSION_MODE=unreachable bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" \
  >"${scratch}/unreachable.out" 2>"${scratch}/unreachable.err"
unreachable_status=$?
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_AUTH_MODE=refused bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" \
  >"${scratch}/refused.out" 2>"${scratch}/refused.err"
refused_status=$?
set -e
[[ ${missing_status} -eq 3 ]]
[[ ${unreachable_status} -eq 4 ]]
[[ ${refused_status} -eq 1 ]]

fallback="${scratch}/forgejo-local.env"
printf '%s\n' \
  'FORGEJO_URL=http://localhost:3000' \
  'FORGEJO_USERNAME=fixture-user' \
  "FORGEJO_PASSWORD=${sentinel}" > "${fallback}"
chmod 600 "${fallback}"
set +e
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_GIT_MODE=missing bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" --env-file "${fallback}" \
  --credential-helper-only \
  >"${scratch}/helper-only-missing.out" 2>"${scratch}/helper-only-missing.err"
helper_only_missing_status=$?
set -e
[[ ${helper_only_missing_status} -eq 3 ]]
grep -q "MISSING Forgejo credential: helper empty" \
  "${scratch}/helper-only-missing.err"
if grep -q "dotenv fallback" \
  "${scratch}/helper-only-missing.out" "${scratch}/helper-only-missing.err"; then
  echo "FAIL: helper-only canary used the dotenv fallback" >&2
  exit 1
fi

HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_GIT_MODE=missing bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" --env-file "${fallback}" \
  >"${scratch}/fallback.out" 2>"${scratch}/fallback.err"
grep -q "AUTHENTICATED Forgejo credential via explicit dotenv fallback" "${scratch}/fallback.out"
if grep -Fq "${sentinel}" "${scratch}/fallback.out" "${scratch}/fallback.err"; then
  echo "FAIL: verifier leaked fallback credential" >&2
  exit 1
fi

chmod 644 "${fallback}"
set +e
HOME="${scratch}/home" PATH="${fake_bin}:${PATH}" FAKE_SECRET="${sentinel}" \
  FAKE_GIT_MODE=missing bash "${ROOT}/scripts/verify-local-runtime.sh" \
  --canonical-path "${scratch}/canonical" --env-file "${fallback}" \
  >"${scratch}/unsafe.out" 2>"${scratch}/unsafe.err"
unsafe_status=$?
set -e
[[ ${unsafe_status} -eq 2 ]]
grep -q "UNSAFE fallback mode 0644" "${scratch}/unsafe.err"

echo "PASS: Agent-readable local integration contract"
