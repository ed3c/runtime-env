# AGENTS.md — PRD traceability contract

`prd/` owns requirement identity and traceability only. It does not own runtime implementation semantics or live evidence.

## Mandatory read order

1. root `AGENTS.md`;
2. `prd/README.md`;
3. `prd/requirements.json`;
4. `contracts/prd-requirements.schema.json`;
5. `tests/check_prd_traceability.py` and `tests/test_prd_traceability.sh`;
6. the requirement's named directory owner and exact issue/PR/evidence subjects.

## Laws

- Stable `REQ-*` IDs are append-only identities. Do not reuse an ID for changed scope.
- Every requirement must name a repository directory and State Machine transition.
- Every closed contract requirement must bind implementation subjects plus positive and disagreement/negative controls.
- `LIVE_CLOSED` requires exact subject-bound live evidence. Fixtures, CI, issue state, declarations, or another runtime cannot proxy it.
- Repository paths in the graph are relative, checked-tree subjects; no host-local absolute paths are admitted.
- Secret values, cookies, tokens, browser/session material, private issue bodies, and private chain of thought are forbidden.
- GitHub issue/PR numbers are lineage metadata. Machine correctness remains in repository bytes and exact receipts.

When implementation or evidence changes, update the graph only after the owning subject is admitted. A traceability edit must never promote #37/#38/#45 or any provider/host lane beyond its exact evidence ceiling.
