# Runtime integration route

This directory owns the documentation route from `runtime-env` contracts to consumer projections and downstream product evidence. It does not own credential values, provider sessions, Bettor implementation, Agent Shield product code, or Human promotion.

## Current verdict

The architecture described in `科技巨頭開源授權與AI框架v2.pdf` is **not fully integrated**.

What exists today:

- `runtime-env` implements the secret-free variable/module/profile/workload/policy contract plane;
- `bettor-arena` contains a generated runtime projection and deterministic Integration / Acceptance mechanisms;
- `agent-shield-monorepo` has admitted the provider-neutral runtime SPI foundation;
- most PDF-specific local/cloud/mobile/security/settlement providers remain `NOT_IMPLEMENTED` or `NOT_EXERCISED`;
- the Bettor projection is pinned to an older `runtime-env` source than current `main`, so integration freshness is not PASS.

Read [`BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md) for exact subjects and requirements.

## Directory → State Machine → data ownership

| Directory | State Machine responsibility | Input | Output / evidence | Must not own |
|---|---|---|---|---|
| [`../../catalog/`](../../catalog/README.md) | `UNDECLARED → METADATA_VALIDATED → VARIABLE_DECLARED` | variable name and security metadata | canonical variable declaration | values or provider execution |
| [`../../contracts/`](../../contracts/README.md) | document-shape validation | JSON document | schema agreement/disagreement | cross-file runtime semantics by itself |
| [`../../modules/`](../../modules/README.md) | `MODULE_REQUESTED → VARIABLE_REFERENCES_RESOLVED → MODULE_VALID` | variable references and provider requirement set | validated module closure | workload choice or live canary |
| [`../../profiles/`](../../profiles/README.md) | `PROFILE_COMPOSITION_REQUESTED → DEFAULTS_CONFLICT_CHECKED → PROFILE_RESOLVED` | selected modules | portable profile closure | host secret material |
| [`../../workloads/`](../../workloads/README.md) | `WORKLOAD_DECLARED → ENTRYPOINT_SELECTED → EXACT_ENVIRONMENT_BUILT → EXECUTED` | fixed entrypoint, profile, exact environment-name allowlist | private metadata receipt and named exit | arbitrary shell or caller-selected command |
| [`../../policies/`](../../policies/README.md) | carrier-policy projection | Claude/Codex/provider policy selection | secret-free native policy document | login/session approval |
| [`../../src/runtime_env/`](../../src/runtime_env/README.md) | cross-document reducers and transition guards | catalog + module + profile + workload + policy | validation, render, check, workload and sync decisions | consumer product semantics |
| [`../../scripts/`](../../scripts/README.md) | bounded bootstrap, broker and verification transitions | admitted fixed arguments | metadata-only result/receipt | generic remote execution |
| [`../../examples/`](../../examples/README.md) | deterministic generated projection | resolved source closure | recomputable `.env.example` and mappings | editable canonical truth |
| [`../../tests/`](../../tests/README.md) | positive, hollow, mutation and public-seam control | exact source subject | falsifiable test result | live-provider truth without canary |
| [`../../.github-delivery/`](../../.github-delivery/README.md) | `ARTIFACT_PRESENT → DELIVERY_RECEIPT_VALID → PUBLICATION_ATTESTED` | tracked artifact and publication metadata | exact publication subject | implementation or merge authority |

## Contract and consumer data flow

```text
PDF/source requirement
  → classify as SOURCE_PROPOSAL
  → assign product owner and runtime requirement names
  → catalog variable declaration
  → module requirement set
  → profile composition
  → fixed workload + carrier policy
  → runtime-env validation
  → explicit sync dry-run
  → secret-free Bettor projection
  → Bettor staged offline verification
  → Bettor module/composition/proof subject
  → Agent Shield provider/product canary
  → Bettor external-release acceptance
  → Human promotion or rollback
```

A transition on the left cannot proxy a transition on the right. In particular:

```text
valid catalog ≠ fresh consumer binding
fresh binding ≠ provider execution
provider execution ≠ product integration
product canary ≠ production promotion
```

## Consumer freshness State Machine

```text
REQUIREMENTS_RECEIVED
→ SOURCE_COMMIT_AND_TREE_IDENTIFIED
→ CURRENT_BINDING_READ
→ SOURCE_PIN_COMPARED
├─ MATCH → OFFLINE_VERIFY
└─ DRIFT → SYNC_PLAN_REQUIRED
             → REVIEW
             → APPLY_EXPLICIT
             → STAGED_OFFLINE_VERIFY
             → CANARY / RECEIPT
             → HUMAN PROMOTION OR ROLLBACK
```

`sync` remains dry-run by default. An Agent must not silently update `.runtime-env/` merely because upstream `main` moved.

## Git Town and molecular Stack ownership

`runtime-env` has no admitted repository-owned `.git-town.toml`. Do not invent local parent metadata. The PDF domain-product Stack is canonical in `ed3c/agent-shield-monorepo`, which does have Git Town policy and a molecular implementation DAG.

```text
Phase 3 Runtime
main
└─ #38 runtime SPI foundation                  MERGED via PR #79
   ├─ #39 Apple Container provider             terminal provider leaf
   ├─ #40 E2B provider                         terminal provider leaf
   ├─ #41 OpenShell policy                     terminal provider leaf
   ├─ #42 tmux / PTY                           terminal provider leaf
   └─ #43 hybrid exchange / repair             terminal provider leaf
main after #38–#43
└─ #44 runtime convergence                     convergence leaf

Phase 4 Product / Mobile
main
└─ #45 product contracts
   ├─ #46 dashboard GenUI
   ├─ #47 terminal projection
   ├─ #48 Expo mobile
   │  └─ #49 In-App action bridge              true child
   ├─ #50 Maestro MCP
   ├─ #51 WDA iOS projection
   └─ #52 scrcpy Android projection
main after #45–#52
└─ #53 product convergence

Phase 5 Security / Settlement
main
└─ #54 security contracts
   ├─ #55 OPA policy
   ├─ #56 durable workflow
   ├─ #57 OpenBao broker
   ├─ #58 verified ledger
   ├─ #59 Secure Enclave
   ├─ #60 CoreNFC challenge
   ├─ #61 MPC-TSS provider
   └─ #62 smart-account contracts
      └─ #63 testnet submission                true child
main after #54–#63
└─ #64 security convergence

Phase 6 Bettor reference consumer
main
└─ #65 consumer contracts
   └─ #66 immutable module closure
      ├─ #67 Skill binding
      └─ #68 runtime-env binding
serialized closure
└─ #69 CLI / MCP parity
   ├─ #70 Claude canary
   ├─ #71 Codex canary
   ├─ #72 GitHub origin
   └─ #73 Forgejo origin
main after #72 + #73
└─ #74 origin equivalence
main after #65–#74
└─ #75 reference composition release
```

Git Town moves branches; it does not create implementation, test, review, merge, release, or production evidence.

## Verification route

```text
README.md
→ ../../AGENTS.md
→ ../INDEX.md
→ architecture/STATE_MACHINES.md
→ this README
→ BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md
→ ../../src/runtime_env/cli.py and exact JSON subjects
→ consumer projection and its source commit/tree
→ Agent Shield status/Stack authorities
→ exact issue and PR
```

## Evidence boundary

Use these states without normalization:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
STALE_SOURCE_PIN
```

`STALE_SOURCE_PIN` is a documentation/audit finding: it requires an explicit sync plan or an accepted pinned-version decision. It is never silently converted into PASS.