#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC="${ROOT}/docs/runtimes/forgejo-localhost.md"

[[ -f "${DOC}" ]] || {
  echo "FAIL: Forgejo localhost placement guide is absent" >&2
  exit 1
}

for required in \
  'catalog/variables.json' \
  'modules/forgejo-local-*.json' \
  'profiles/forgejo-delivery-local-*.json' \
  'examples/forgejo-delivery-local-password.dotenv.example' \
  '~/.config/runtime-env/secrets/forgejo-local.env' \
  '~/Library/Keychains/login.keychain-db' \
  '~/.git-credentials' \
  '<forgejo-repo>/.git/config' \
  'http://localhost:3000/user/settings/applications' \
  'current Chrome profile' \
  'git credential fill' \
  './runtime-env local-env migrate-forgejo-keychain' \
  'forgejo-delivery-loop' \
  'FORGEJO_URL' \
  'FORGEJO_USERNAME' \
  'FORGEJO_PASSWORD' \
  'FORGEJO_TOKEN' \
  'reserves the `FORGEJO_`, `GITHUB_`, and' \
  'current Forgejo 9.0.3 instance'; do
  grep -Fq "${required}" "${DOC}" || {
    echo "FAIL: Forgejo guide omitted path or seam: ${required}" >&2
    exit 1
  }
done

echo "PASS: Forgejo localhost placement paths"
