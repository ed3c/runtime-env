# `.github-delivery/`

Owner: this repository's delivery registry, implementation receipt, metrics snapshot and publication attestation.

## State Machine

```text
TRACKED_ARTIFACT
→ DELIVERY_RECEIPT_VALID
→ GITHUB_STATE_OBSERVED
→ PUBLICATION_ATTESTATION
→ SUBJECT_FRESHNESS_COMPARED
→ CURRENT_SUBJECT_VERIFIED
```

## DAG position and data flow

```text
implementation / tests / merged publication state
→ registry + metrics + receipt + publication attestation
→ compare with current GitHub issue/PR/release/HEAD truth
→ freshness verdict
→ Shadow Architect convergence
```

Delivery evidence binds identities and publication state. It does **not** prove runtime correctness, GitHub Actions execution, host/provider canaries, merge authority, GitHub/Forgejo equivalence or production promotion.

## Freshness law

Every file here is a point-in-time subject. A later GitHub issue close, PR merge, release, visibility change or main commit can make a previously valid snapshot stale without making the old JSON malformed.

```text
SNAPSHOT_VALID + SUBJECT_MOVED → STALE_EVIDENCE
STALE_EVIDENCE → REFRESH / COMPARE
REFRESHED_CURRENT_SUBJECT + REQUIRED CONTROLS → eligible convergence input
```

Never use `metrics.json`, a receipt, or an attestation as current truth without checking its `fetched_at`/`verified_at`, commit/tree and current GitHub state.

Current convergence owner: issue #50. Current exact-head CI and live issues #37/#38/#45 remain separate evidence lanes. See `docs/architecture/SHADOW_ARCHITECT_LEDGER.md`.