# PRD requirement graph

This directory turns product requirements into a machine-verifiable traceability graph. The human source PRD remains GitHub issue #1; `requirements.json` assigns stable repository IDs to its load-bearing acceptance requirements and records how each requirement is implemented and falsified.

## Authority

```text
GitHub PRD / admitted source requirement
→ stable REQ-* ID in requirements.json
→ directory + State Machine owner
→ implementation subjects
→ issue / Stack leaf / PR lineage
→ positive control
→ disagreement / negative control
→ optional exact live evidence
→ CONTRACT_CLOSED | LIVE_CLOSED | PARTIAL
```

`requirements.json` is not an implementation SSOT. Machine authority remains in `catalog/`, `contracts/`, `modules/`, `profiles/`, `workloads/`, `policies/`, `src/`, `scripts/`, `tests/`, and exact receipts. This graph only binds why those subjects exist and what evidence ceiling has been reached.

## Closure laws

- `CONTRACT_CLOSED` requires repository implementation subjects, at least one positive control, and at least one disagreement/negative control.
- `LIVE_CLOSED` additionally requires at least one exact live evidence subject. CI or fixtures alone cannot satisfy it.
- `PARTIAL` names an implemented or planned requirement whose required evidence is incomplete.
- GitHub issue `closed` is delivery metadata, not a closure state by itself.
- New scope receives a new stable requirement ID. Do not silently repurpose an old requirement ID.
- Every repository-relative path named by the graph must exist in the checked tree.

## Validation

```bash
python3 tests/check_prd_traceability.py
bash tests/test_prd_traceability.sh
```

`tests/run-all.sh` automatically discovers the shell test. The planted controls prove duplicate IDs, missing implementation paths, and `LIVE_CLOSED` without live evidence turn red.

## Update procedure

1. Identify the source PRD/issue acceptance item.
2. Allocate a stable `REQ-*` ID.
3. Name its directory owner and State Machine transition.
4. Bind current implementation paths and issue/PR lineage.
5. Bind positive and negative/disagreement controls.
6. Set the honest closure state and live-evidence requirement.
7. Run the full suite and update the Shadow Architect ledger if the evidence ceiling changes.
