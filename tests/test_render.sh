#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

e2b_dotenv="$(${ROOT}/runtime-env render --profile skill-bettor-e2b --format dotenv)"
[[ "${e2b_dotenv}" == *$'E2B_API_KEY='* ]] || {
  echo "FAIL: E2B profile did not render E2B_API_KEY" >&2
  exit 1
}
[[ "${e2b_dotenv}" != *"e2b_"* ]] || {
  echo "FAIL: rendered dotenv contains a secret-looking E2B value" >&2
  exit 1
}

local_dotenv="$(${ROOT}/runtime-env render --profile skill-bettor-local --format dotenv)"
[[ "${local_dotenv}" == *"OLLAMA_BASE_URL=http://127.0.0.1:11434/v1"* ]] || {
  echo "FAIL: local profile lost its Ollama default" >&2
  exit 1
}

gemini_dotenv="$(${ROOT}/runtime-env render --profile skill-bettor-gemini --format dotenv)"
[[ "${gemini_dotenv}" == *$'NL_PROVIDER=gemini'* ]] || {
  echo "FAIL: Gemini profile does not select the Gemini provider" >&2
  exit 1
}
[[ "${gemini_dotenv}" == *$'NL_MODEL=google/gemini-2.0-flash'* ]] || {
  echo "FAIL: Gemini profile does not select its verified model default" >&2
  exit 1
}
[[ "${local_dotenv}" != *"API_KEY"* ]] || {
  echo "FAIL: local-zero-key profile unexpectedly requires a cloud key" >&2
  exit 1
}

actions="$(${ROOT}/runtime-env render --profile skill-bettor-e2b --format github-actions)"
[[ "${actions}" == *'E2B_API_KEY: ${{ secrets.E2B_API_KEY }}'* ]] || {
  echo "FAIL: GitHub Actions output did not map the E2B secret" >&2
  exit 1
}

all_dotenv="$(${ROOT}/runtime-env render --all --format dotenv)"
for expected in E2B_API_KEY GEMINI_API_KEY OPENAI_API_KEY APPLITOOLS_API_KEY NGC_API_KEY; do
  [[ "${all_dotenv}" == *"${expected}="* ]] || {
    echo "FAIL: all-variable render omitted ${expected}" >&2
    exit 1
  }
done

echo "PASS: deterministic secret-free rendering seam"
