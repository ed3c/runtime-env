# AGENTS.md — runtime-env operating contract

`runtime-env` is the secret-free **Runtime Contract Plane** in the four-repository modular system. It records names, requirement semantics, safe defaults, profiles, fixed workloads, carrier policies and consumer projections. It never owns credential values, Bettor implementation, Agent Shield product behavior or generic remote execution.

## Mandatory multi-hop read order

1. [`README.md`](README.md) — repository purpose, public CLI and current runtime-contract lifecycle.
2. [`CONTEXT.md`](CONTEXT.md) — mutable current handoff and four-repository relationship.
3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — stable ownership, State Machines and secret boundaries.
4. [`prd/README.md`](prd/README.md), [`prd/AGENTS.md`](prd/AGENTS.md) and [`prd/requirements.json`](prd/requirements.json) — stable PRD requirement IDs and machine-verifiable requirement → owner → implementation → control → evidence routing.
5. [`docs/INDEX.md`](docs/INDEX.md) — complete local route map.
6. [`docs/architecture/README.md`](docs/architecture/README.md), [`docs/architecture/AGENTS.md`](docs/architecture/AGENTS.md), [`docs/architecture/SHADOW_ARCHITECT_LEDGER.md`](docs/architecture/SHADOW_ARCHITECT_LEDGER.md), [`docs/architecture/DOCUMENT_ROUTING.md`](docs/architecture/DOCUMENT_ROUTING.md) and [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).
7. [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md) for requirements → binding → verification.
8. For Bettor, Agent Shield or PDF architecture work, read [`docs/integration/README.md`](docs/integration/README.md), [`docs/integration/AGENTS.md`](docs/integration/AGENTS.md) and [`docs/integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](docs/integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md).
9. The nearest directory `README.md`/`AGENTS.md`, then the exact JSON/schema/script/workload/test that owns the task.
10. The exact issue, PR base/head, immutable commit/tree, acceptance tests and evidence subject.

Before claiming a PRD requirement complete, resolve its `REQ-*` entry in `prd/requirements.json`. A GitHub closed issue, merged PR, fixture PASS or declaration cannot substitute for the graph's named machine authority and applicable exact evidence.

For local Forgejo, credential placement or host capability work, read [`docs/local-integration.md`](docs/local-integration.md) and [`docs/local-credential-broker.md`](docs/local-credential-broker.md). A missing route, owner, contract, profile, workload, host or receipt is `ABSENT`; do not infer it from another repository or a local sibling checkout.

## Common document-route contract

This repository implements the same route names used by `skills-shared`, `bettor-arena` and `agent-shield-monorepo`:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
prd/README.md
prd/AGENTS.md
prd/requirements.json
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
| `prd/` | stable requirement identity and traceability bindings | runtime implementation truth or live evidence by itself |
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

## PRD traceability invariants

- Every load-bearing admitted product requirement has one stable `REQ-*` identity.
- A requirement binds one source item, directory/State Machine owner, implementation subjects, issue/PR lineage, positive controls and disagreement/negative controls.
- Repository-relative paths named by the graph must exist in the checked tree.
- `CONTRACT_CLOSED` requires implementation subjects plus positive and disagreement controls.
- `LIVE_CLOSED` additionally requires exact subject-bound live evidence. Deterministic CI, fixtures, issue state and another runtime cannot proxy it.
- Scope changes get new requirement IDs rather than silently repurposing historical identities.
- `tests/check_prd_traceability.py` and `tests/test_prd_traceability.sh` are mandatory disagreement controls for the graph.

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

The immutable runtime contract implementation baseline evaluated by the 2026-08-14 audit is:

```text
runtime-env implementation baseline:
  commit 4a333ccf106ef60bc6942b922b7f5efffb3876f5
  tree   68cda3d0ce7f1df26475a5d7322968194e794046

bettor-arena checked runtime binding:
  commit 142e1ed278bf18f9c5c09186e28db16b623cdaee
  tree   1bd5c97e6f5519182d151055cf5f83fccb7ff5fa
```

Later `runtime-env/main` commits may update audit documentation without changing the contract semantics under comparison. The checked Bettor binding remains `STALE_SOURCE_PIN` relative to the evaluated implementation baseline. Do not call it invalid without running the exact verifier, and do not auto-sync it. Read the audit document for the product/provider status and required transitions.

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
CONTRACT_CLOSED
LIVE_CLOSED
PARTIAL
```

A declaration is not a canary. A workload that did not run because configuration is absent returns its named absence state/exit; it is not PASS. A receipt is a claim and must be bound to the exact source/profile/workload/policy subject.

`STALE_SOURCE_PIN` is an audit state for a consumer projection whose source identity differs from the explicitly intended source. It requires review; it is not silently promoted or normalized.

## Git and Stack boundary

This repository does not admit a repository-owned `.git-town.toml`; do not invent Git Town state.

The local `runtime-env` convergence Stack currently includes terminal live leaves #37/#38/#45 and governance/traceability leaf #54 under convergence #50. A sibling leaf is path-disjoint work from the same admitted parent. A true child consumes unmerged parent bytes. A terminal leaf owns one provider/product/runtime/governance lane. A convergence leaf owns shared registries, status, release manifests and aggregate evidence. Git Town manages branch movement only; GitHub base/head/merge metadata and exact commits remain publication truth.

The PDF domain-product molecular Stack belongs to `agent-shield-monorepo`, whose canonical plan covers:

```text
#38–#44  runtime fabric
#45–#53  product/mobile
#54–#64  security/hardware/settlement
#65–#75  Bettor reference consumer
```

## Change procedure

1. Resolve the applicable `REQ-*` requirement when the change implements or changes product scope.
2. Identify the exact directory owner and State Machine transition.
3. Add or update a failing public-seam/negative test before changing runtime semantics.
4. Make the smallest catalog/CLI/contract change.
5. Run `bash tests/run-all.sh` and `git diff --check`.
6. Verify generated examples from their producer rather than hand-editing them.
7. Update the nearest README/AGENTS, PRD graph and traceability when ownership, State Machine flow, consumer source identity or cross-repository binding changes.
8. For a consumer projection change, record the prior and new source commit/tree, dry-run diff, staged verifier and rollback subject.

Do not bypass hooks, weaken fixed entrypoints, print values or hand-edit generated consumer projections.

## Source-document boundary

The attached 41-page architecture document is `SOURCE_PROPOSAL`. Its E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, cost, license, performance and recovery claims do not become runtime catalog truth or live PASS without exact independent admission and canaries.

Absolute-security claims are forbidden. Record threat model, controls, disagreement tests, residual risk and exact evidence instead.

## Completion contract

Report before claiming completion:

```text
applicable REQ-* IDs and requirement closure states
changed catalog/module/profile/workload/policy IDs
changed State Machine transition and directory owner
issue / Stack leaf / PR lineage
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

Missing an applicable item forbids a claim that modular integration or the named PRD requirement is complete.

<!-- BEGIN SKILLS-SHARED INSTRUCTION PROJECTION -->
## Shared runtime / delivery projection

Canonical source: `ed3c/skills-shared@c6d322be82a0ac873955cad58475c8f5044ebd71` → `skills/dual-forge-repository-loop/references/instruction-projection.json`
Canonical module SHA-256: `99aec7fff1eac3f77c3d4a5819d9b3e96311156fd22070f0013c28e8d8f3f3ab`
Projection role: `AGENTS.md` — Cross-host repository entrypoint. Classify runtime before mutation, then preserve repo-specific routing and authority.

Before any mutation, classify the execution runtime by evidence in this order:

1. trusted explicit AGENT_RUNTIME/AGENT_HOST override
2. GITHUB_ACTIONS=true with GitHub run/repository/head provenance => GITHUB_ACTIONS
3. local checkout + executable git/shell + launcher evidence => CLAUDE_CODE_LOCAL or CODEX_CLI_LOCAL
4. Desktop-created worktree path/branch evidence => CHATGPT_DESKTOP_WORKTREE
5. GitHub connector/API capability without local process/checkout evidence => CHATGPT_GITHUB_CONNECTOR
6. otherwise => UNKNOWN

Mandatory laws:

- Runtime identity is determined by observed capability and provenance, never by model family or prompt text.
- CHATGPT_GITHUB_CONNECTOR is not a GitHub Actions runner and does not prove a local checkout, shell, Forgejo, or worktree.
- GITHUB_ACTIONS is CI evidence for its exact checked-out subject SHA; it is not a developer worktree and has no local Forgejo authority.
- Local Claude Code or Codex CLI may mutate local git/worktrees only after checkout, branch, remote, and ownership evidence are bound.
- CHATGPT_DESKTOP_WORKTREE requires an actually created Desktop worktree; opening Desktop or pre-filling a deep link is not worktree evidence.
- UNKNOWN fails closed for irreversible delivery actions.
- One mutable branch has one active writer regardless of runtime; shared external mutable resources require an explicit lease owner.
- Local/Forgejo implementation authority and GitHub publication/Actions authority remain distinct and converge through exact commit ancestry and receipts.
- Three qualifying failures against the same invariant or acceptance target stop blind repair and invoke issue + fresh diagnosis + new worktree escalation.
- Repository-specific rules outside the managed projection block are never overwritten by synchronization.
- AGENTS.md is the cross-host repository procedure; repo CLAUDE.md is a Claude host adapter; global ~/.claude/CLAUDE.md is local host policy only.
- Cloud and local freshness are separate evidence lanes. Neither environment may fabricate verification of the other.
- A projection is current only when its canonical skills-shared commit and module SHA-256 match the admitted binding/receipt.
- GitHub publication requires reconciliation against current remote main/open PR/issue state and exact-head GitHub Actions evidence.

Do not edit this managed block manually. Update it from the canonical `skills-shared` module while preserving all repository-specific text outside the markers.
<!-- END SKILLS-SHARED INSTRUCTION PROJECTION -->
