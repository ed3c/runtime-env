# `tests/`

Owner: public-seam, regression, hollow, mutation, schema, consumer-sync, workload, credential-broker, carrier-policy, repository-safety and bounded runtime controls.

## Verification State Machine

```text
EXACT_SUBJECT_SELECTED
→ POSITIVE_CONTROL
→ DISAGREEMENT / NEGATIVE_CONTROL
→ RESULT_BOUND_TO_SUBJECT
→ DETERMINISTIC_VERDICT
→ LIVE_CANARY_REQUIRED? ── yes → NOT_EXERCISED until exact live receipt
                         └─ no  → CONTRACT_CLOSED candidate
```

`bash tests/run-all.sh` is the aggregate deterministic suite. Fixtures prove deterministic behavior only; they do not proxy a real provider, account, browser, device, service, consumer repository or Human promotion.

## DAG position

```text
catalog/module/profile/workload/script change
→ matching focused test
→ aggregate run-all.sh
→ GitHub Actions exact-head run
→ exact host/provider/consumer canary when applicable
→ receipt + residue check
→ convergence
```

## Evidence classes

| Test subject | May prove | Must not prove |
|---|---|---|
| schema/fixture | contract shape/reducer behavior | provider availability |
| synthetic process/worktree | scheduler mechanics | admitted-consumer PASS |
| fake GitHub/Forgejo | failure/normalization controls | real provider identity |
| exact live canary | one named live subject | unrelated product/release correctness |
| current-head Actions | checked commit deterministic suite | local host/Forgejo/session state |

A skipped optional provider remains named separately from PASS. A closed issue with only deterministic tests is `CONTRACT_CLOSED`, not automatically `LIVE_CLOSED`.

Current live terminal issues are #37, #38 and #45. Shared current-head/freshness convergence is #50. Read `docs/architecture/SHADOW_ARCHITECT_LEDGER.md` before closing or promoting any of these lanes.