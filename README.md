# runtime-env

`runtime-env` is the secret-free **Runtime Contract Plane** for agent repositories. It records names, requirement semantics, safe defaults, profiles, fixed workloads, carrier policies and consumer projections. It never stores credential values and never treats a declaration as live execution evidence.

The repository is **public**. `v0.1.0` was published on 2026-08-17 from commit `648d474e7cc06bbd00b2b1ec626cd0df78f1ef87`. Consumers should pin an exact commit SHA; a tag alone is not sufficient immutability authority.

> **Agent route:** read [`AGENTS.md`](AGENTS.md) → [`CONTEXT.md`](CONTEXT.md) → [`ARCHITECTURE.md`](ARCHITECTURE.md) → [`prd/README.md`](prd/README.md) → [`prd/requirements.json`](prd/requirements.json) → [`docs/INDEX.md`](docs/INDEX.md) → [`docs/architecture/README.md`](docs/architecture/README.md) → [`docs/architecture/AGENTS.md`](docs/architecture/AGENTS.md) → [`docs/architecture/SHADOW_ARCHITECT_LEDGER.md`](docs/architecture/SHADOW_ARCHITECT_LEDGER.md) → nearest directory README/AGENTS → exact issue/PR/commit/test/receipt.

## Requirement → implementation traceability

PRD #1 and later admitted requirements are bound through stable `REQ-*` IDs in [`prd/requirements.json`](prd/requirements.json):

```text
PRD requirement
→ stable REQ-* identity
→ directory + State Machine owner
→ implementation subjects
→ issue / molecular Stack leaf / PR lineage
→ positive control
→ disagreement / negative control
→ exact live evidence when required
→ CONTRACT_CLOSED | LIVE_CLOSED | PARTIAL
```

The graph is checked by `tests/check_prd_traceability.py` and planted disagreement controls. A closed GitHub issue cannot substitute for this evidence chain, and `LIVE_CLOSED` cannot be represented without an exact live evidence subject.

## What this repository separates

```text
variable declaration
→ module requirements
→ profile composition
→ workload + carrier policy
→ typed runtime reducer
→ fixed host/provider adapter
→ deterministic controls
→ exact live canary when required
→ delivery evidence
→ Human Admit / rollback
```

No arrow may be skipped. In particular:

```text
module exists ≠ provider installed
profile resolves ≠ workload executed
test PASS ≠ live provider PASS
issue closed ≠ operational closure
publication receipt ≠ runtime correctness
```

## Directory → State Machine → DAG → data flow

| Directory | State Machine responsibility | DAG input | Output / next owner | Evidence ceiling |
|---|---|---|---|---|
| [`prd/`](prd/README.md) | `SOURCE_REQUIREMENT → REQ_ID → OWNER/CONTROL BINDING → CLOSURE_CLASS` | PRD/issue requirement | traceability graph → exact owner/evidence | traceability only |
| [`catalog/`](catalog/README.md) | `UNDECLARED → METADATA_VALIDATED → VARIABLE_DECLARED` | source/runtime requirement | canonical variable vocabulary → modules | declaration only |
| [`contracts/`](contracts/README.md) | document-shape validation | JSON subject | schema verdict | shape only |
| [`modules/`](modules/README.md) | `MODULE_REQUESTED → REFERENCES_RESOLVED → MODULE_VALID` | catalog variables | provider/runtime requirement unit → profiles | declared, not live |
| [`profiles/`](profiles/README.md) | `PROFILE_SELECTED → MODULES_RESOLVED → PROFILE_RESOLVED` | modules | portable composition → workloads/policies | composition only |
| [`workloads/`](workloads/README.md) | `WORKLOAD_SELECTED → EXACT_ENV → FIXED_ENTRYPOINT → RECEIPT` | profile + exact subject | bounded execution → scripts/runtime | one exact invocation |
| [`policies/`](policies/README.md) | carrier-native isolation projection | carrier requirement | secret-free carrier policy | projection only |
| [`src/runtime_env/`](src/runtime_env/README.md) | typed reducers and cross-file invariants | declarative planes | validation/render/check/sync/workload decisions | deterministic semantics |
| [`scripts/`](scripts/README.md) | bounded host/provider/process/worktree transitions | fixed workload inputs | metadata-only receipts | exact adapter invocation |
| [`examples/`](examples/README.md) | generated projection | source closure | secret-free examples | no authority |
| [`tests/`](tests/README.md) | positive/disagreement/negative controls | exact subject | deterministic verdict | fixture unless live subject |
| [`.github-delivery/`](.github-delivery/README.md) | artifact → receipt → publication → freshness | tracked artifact + GitHub state | publication evidence | publication only |
| [`docs/integration/`](docs/integration/README.md) | source claim → owner → evidence state | PDF/article/cross-repo requirement | integration audit | documentation/audit only |

The full DAG and molecular Stack index are in [`docs/architecture/README.md`](docs/architecture/README.md).

## Current Shadow Architect closure

Current convergence owner: **issue #50**.

```text
main / convergence
├─ #37 read-only GitHub monitor live closure
├─ #38 Forgejo exact-host lifecycle live closure
├─ #45 admitted-consumer multi-Worker live closure
└─ #54 PRD requirement graph / traceability closure
```

The Runtime Contract Plane and public release exist. Current-head CI must remain green, and #37/#38/#45 retain their exact live receipt requirements. Read [`docs/architecture/SHADOW_ARCHITECT_LEDGER.md`](docs/architecture/SHADOW_ARCHITECT_LEDGER.md) for the mutable current assessment rather than inferring readiness from issue state.

## Molecular Stack PR rule

`runtime-env` does not claim a repository-owned `.git-town.toml`. The implementation topology still follows `git-town-stacked-pr-worker` laws:

```text
same admitted base
├─ terminal leaf #37  GitHub monitor
├─ terminal leaf #38  Forgejo host lifecycle
├─ terminal leaf #45  scheduler runtime
└─ terminal leaf #54  PRD requirement graph
        ↓
#50 convergence owns shared README / AGENTS / index / aggregate evidence
```

Use a **true child PR only when it consumes unmerged parent bytes**. Otherwise terminal leaves are siblings. GitHub base/head/commit metadata is publication truth; Git Town branch movement is not correctness evidence.

## Quick start

```bash
./runtime-env validate
./runtime-env list --kind profiles
./runtime-env render --profile skill-bettor-e2b --format dotenv
./runtime-env check --profile skill-bettor-e2b --env-file .env
./runtime-env workload list
./runtime-env local-env init
./runtime-env local-env doctor
python3 tests/check_prd_traceability.py
```

Exit codes are public contract:

| Exit | Meaning |
|---:|---|
| `0` | contract/result PASS for the exact deterministic subject |
| `2` | invalid catalog/profile/arguments/input |
| `3` | required configuration absent; workload did not run |

`check` prints names/presence only. `workload run` accepts only checked-in fixed entrypoints and exact environment allowlists; there is no trailing arbitrary command surface.

## Consumer synchronization

The portable consumer lifecycle is defined in [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md).

```bash
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root /path/to/bettor-arena

# dry-run by default; explicit write only:
./runtime-env sync ... --apply

# read-only freshness check:
./runtime-env sync ... --check
```

Generated consumer files pin source repository, commit and tree. Consumer pre-commit verifies its staged projection only; it must not invoke sync, use the network or depend on a sibling checkout.

Public consumption and pinning rules are in [`docs/public-consumption.md`](docs/public-consumption.md).

## Secrets and execution planes

Secret variables never have committed defaults. Values belong to the execution plane:

| Execution plane | Value owner |
|---|---|
| developer machine | untracked mode-0600 dotenv, OS Keychain or provider CLI keyring |
| GitHub Actions | repository/environment secrets; prefer OIDC where applicable |
| cloud execution | that environment's secret store |
| dedicated host | host secret manager/service environment |

A GitHub or ChatGPT connector is authorization/tooling, not proof of a local shell, Forgejo daemon, browser session or worker process. Do not add generic shell-over-MCP.

Local credential isolation and broker behavior are documented in [`docs/local-credential-broker.md`](docs/local-credential-broker.md). Runtime-plane distinctions are in [`docs/runtime-topology.md`](docs/runtime-topology.md).

## Forgejo / repository control plane

Forgejo credentials remain Keychain/secret-store owned; portable receipts contain metadata only. Host lifecycle, Git Town toolchain, GitHub monitor and scheduler are separate evidence lanes.

Read:

- [`docs/local-integration.md`](docs/local-integration.md)
- [`docs/runtimes/forgejo-localhost.md`](docs/runtimes/forgejo-localhost.md)
- [`scripts/README.md`](scripts/README.md)
- issues #37, #38, #45 and convergence #50

A healthy Forgejo service does not prove Git Town Stack correctness, GitHub reconciliation, Actions success, semantic integration, merge or promotion.

## Source articles / PDF architecture

External architecture documents are `SOURCE_PROPOSAL`:

```text
claim
→ owner plane
→ directory + State Machine
→ issue
→ implementation
→ positive + disagreement controls
→ exact provider/product canary
→ consumer integration
→ release evidence
→ Human Admit / rollback
```

The referenced `科技巨頭開源授權與AI框架v2.pdf` does not make E2B/Firecracker, OpenShell/tmux, mobile, wallet, security, settlement, cost, licensing, performance or recovery claims live truth. Cross-repository audit routing is under [`docs/integration/`](docs/integration/README.md).

## Evidence states

Use these without normalization:

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

A GitHub `CLOSED` issue is not a runtime evidence state.

## Development

```bash
bash tests/run-all.sh
git diff --check
```

Before claiming completion, require exact current-head CI plus all applicable live receipts and cleanup/residue evidence. See [`AGENTS.md`](AGENTS.md), [`prd/AGENTS.md`](prd/AGENTS.md), and [`docs/architecture/AGENTS.md`](docs/architecture/AGENTS.md).