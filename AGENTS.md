# AGENTS.md — runtime-env operating contract

`runtime-env` is the secret-free **Runtime Contract Plane** in the four-repository modular system. It records names, requirement semantics, safe defaults, profiles, fixed workloads, carrier policies and consumer projections. It never owns credential values, Bettor implementation, Agent Shield product behavior or generic remote execution.

## Mandatory multi-hop read order

1. [`README.md`](README.md) — repository purpose, public CLI and current runtime-contract lifecycle.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership, State Machines and secret boundaries.
4. [`docs/INDEX.md`](docs/INDEX.md) — complete local route map.
5. [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md) and [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).
6. [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md) for requirements → binding → verification.
7. For Bettor, Agent Shield or PDF architecture work, read [`docs/integration/README.md`](docs/integration/README.md), [`docs/integration/AGENTS.md`](docs/integration/AGENTS.md) and [`docs/integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](docs/integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md).
8. The nearest directory `README.md`, then the exact JSON/schema/script/workload/test that owns the task.
9. The exact issue, PR base/head, immutable commit/tree, acceptance tests and evidence subject.

For local Forgejo, credential placement or host capability work, read [`docs/local-integration.md`](docs/local-integration.md) and [`docs/local-credential-broker.md`](docs/local-credential-broker.md). A missing route, owner, contract, profile, workload, host or receipt is `ABSENT`; do not infer it from another repository or a local sibling checkout.

## Common document-route contract

This repository implements the same route names used by `skills-shared`, `bettor-arena` and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/DOCUMENT_ROUTING.md
docs/architecture/STATE_MACHINES.md
docs/integration/README.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
<governed-directory>/README.md
```

README files explain ownership and route to machine authority. They must not duplicate JSON schemas, catalog entries, policies, workload contracts, consumer bindings or receipts.

## Directory and State Machine ownership

| Directory | Owns | Does not own |
|---|---|---|
| `catalog/` | one declaration per variable name and security metadata | provider composition or values |
| `contracts/` | JSON document shape | cross-file runtime semantics by itself |
| `modules/` | provider/runtime requirement sets | workload selection or execution proof |
| `profiles/` | module composition for a workload class | secret values or host execution |
| `workloads/` | fixed entrypoints, allowed environments, mutation class and receipt shape | arbitrary shell commands |
| `policies/` | Claude/Codex/carrier-native isolation projections | credentials, sessions or host approval |
| `src/runtime_env/` | CLI transitions and cross-file invariants | product semantics |
| `scripts/` | bounded bootstrap/install/verification helpers | generic remote execution |
| `examples/` | deterministic generated projections | editable source of truth |
| `tests/` | positive, hollow, mutation and public-seam controls | live-provider truth without a canary |
| `.github-delivery/` | artifact/receipt/publication binding for this repository | implementation correctness or merge authority |
| `docs/integration/` | cross-repository ownership, freshness audit and Stack routing | machine status or provider evidence |

Nearest READMEs provide local details and route to the exact machine owner.

## Core invariants

- A variable name and its security metadata are declared exactly once in `catalog/variables.json`.
- Modules reference variables; profiles compose modules; workloads select fixed entrypoints; policies project carrier settings.
- Secret variables never have committed defaults. Values live in an execution-plane secret store, not this repository.
- Local-first and cloud opt-in profiles remain separate. Missing optional cloud credentials do not fail unrelated local capability.
- `check` and receipts report names/presence/metadata only, never values.
- `workload run` accepts only checked-in fixed entrypoints and exact environment allowlists; no trailing generic command is permitted.
- A module/profile/policy declaration is not execution evidence.
- Consumer pre-commit verification reads the consumer's staged projection only; it does not run `sync`, use the network or depend on a sibling checkout.
- A consumer binding is fresh only against an explicitly named intended source commit/tree. Moving upstream `main` creates a comparison requirement, not automatic permission to rewrite the consumer.

## Consumer lifecycle and freshness

```text
VARIABLE_DECLARED
→ MODULE_VALID
→ PROFILE_RESOLVED
→ WORKLOAD/POLICY_SELECTED
→ SOURCE_COMMIT_AND_TREE_IDENTIFIED
→ SYNC_PLANNED
→ PROJECTION_APPLIED
→ CONSUMER_STAGED_VERIFY
→ CANARY/RECEIPT
→ HUMAN PROMOTION OR ROLLBACK
```

When a binding already exists:

```text
CURRENT_BINDING_READ
→ SOURCE_PIN_COMPARED
├─ MATCH → OFFLINE_VERIFY
└─ DRIFT → STALE_SOURCE_PIN
             → DRY-RUN PLAN
             → HUMAN REVIEW
             → APPLY EXPLICIT OR ACCEPT PIN
```

`sync` is dry-run by default. `--apply` is the only write transition. Rollback and promotion remain consumer/Human-owned.

## Bettor and PDF architecture boundary

The source PDF `科技巨頭開源授權與AI框架v2.pdf` proposes an `agent-shield-monorepo/` product topology. It is not a declaration that `runtime-env` or `bettor-arena` owns those domain services.

At the 2026-08-14 audit snapshot:

```text
runtime-env current main:
  commit 4a333ccf106ef60bc6942b922b7f5efffb3876f5
  tree   68cda3d0ce7f1df26475a5d7322968194e794046

bettor-arena checked runtime binding:
  commit 142e1ed278bf18f9c5c09186e28db16b623cdaee
  tree   1bd5c97e6f5519182d151055cf5f83fccb7ff5fa
```

That relation is `STALE_SOURCE_PIN` relative to current runtime main. Do not call it invalid without running the exact verifier, and do not auto-sync it. Read the audit document for the product/provider status and required transitions.

PDF prose, directory diagrams, direct-license labels, capability claims, percentages and “fully integrated” statements remain `SOURCE_PROPOSAL` until repository decisions, implementation, controls, canaries and receipts independently admit them.

## Four-repository integration

- `skills-shared` declares procedural Skill requirements.
- `runtime-env` resolves the selected secret-free runtime closure.
- `bettor-arena` binds Skill/runtime/module locks and runs proof/control/mutation and stateless MCP acceptance.
- `agent-shield-monorepo` consumes immutable releases as the domain reference consumer and owns PDF-specific product/provider modules.

```text
skills-shared release
+ runtime-env binding/workload/policy
→ Bettor composition/proof/MCP/bootstrap
→ Agent Shield provider/product canaries
→ Bettor external-release acceptance
→ Human promotion or rollback
```

See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Local symlinks, dotenv files, Keychain entries, browser profiles and sibling checkouts are not release identities.

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
STALE_SOURCE_PIN
```

A declaration is not a canary. A workload that did not run because configuration is absent returns its named absence state/exit; it is not PASS. A receipt is a claim and must be bound to the exact source/profile/workload/policy subject.

`STALE_SOURCE_PIN` is an audit state for a consumer projection whose source identity differs from the explicitly intended source. It requires review; it is not silently promoted or normalized.

## Git and Stack boundary

This repository does not admit a repository-owned `.git-town.toml`; do not invent Git Town state.

The PDF domain-product molecular Stack belongs to `agent-shield-monorepo`, whose canonical plan covers:

```text
#38–#44  runtime fabric
#45–#53  product/mobile
#54–#64  security/hardware/settlement
#65–#75  Bettor reference consumer
```

A sibling leaf is path-disjoint work from the same admitted parent. A true child consumes unmerged parent bytes. A terminal leaf owns one provider/product lane. A convergence leaf owns shared registries, status, release manifests and aggregate evidence. Git Town manages branch movement only; GitHub base/head/merge metadata and exact commits remain publication truth.

## Change procedure

1. Identify the exact directory owner and State Machine transition.
2. Add or update a failing public-seam/negative test before changing runtime semantics.
3. Make the smallest catalog/CLI/contract change.
4. Run `bash tests/run-all.sh` and `git diff --check`.
5. Verify generated examples from their producer rather than hand-editing them.
6. Update the nearest README and traceability when ownership, State Machine flow, consumer source identity or cross-repository binding changes.
7. For a consumer projection change, record the prior and new source commit/tree, dry-run diff, staged verifier and rollback subject.

Do not bypass hooks, weaken fixed entrypoints, print values or hand-edit generated consumer projections.

## Source-document boundary

The attached 41-page architecture document is `SOURCE_PROPOSAL`. Its E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, cost, license, performance and recovery claims do not become runtime catalog truth or live PASS without exact independent admission and canaries.

Absolute-security claims are forbidden. Record threat model, controls, disagreement tests, residual risk and exact evidence instead.

## Completion contract

Report before claiming completion:

```text
changed catalog/module/profile/workload/policy IDs
changed State Machine transition and directory owner
consumer binding prior/new commit, tree and digest
freshness decision: MATCH / STALE_SOURCE_PIN / accepted pin / updated pin
consumer projections affected
exact source commit/tree and generated digest changes
positive and negative-control results
host/provider/carrier/product canaries separately
Git Town sibling/child/terminal/convergence class when applicable
remaining ABSENT / NOT_IMPLEMENTED / NOT_EXERCISED / SKIPPED_BY_POLICY
secret-bearing Human steps not performed
rollback subject and Human Admit required
```

Missing an applicable item forbids a claim that modular integration is complete.