# Shadow Architect current closure ledger

> Observation time: 2026-08-17 23:29 Asia/Taipei  
> Repository: `ed3c/runtime-env`  
> Convergence owner: issue #50

This is an evidence ledger, not a second implementation SSOT.

## Current verdict

```text
Runtime Contract Plane                  IMPLEMENTED
Public repository / v0.1.0             PUBLISHED
Deterministic contract controls         MOSTLY CLOSED
Current main GitHub Actions             FAIL at observed HEAD
GitHub monitor live acceptance (#37)    PARTIAL / NOT_EXERCISED
Forgejo exact-host acceptance (#38)     PARTIAL / NOT_EXERCISED
Multi-Worker live consumer (#45)        PARTIAL / NOT_EXERCISED
Cross-repo/PDF end-to-end integration   PARTIAL
Operational completion                  NOT CLOSED
```

At the start of this pass, `main` was `6eaae8b8d31fd867dd933a3266024ff7a5e35ce3`; CI run #94 failed while prior main `77dca3584a4adb1c463c815bdb5ab603eae32b23` passed. The connector exposed exit code `1` but not enough failing-test log to prove a root cause. Independently observed freshness drift: delivery metrics still represented issue #4 as open although GitHub #4 is closed, and the publication attestation still carries `export-tree-drift` / `open-delivery-slices`. Treat this as a freshness defect to verify, not as a fabricated CI diagnosis.

## Closure classification

```text
GitHub CLOSED + deterministic controls only → CONTRACT_CLOSED
GitHub CLOSED + required exact live canary + receipt → LIVE_CLOSED
GitHub OPEN + implementation present but live missing → PARTIAL / NOT_EXERCISED
```

GitHub issue state is publication metadata, not runtime evidence.

## #37 — read-only GitHub monitor

Implemented: module/profile/workload, allowlisted registry, bounded metadata snapshot adapter, exact compiler binding, receipt path, deterministic tests, no-write authority boundary.

Remaining:

```text
admitted repository
→ real read-only GitHub fetch
→ pagination + rate metadata
→ normalized snapshot validation
→ offline replay / byte stability
→ blocker transition determinism
→ provider/rate failure preserves prior admitted plan
→ duplicate suppression
→ scheduler handoff packet
→ zero writes / zero secret leak / zero residue
```

State: `PARTIAL`; live acceptance remains `NOT_EXERCISED`.

## #38 — Forgejo host lifecycle

Implemented: exact version/digest binding, platform checks, loopback config, collision refusal, install/check/health commands, backup identity, restore-check, upgrade/rollback planning and negative controls.

Remaining:

```text
exact admitted host
→ activate real Forgejo service
→ status + health readback
→ credential-helper compatibility canary
→ backup
→ restore drill
→ controlled upgrade path
→ rollback receipt
→ identity re-check
→ zero unintended repo-local state
```

State: `PARTIAL`; exact-host PASS remains `NOT_EXERCISED`.

## #45 — bounded multi-Worker scheduler

Implemented: typed reducer, leases, heartbeats, expiry, budgets, checkpoint identity, stale classification, retry lineage, straggler semantics, subprocess/worktree synthetic canary, interruption/resume and cleanup checks.

Remaining:

```text
admitted exact consumer
→ two path-disjoint concurrent Workers
→ exact linked worktrees + process identities
→ checkpoint/resume
→ stale/expired real result refusal
→ straggler detach + reassignment
→ exact budget reconciliation
→ verified prerequisite convergence
→ zero active lease/process/worktree residue
→ replayable receipt
```

State: `PARTIAL`; admitted-consumer PASS remains `NOT_EXERCISED`.

## Article / PDF closure rule

```text
SOURCE_PROPOSAL
→ owner plane
→ directory + State Machine
→ issue
→ implementation
→ positive + disagreement controls
→ exact provider/product canary
→ consumer integration canary
→ release evidence
→ Human Admit / rollback
```

Article/PDF prose, diagrams, package presence or licensing claims never become live PASS by themselves.

## Freshness defects found

1. Root README still says the repository is private although GitHub is public and `v0.1.0` is published.
2. Delivery metrics/attestations are point-in-time snapshots and can be stale relative to GitHub issue/HEAD state.
3. Directory READMEs often omit upstream/downstream DAG ownership and evidence ceiling.
4. Root `AGENTS.md` lacks a mandatory current Shadow Architect ledger route.
5. Current main CI is red; current-head completion cannot be claimed.

## Closure DAG

```text
current-head CI/freshness
          │
          ├──────────────┬──────────────┐
          ▼              ▼              ▼
      #37 live        #38 live        #45 live
          │              │              │
          └──────────────┴──────────────┘
                         ▼
               #50 shared convergence
                         ▼
       README / AGENTS / index / ledger refresh
                         ▼
              exact current-head CI PASS
                         ▼
             applicable live receipts PASS
                         ▼
             zero residue + rollback bound
                         ▼
                    Human Admit
```

## Stop conditions

Refuse a completion claim when current-head CI is not PASS, source identity is ambiguous, a fixture proxies live evidence, a closed issue proxies runtime evidence, a receipt predates material subject changes, cleanup is unmeasured, or Human-only destructive/secret-bearing authority remains required.
