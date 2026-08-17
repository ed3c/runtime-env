#!/usr/bin/env bash
# runtime-env issue #4 unpark steps 2-3: v0.1.0 release + post-flip sync.
# Idempotent: skips the release if the tag already exists; sync re-derives
# state from the observed remote, so re-running is safe.
set -euo pipefail

REPO=ed3c/runtime-env
COMMIT=648d474e7cc06bbd00b2b1ec626cd0df78f1ef87
TREE=e214062dadb825c5f135a5299b27e6893c6f8fe4
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYNC=/Users/neon/.claude/skills/github-delivery-loop/scripts/github_delivery.py

gh_clean() { env -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u http_proxy -u ALL_PROXY -u all_proxy gh "$@"; }

# Preconditions: repo must be observed PUBLIC and the released commit must exist.
vis=$(gh_clean repo view "$REPO" --json visibility -q .visibility)
[ "$vis" = "PUBLIC" ] || { echo "FATAL: $REPO visibility is $vis, not PUBLIC — the owner flip is the gate" >&2; exit 1; }
git -C "$ROOT" cat-file -e "$COMMIT^{commit}" || { echo "FATAL: released commit missing locally" >&2; exit 1; }
[ "$(git -C "$ROOT" rev-parse "$COMMIT^{tree}")" = "$TREE" ] || { echo "FATAL: tree sha mismatch" >&2; exit 1; }

if gh_clean release view v0.1.0 --repo "$REPO" >/dev/null 2>&1; then
  echo "OK: release v0.1.0 already exists — skipping creation"
else
  gh_clean release create v0.1.0 --repo "$REPO" --target "$COMMIT" \
    --title "v0.1.0 — first public release" \
    --notes "First credential-free public release of the runtime-env environment contract (issue #4).

Released subject: commit $COMMIT, tree $TREE, 198 files, MIT.
Pre-flip audit evidence: tree audit #31/#32, credential scanner + CI run 31800651206 on 9a142b7, attestation re-verification #34.
Consumers pin by SHA/tag per docs/public-consumption.md."
  echo "OK: release v0.1.0 created at $COMMIT"
fi

env -u HTTPS_PROXY -u https_proxy -u HTTP_PROXY -u http_proxy -u ALL_PROXY -u all_proxy \
python3 "$SYNC" sync \
  --registry "$ROOT/.github-delivery/registry.json" \
  --line runtime-contracts --github \
  --metrics "$ROOT/.github-delivery/metrics/runtime-contracts.json" \
  --dashboard "$ROOT/.github-delivery/dashboard.md" \
  --export-source-commit "$COMMIT" \
  --export-tree-sha "$TREE"

# Post-assertion: the attestation must now say PUBLIC before we call this done.
python3 - "$ROOT/.github-delivery/publications/runtime-contracts.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["visibility"] == "PUBLIC", f"attestation still says {d['visibility']}"
assert "human-visibility-gate" not in d.get("blockers", []), d.get("blockers")
print("ASSERT OK: attestation visibility=PUBLIC, human-visibility-gate cleared")
print("remaining blockers:", d.get("blockers", []))
PY
echo "DONE — commit the .github-delivery/ changes and close #4 citing this run."
