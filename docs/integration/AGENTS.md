# AGENTS.md — runtime integration audit contract

This file applies to `docs/integration/`. Root [`../../AGENTS.md`](../../AGENTS.md) remains the repository-wide authority.

## Mandatory read order

For Bettor, Agent Shield, PDF architecture, runtime projection, cross-repository State Machine or Stack work, read:

1. [`../../README.md`](../../README.md)
2. [`../../AGENTS.md`](../../AGENTS.md)
3. [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
4. [`../INDEX.md`](../INDEX.md)
5. [`../architecture/STATE_MACHINES.md`](../architecture/STATE_MACHINES.md)
6. [`README.md`](README.md)
7. [`CROSS_REPO_INTEGRATION.md`](CROSS_REPO_INTEGRATION.md)
8. [`BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md)
9. [`../traceability/TRACEABILITY_INDEX.md`](../traceability/TRACEABILITY_INDEX.md)
10. the exact catalog/module/profile/workload/policy, consumer binding, status ledger, issue and PR.

## Non-negotiable rules

- Treat the PDF as `SOURCE_PROPOSAL`, never as implementation or live evidence.
- `runtime-env` owns secret-free contracts, not Bettor modules or Agent Shield product behavior.
- Compare a consumer binding's source commit/tree with the explicitly intended runtime source before claiming freshness.
- A stale pin is not automatically invalid and must not be silently updated. Run sync dry-run, review, then apply only with explicit approval.
- Do not read or transmit secret values, `.env`, Keychain items, OAuth state, browser profiles, NFC material, private-key shards or provider sessions.
- Do not infer provider readiness from a module declaration, package, direct license, issue, branch or merged foundation contract.
- Preserve `PASS`, `FAIL`, `ABSENT`, `NOT_IMPLEMENTED`, `NOT_EXERCISED`, `SKIPPED_BY_POLICY` and `STALE_SOURCE_PIN` as distinct states.
- Git Town state is repository-owned. `runtime-env` has no admitted `.git-town.toml`; Agent Shield owns the PDF domain-product Stack.
- GitHub PR base/head/merge metadata and exact commits are publication truth. Git Town exit `0` is only branch-movement evidence.
- A terminal leaf owns one provider/product lane. Shared registry/status/release changes belong to the named convergence leaf.

## Required audit packet

```text
source document and page/range
source classification
repository/plane owner
exact current source commit and tree
consumer binding commit/tree/digest
State Machine transition being evaluated
directory owner and public seam
positive evidence
negative or disagreement control
current evidence state
Git Town sibling/child/convergence class when applicable
issue / PR / base / head
remaining gaps
rollback subject and Human action
```

Missing a required field is `ABSENT`; do not reconstruct it from chat history.

## Completion boundary

Before saying “modular integration is complete”, prove all of the following for one immutable subject:

```text
fresh runtime binding
compatible Skill and module closure
Bettor deterministic proof/control/mutation
Agent Shield provider and product canaries
Claude/Codex carrier results
GitHub/Forgejo origin equivalence
cleanup and residue state
aggregate release receipt
Human Admit
rollback subject
```

If any item is missing, report the exact partial state rather than compressing it into PASS.