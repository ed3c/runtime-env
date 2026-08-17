# `workloads/`

Owner: fixed executable entrypoints, allowed environments, mutation/control classes, and receipt locations.

## State Machine

```text
WORKLOAD_SELECTED
→ PROFILE_RESOLVED
→ REQUIRED_NAMES_PRESENT
→ EXACT_ENVIRONMENT_BUILT
→ FIXED_ENTRYPOINT_EXECUTED
→ PRIVATE_METADATA_RECEIPT
```

Terminal states include invalid contract, required configuration absent/not-run, fixed entrypoint failure, timeout, bounded control failure and PASS for the exact subject.

## DAG position and data flow

```text
profile + policy + exact host/consumer subject
→ workload contract
→ src/runtime_env transition guard
→ fixed script/entrypoint
→ metadata-only receipt
→ tests / live canary readback
→ convergence decision
```

| Input | Output | Evidence owner | Evidence ceiling |
|---|---|---|---|
| profile + fixed entrypoint + allowlist | exact execution request | `src/runtime_env/` + `scripts/` | one bounded invocation |
| host/provider state | receipt with names/metadata only | exact canary owner | does not proxy downstream product correctness |

No trailing arbitrary command is allowed. Missing configuration is an explicit not-run state, not PASS. Live credentials and sessions remain host/provider owned.

## Molecular implementation lanes

Current terminal live lanes route through workload contracts but close only on exact subjects:

- #37 repository-control-plane monitor → real read-only GitHub fetch receipt.
- #38 Forgejo host lifecycle → exact-host activation/health/restore/rollback receipts.
- #45 multi-Worker scheduler → admitted-consumer concurrency/stale/straggler/budget/residue receipt.

A workload PR owns one bounded execution lane. Shared aggregate status or cross-lane release changes belong to #50 convergence.

Read `docs/architecture/README.md` and `docs/architecture/SHADOW_ARCHITECT_LEDGER.md` before interpreting a workload as operationally complete.