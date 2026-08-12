# AGENTS.md — runtime-env operating contract

`runtime-env` is the secret-free **Runtime Contract Plane** in the four-repository modular system. It records names, requirement semantics, safe defaults, profiles, fixed workloads, carrier policies, and consumer projections. It never owns credential values, product behavior, or generic remote execution.

## Mandatory multi-hop read order

1. [`README.md`](README.md) — repository purpose, public CLI, and current runtime-contract lifecycle.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership, state machines, and secret boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — complete local route map.
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md) and [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).
6. [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md) for requirements → binding → verification.
7. The nearest directory `README.md`, then the exact JSON/schema/script/workload/test that owns the task.
8. The exact issue, PR base/head, acceptance tests, and evidence subject.

For local Forgejo, credential placement, or host capability work, read [`docs/local-integration.md`](docs/local-integration.md) and [`docs/local-credential-broker.md`](docs/local-credential-broker.md). A missing route, owner, contract, profile, workload, host, or receipt is `ABSENT`; do not infer it from another repository or a local sibling checkout.

## Common document-route contract

This repository implements the same route names used by `skills-shared`, `bettor-arena`, and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

README files explain ownership and route to machine authority. They must not duplicate JSON schemas, catalog entries, policies, workload contracts, consumer bindings, or receipts.

## Directory and state-machine ownership

| Directory | Owns | Does not own |
|---|---|---|
| `catalog/` | one declaration per variable name and security metadata | provider composition or values |
| `contracts/` | JSON document shape | cross-file runtime semantics by itself |
| `modules/` | provider/runtime requirement sets | workload selection or execution proof |
| `profiles/` | module composition for a workload class | secret values or host execution |
| `workloads/` | fixed entrypoints, allowed environments, mutation class, receipt shape | arbitrary shell commands |
| `policies/` | Claude/Codex/carrier-native isolation projections | credentials, sessions, or host approval |
| `src/runtime_env/` | CLI transitions and cross-file invariants | product semantics |
| `scripts/` | bounded bootstrap/install/verification helpers | generic remote execution |
| `examples/` | deterministic generated projections | editable source of truth |
| `tests/` | positive, hollow, mutation, and public-seam controls | live provider truth without a canary |
| `.github-delivery/` | artifact/receipt/publication binding for this repository | implementation correctness or merge authority |

Nearest READMEs provide local details and route to the exact machine owner.

## Core invariants

- A variable name and its security metadata are declared exactly once in `catalog/variables.json`.
- Modules reference variables; profiles compose modules; workloads select fixed entrypoints; policies project carrier settings.
- Secret variables never have committed defaults. Values live in an execution-plane secret store, not this repository.
- Local-first and cloud opt-in profiles remain separate. Missing optional cloud credentials do not fail unrelated local capability.
- `check` and receipts report names/presence/metadata only, never values.
- `workload run` accepts only checked-in fixed entrypoints and exact environment allowlists; no trailing generic command is permitted.
- A module/profile/policy declaration is not execution evidence.
- Consumer pre-commit verification reads the consumer's staged projection only; it does not run `sync`, use the network, or depend on a sibling checkout.

## Consumer lifecycle

```text
VARIABLE_DECLARED
→ MODULE_VALID
→ PROFILE_RESOLVED
→ WORKLOAD/POLICY_SELECTED
→ SYNC_PLANNED
→ PROJECTION_APPLIED
→ CONSUMER_STAGED_VERIFY
→ CANARY/RECEIPT
→ HUMAN PROMOTION OR ROLLBACK
```

`sync` is dry-run by default. `--apply` is the only write transition. Rollback and promotion remain consumer/Human-owned.

## Four-repository integration

- `skills-shared` declares procedural Skill requirements.
- `runtime-env` resolves the selected secret-free runtime closure.
- `bettor-arena` binds Skill/runtime/module locks and runs proof/control/mutation and stateless MCP acceptance.
- `agent-shield-monorepo` consumes immutable releases as the domain reference consumer.

See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Local symlinks, dotenv files, Keychain entries, browser profiles, and sibling checkouts are not release identities.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A declaration is not a canary. A workload that did not run because configuration is absent returns its named absence state/exit; it is not PASS. A receipt is a claim and must be bound to the exact source/profile/workload/policy subject.

## Git and Stack boundary

This repository does not currently admit a repository-owned `.git-town.toml`; do not invent Git Town state. Documentation issue `ed3c/runtime-env#29` is an independent sibling in the four-repository documentation stack. If Git Town is introduced later, it must document sibling versus true-child branches, terminal leaves, convergence leaves, no-push synchronization, and Human-owned conflict/merge/promotion.

## Change procedure

1. Identify the exact directory owner and state transition.
2. Add or update a failing public-seam/negative test before changing runtime semantics.
3. Make the smallest catalog/CLI/contract change.
4. Run `bash tests/run-all.sh` and `git diff --check`.
5. Verify generated examples from their producer rather than hand-editing them.
6. Update nearest README and traceability when ownership, state flow, or cross-repository binding changes.

Do not bypass hooks, weaken fixed entrypoints, print values, or hand-edit generated consumer projections.

## Source-document boundary

The attached 41-page architecture document is `SOURCE_PROPOSAL`. Its E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, cost, license, performance, and recovery claims do not become runtime catalog truth or live PASS without exact independent admission and canaries.

## Completion contract

Report before claiming completion:

```text
changed catalog/module/profile/workload/policy IDs
changed state-machine transition and directory owner
consumer bindings/projections affected
exact source commit/tree and generated digest changes
positive and negative-control results
host/provider/carrier canaries separately
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
secret-bearing Human steps not performed
rollback subject and Human Admit required
```
