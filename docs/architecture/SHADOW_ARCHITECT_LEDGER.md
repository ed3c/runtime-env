# Shadow Architect current closure ledger

> Observation time: 2026-08-18 00:28 Asia/Taipei  
> Repository: `ed3c/runtime-env`  
> Convergence owner: issue #50

This is an evidence ledger, not a second implementation SSOT.

## Current verdict

```text
Runtime Contract Plane                  IMPLEMENTED
Public repository / v0.1.0             PUBLISHED
Deterministic current-head CI           PASS at last admitted main
CI safety/freshness repair (#51)        CONTRACT_CLOSED
PRD requirement graph (#54)             IMPLEMENTED ON PR #55 / CI REQUIRED
GitHub monitor live acceptance (#37)    PARTIAL / NOT_EXERCISED / REOPENED
Forgejo exact-host acceptance (#38)     PARTIAL / NOT_EXERCISED
Multi-Worker live consumer (#45)        PARTIAL / NOT_EXERCISED
Cross-repo/PDF end-to-end integration   PARTIAL
Operational completion                  NOT CLOSED
```

## PRD traceability lane — #54

PRD #1 previously had a human-readable acceptance checklist but no stable machine-verifiable requirement IDs. PR #55 adds:

```text
prd/requirements.json
contracts/prd-requirements.schema.json
tests/check_prd_traceability.py
tests/test_prd_traceability.sh
prd/README.md + prd/AGENTS.md
```

The six original PRD #1 acceptance requirements are now assigned `REQ-PRD-001` through `REQ-PRD-006` and bind directory/State Machine owner, repository implementation paths, issue/PR lineage, positive controls, disagreement controls, live-evidence requirement and closure state.

Planted controls require duplicate IDs, missing implementation paths and `LIVE_CLOSED` without exact live evidence to turn red. #54 may become `CONTRACT_CLOSED` only after exact PR-head CI passes and the routing docs are admitted. It cannot close or promote #37/#38/#45.

## #37 closure correction

#37 was found closed while its latest evidence still explicitly classified it `CONTRACT_IMPLEMENTED / LIVE_NOT_EXERCISED`; no later exact live receipt was present. The issue was therefore reopened during this Shadow Architect pass. This is a governance correction, not a regression in its deterministic implementation.

## Current-head CI closure

The earlier pass started with `main@6eaae8b8d31fd867dd933a3266024ff7a5e35ce3` failing CI run #94. The exact failing seam was proven: `scripts/publish_v0_1_0.sh` tracked a maintainer-specific `/Users/...` path while `tests/check_tracked_text.py` intentionally rejects host-account paths in the public tree.

Issue #51 / PR #52 replaced that path with explicit host-owned `GITHUB_DELIVERY_SCRIPT` binding and fail-closed validation.

```text
PR #52 head d928edf0bfa14b7c4e6d01c44a476dd77192b228
→ CI run #95 PASS
→ merged main cd92685459d60064c5b1bf31ebeda5784d51c120
→ main CI run #97 PASS
→ PR #53 convergence merged main 3cf0118f3ada21d91d7e692f3938d1d47e59d0e5
```

#51 is `CONTRACT_CLOSED`. It does not close any live lane. Every new head, including PR #55 and any later merge, still requires its own exact CI result.

Delivery metrics/attestations remain point-in-time snapshots. If their timestamp/commit predates material GitHub state, classify them as stale evidence and compare them with current provider truth rather than rewriting historical release identity.

## Closure classification

```text
GitHub CLOSED + deterministic controls only → CONTRACT_CLOSED at most
GitHub CLOSED + required exact live canary + receipt → LIVE_CLOSED
GitHub OPEN + implementation present but live missing → PARTIAL / NOT_EXERCISED
```

GitHub issue state is publication metadata, not runtime evidence.

## #37 — read-only GitHub monitor

Implemented: module/profile/workload, allowlisted registry, bounded metadata snapshot adapter, exact compiler binding, content-addressed run identity, overlap lock, duplicate suppression, prior-state preservation, scheduler-review handoff, deterministic tests, no-write authority boundary.

Remaining:

```text
admitted repository
→ real read-only GitHub fetch
→ pagination + rate metadata
→ normalized snapshot validation
→ offline replay / byte stability
→ blocker transition determinism
→ provider/rate failure preserves prior admitted plan
→ scheduler handoff packet readback
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
→ stable REQ-* identity when admitted
→ owner plane
→ directory + State Machine
→ issue / molecular leaf
→ implementation
→ positive + disagreement controls
→ exact provider/product canary
→ consumer integration canary
→ release evidence
→ Human Admit / rollback
```

Article/PDF prose, diagrams, package presence or licensing claims never become live PASS by themselves.

## Residual closure DAG

```text
#54 PRD graph ──────────┐
#37 live monitor ───────┤
#38 live Forgejo ───────┼─→ #50 convergence → exact current-head verification → Human Admit / rollback
#45 live scheduler ─────┘
```

#54 is connector/CI-completable. #37/#38/#45 require exact runtime/provider/host subjects and remain open unless those receipts are actually obtained.

## Stop conditions

Refuse a completion claim when a requirement lacks a stable traceability route, source identity is ambiguous, a fixture proxies live evidence, a closed issue proxies runtime evidence, a receipt predates material subject changes, cleanup is unmeasured, current-head CI is not PASS, or Human-only destructive/secret-bearing authority remains required.
