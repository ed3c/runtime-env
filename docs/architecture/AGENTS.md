# AGENTS.md — architecture and Shadow Architect monitor

This file governs `docs/architecture/`. Root `../../AGENTS.md` remains repository-wide authority.

## Mandatory read order

1. `../../README.md`
2. `../../AGENTS.md`
3. `../../CONTEXT.md`
4. `../../ARCHITECTURE.md`
5. `../INDEX.md`
6. `README.md`
7. `STATE_MACHINES.md`
8. `SHADOW_ARCHITECT_LEDGER.md`
9. nearest directory README
10. exact issue / PR / commit / Actions run / receipt

## Shadow Architect monitor contract

For every completion, integration, issue-closing, article/PDF audit, runtime provider or Stack PR task, build this packet before making a claim:

```text
source problem / claim
classification
repository plane owner
directory owner
State Machine transition
DAG parents and children
issue number
Stack class: sibling | true child | terminal | convergence
PR base/head or planned branch
exact commit/tree
positive control
disagreement/negative control
live canary requirement
live receipt identity
cleanup/residue result
current-head CI result
closure state
rollback subject
Human authority still required
```

Missing an applicable field is `ABSENT` or `NOT_EXERCISED`; do not infer it from issue state, chat history, package presence, a diagram or another repository.

## Tech Lead issue audit

Review each issue using two independent axes:

```text
implementation axis: ABSENT → CONTRACT_IMPLEMENTED → CONTRACT_CLOSED
runtime axis:        NOT_EXERCISED → LIVE_CANARY → LIVE_CLOSED
```

A GitHub issue may be closed while runtime axis remains `NOT_EXERCISED`. When that happens, do not manufacture PASS; route the live gap to the existing terminal owner or convergence issue.

## Molecular Stack laws

- Use terminal leaves for one provider/runtime lane and its directly coupled tests.
- Use convergence leaves for shared README/AGENTS/index/status/release changes.
- Use a true child only when it consumes unmerged parent bytes.
- Otherwise terminal leaves are siblings from the same admitted base.
- GitHub base/head/commit metadata is publication truth; Git Town branch movement is not correctness evidence.
- A terminal leaf must not edit another terminal lane's implementation or aggregate release state.
- If a new real gap has no owner, create an issue before adding it to the Stack index.

Current convergence owner is #50. Current terminal live owners are #37, #38 and #45. A current-head CI/freshness repair becomes its own terminal child/sibling only after the exact failing seam is proven.

## Article/PDF rule

Treat every external architecture claim as `SOURCE_PROPOSAL` until it maps to a directory owner, State Machine, issue, implementation, controls and exact live evidence. Absolute-security and unsupported completion claims are forbidden.

## Completion stop conditions

Do not say complete when:

- current main CI is red or not checked for the claimed SHA;
- the only evidence is deterministic fixture output for a live lane;
- delivery snapshots predate material GitHub state changes;
- cleanup/residue is unmeasured;
- rollback is absent for destructive/upgrade transitions;
- a consumer binding is stale or ambiguous;
- Human-only credential, visibility, merge, destructive migration or promotion authority remains unperformed.
