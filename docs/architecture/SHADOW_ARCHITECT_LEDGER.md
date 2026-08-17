# Shadow Architect current closure ledger

> Observation time: 2026-08-17 23:39 Asia/Taipei  
> Repository: `ed3c/runtime-env`  
> Convergence owner: issue #50

This is an evidence ledger, not a second implementation SSOT.

## Current verdict

```text
Runtime Contract Plane                  IMPLEMENTED
Public repository / v0.1.0             PUBLISHED
Deterministic current-head CI           PASS
CI safety/freshness repair (#51)        CONTRACT_CLOSED
GitHub monitor live acceptance (#37)    PARTIAL / NOT_EXERCISED
Forgejo exact-host acceptance (#38)     PARTIAL / NOT_EXERCISED
Multi-Worker live consumer (#45)        PARTIAL / NOT_EXERCISED
Cross-repo/PDF end-to-end integration   PARTIAL
Operational completion                  NOT CLOSED
```

## Current-head CI closure

The pass started with `main@6eaae8b8d31fd867dd933a3266024ff7a5e35ce3` failing CI run #94. The exact failing seam was later proven: `scripts/publish_v0_1_0.sh` tracked a maintainer-specific `/Users/...` path while `tests/check_tracked_text.py` intentionally rejects host-account paths in the public tree.

Issue #51 / PR #52 replaced that path with explicit host-owned `GITHUB_DELIVERY_SCRIPT` binding and fail-closed validation.

```text
PR #52 head d928edf0bfa14b7c4e6d01c44a476dd77192b228
→ CI run #95 PASS
→ merged main cd92685459d60064c5b1bf31ebeda5784d51c120
→ main CI run #97 PASS
```

The Shadow Architect documentation branch was then merged with repaired main; its head `75382a50a0799a73de7f71b2658ce38009a71ea0` passed CI run #98. #51 is therefore `CONTRACT_CLOSED`. It does not close any live lane.

Delivery metrics/attestations remain point-in-time snapshots. If their timestamp/commit predates material GitHub state, classify them as stale evidence and compare them with current provider truth rather than rewriting historical release identity.

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

## Documentation defects addressed by PR #53

- root README public/private truth corrected;
- directory READMEs now name upstream/downstream DAG ownership and evidence ceilings;
- architecture README adds molecular Stack index and closure states;
- architecture AGENTS adds mandatory Shadow Architect / Tech Lead audit packet;
- docs index routes Agents through the current ledger;
- delivery README makes point-in-time freshness explicit.

## Residual closure DAG

```text
#37 live monitor ───────┐
#38 live Forgejo ───────┼─→ #50 convergence → exact current-head verification → Human Admit / rollback
#45 live scheduler ─────┘
```

The deterministic CI repair is no longer a residual dependency. Operational closure now depends on the exact live receipts, cleanup/residue checks and any cross-repository acceptance required by the claimed capability.

## Stop conditions

Refuse a completion claim when source identity is ambiguous, a fixture proxies live evidence, a closed issue proxies runtime evidence, a receipt predates material subject changes, cleanup is unmeasured, current-head CI is not PASS, or Human-only destructive/secret-bearing authority remains required.
