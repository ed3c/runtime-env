# Bettor Arena × Agent Shield PDF modular-integration audit

> Audit date: 2026-08-14  
> Source document: `科技巨頭開源授權與AI框架v2.pdf`, especially pages 25–41  
> Audit scope: `runtime-env` → `bettor-arena` → `agent-shield-monorepo`  
> Result: **PARTIALLY_INTEGRATED / NOT_PRODUCT_COMPLETE / STALE_RUNTIME_PROJECTION**

## 1. What is being verified

The PDF proposes an `agent-shield-monorepo/` domain product containing:

- smart-account contracts and validators/hooks;
- MPC-TSS, risk, durable workflow and verifiable-ledger services;
- mobile, iOS hardware-brake and web-dashboard applications;
- local Apple Container/OpenShell/tmux execution;
- cloud E2B/Firecracker execution;
- local/cloud synchronization and repair;
- Secure Enclave/NFC, OpenBao, OPA, Temporal, immudb and L2 settlement.

It also contains prose claiming that these MVPs are already completely integrated. That prose is a `SOURCE_PROPOSAL`; it is not implementation or runtime evidence.

The repository architecture assigns distinct owners:

| Plane | Repository | Owns |
|---|---|---|
| Instruction / Method | `skills-shared` | portable procedures and eval contracts |
| Runtime Contract | `runtime-env` | secret-free variables, modules, profiles, fixed workloads and policies |
| Integration / Acceptance | `bettor-arena` | composition, proof/control/mutation, Context Capsules, stateless MCP and bootstrap |
| Domain Product / Reference Consumer | `agent-shield-monorepo` | PDF product modules, provider adapters, product State Machines and domain canaries |

Therefore the question is not whether PDF directories were copied into Bettor. The correct question is whether all four planes are connected by immutable interfaces and whether each PDF capability has current subject-bound evidence.

## 2. Exact runtime binding freshness

### Runtime contract implementation baseline evaluated

```text
runtime-env commit: 4a333ccf106ef60bc6942b922b7f5efffb3876f5
runtime-env tree:   68cda3d0ce7f1df26475a5d7322968194e794046
```

This is the immutable implementation baseline evaluated by the audit. Later `runtime-env/main` commits may add or revise audit documentation without changing the contract semantics under comparison.

### Bettor consumer projection

```text
bettor path: .runtime-env/bindings/bettor-arena-local.json
binding source commit: 142e1ed278bf18f9c5c09186e28db16b623cdaee
binding source tree:   1bd5c97e6f5519182d151055cf5f83fccb7ff5fa
binding content digest: 805a069efdad08342f79f3eee74f8f122de445f2f4e67bf46364353faa80f745
```

Verdict: `STALE_SOURCE_PIN` relative to the evaluated runtime implementation baseline.

This does **not** prove that the old binding is invalid. It proves that the evaluated upstream contract changes are not represented in Bettor's checked projection. The next transition must be an explicit dry-run comparison and Human-reviewed sync decision, not an automatic update.

## 3. Integration matrix

| PDF capability / boundary | Repository owner | Current implementation evidence | Audit state |
|---|---|---|---|
| Secret-free runtime vocabulary and profiles | `runtime-env` | catalog/modules/profiles/workloads/policies and CLI validation exist | `IMPLEMENTED` |
| Bettor runtime requirement and generated projection | `bettor-arena` | `.runtime-env/requirements.json`, binding, workload, policies and example exist | `IMPLEMENTED_BUT_STALE_PIN` |
| Bettor module composition, proof and default-deny MCP | `bettor-arena` | deterministic module catalog, locks, proof subjects, Context Capsules, MCP and bootstrap mechanisms exist | `IMPLEMENTED` for named deterministic contracts |
| Provider-neutral runtime request/receipt SPI | `agent-shield-monorepo` | issue #38 merged through PR #79 at commit `7d28a8cada03726b2b8966d9a229500f285d1b2b` | `IMPLEMENTED` for the contract/SPI only |
| Disposable local runtime baseline | `agent-shield-monorepo` | status ledger records `runtime-local-disposable: PASS` | `PASS` for the exact local baseline subject |
| Apple Container | `agent-shield-monorepo` issue #39 | status ledger records `runtime-apple-container: NOT_EXERCISED` | `NOT_EXERCISED` |
| E2B / Firecracker | `agent-shield-monorepo` issue #40 | status ledger records `runtime-e2b: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| OpenShell / tmux | `agent-shield-monorepo` issues #41–#42 | status ledger records `runtime-openshell-tmux: NOT_EXERCISED` | `NOT_EXERCISED` |
| Hybrid immutable exchange and repair | `agent-shield-monorepo` issue #43 | planned molecular leaf; no promoted provider receipt | `NOT_IMPLEMENTED_OR_NOT_EXERCISED` |
| Expo mobile product | `agent-shield-monorepo` issue #48 | status ledger records `product-expo: NOT_EXERCISED` | `NOT_EXERCISED` |
| In-App action bridge | `agent-shield-monorepo` issue #49 | true child of Expo product surface | `NOT_IMPLEMENTED_OR_NOT_EXERCISED` |
| Maestro / WDA / scrcpy | `agent-shield-monorepo` issues #50–#52 | status ledger records `product-maestro-wda-scrcpy: NOT_EXERCISED` | `NOT_EXERCISED` |
| OPA, durable workflow, OpenBao, ledger, Secure Enclave, NFC, TSS and smart account | `agent-shield-monorepo` issues #54–#64 | status ledger records `security-native-providers: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| PDF ingest | `agent-shield-monorepo` | status ledger records `document-ingest-pdf: NOT_IMPLEMENTED` | `NOT_IMPLEMENTED` |
| Bettor reference-consumer canary | `agent-shield-monorepo` Phase 6 | status ledger records `bettor-consumer: NOT_EXERCISED` | `NOT_EXERCISED` |
| Claude/Codex live carrier | environment + Agent Shield/Bettor | status ledger records both `NOT_EXERCISED` | `NOT_EXERCISED` |
| Forgejo/GitHub equivalence | integration plane | current immutable equivalence receipt absent for this product subject | `NOT_EXERCISED` |
| Signed-in browser routes | environment + product adapters | status ledger records `signed-in-browser: NOT_EXERCISED` | `NOT_EXERCISED` |
| Human promotion / production rollback | Human governance | no product-complete release subject exists | `NOT_EXERCISED` |

## 4. Directory and State Machine division

```text
runtime-env/
  catalog → modules → profiles → workloads/policies
  → validate/render/check/sync
  → secret-free consumer projection

bettor-arena/
  .runtime-env requirements/binding
  + .agents Skill closure
  + .arena module/composition/context/lock
  → loopctl public port
  → default-deny MCP
  → proof/control/mutation
  → acceptance/release receipt

agent-shield-monorepo/
  runtime fabric
  → product/mobile
  → security/hardware/settlement
  → Bettor reference-consumer adapters
  → provider/product canaries
  → aggregate release subject
```

### Runtime Contract State Machine

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

### Bettor integration State Machine

```text
MODULE_REQUIREMENTS_SELECTED
→ CAPABILITY/CONFLICT_RESOLVED
→ SKILL/RUNTIME/HOST PROJECTIONS
→ PROOF MATRIX
→ HUMAN ADMIT
→ COMPOSITION LOCK
→ IMMUTABLE RELEASE / ROLLBACK
```

### Agent Shield provider/product State Machine

```text
FOUNDATION CONTRACT
→ PROVIDER OR PRODUCT LEAVES
→ SUBJECT-BOUND EVALS AND DISAGREEMENT CONTROLS
→ PHASE CONVERGENCE
→ BETTOR CONSUMER BINDING
→ CLI/MCP AND CARRIER CANARIES
→ ORIGIN EQUIVALENCE
→ REFERENCE COMPOSITION RELEASE
```

## 5. Molecular Git Town Stack

`agent-shield-monorepo` has an admitted `.git-town.toml`. Its canonical implementation plan is `docs/implementation/STACKED_IMPLEMENTATION_PLAN.md`.

### Phase 3 — Runtime fabric

```text
main
└─ #38 runtime SPI foundation                   MERGED / PR #79
   ├─ #39 Apple Container                       provider leaf
   ├─ #40 E2B runtime                           provider leaf
   ├─ #41 OpenShell policy                      provider leaf
   ├─ #42 tmux / PTY                            provider leaf
   └─ #43 hybrid exchange                       provider leaf
main after #38–#43
└─ #44 runtime convergence                      convergence leaf
```

### Phase 4 — Product and mobile

```text
main
└─ #45 product contracts
   ├─ #46 web dashboard
   ├─ #47 terminal projection
   ├─ #48 Expo mobile
   │  └─ #49 In-App action bridge               true child
   ├─ #50 Maestro MCP
   ├─ #51 WDA iOS projection
   └─ #52 scrcpy Android projection
main after #45–#52
└─ #53 product convergence
```

### Phase 5 — Security, hardware and settlement

```text
main
└─ #54 security contracts
   ├─ #55 OPA
   ├─ #56 durable workflow
   ├─ #57 OpenBao
   ├─ #58 verified ledger
   ├─ #59 Secure Enclave
   ├─ #60 CoreNFC
   ├─ #61 MPC-TSS
   └─ #62 smart-account contracts
      └─ #63 testnet submission                 true child
main after #54–#63
└─ #64 security convergence
```

### Phase 6 — Bettor reference consumer

```text
main
└─ #65 consumer contracts
   └─ #66 immutable module closure
      ├─ #67 Skill binding
      └─ #68 runtime binding
serialized selected closure
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

A terminal leaf owns one provider/product lane and its evidence. A convergence leaf owns shared registries, status, release manifests and aggregate compatibility. Git Town synchronization success is not correctness or release authority.

## 6. Required next transitions

### Runtime projection

```sh
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /path/to/bettor-arena
```

1. Run dry-run only.
2. Review source commit/tree, closure and generated diff.
3. Decide whether Bettor intentionally remains pinned or should advance.
4. Use `--apply` only after review.
5. Run staged offline consumer verification.
6. Record the exact canary/receipt state separately.

### Product implementation

1. Land provider/product leaves only after their foundation parent is admitted.
2. Keep Apple/E2B/OpenShell/tmux/mobile/security/settlement evidence independent.
3. Run each disagreement control against the public seam.
4. Aggregate only in the named phase convergence issue.
5. Complete Phase 6 immutable Bettor bindings and carrier/origin canaries.
6. Promote only through #75 with Human Admit and an explicit rollback subject.

## 7. Security and factuality boundary

The PDF correctly states in one section that absolute security does not exist, but elsewhere uses unsupported percentages and “100% immune” language. Repository truth must use threat models, controls, residual risk and exact evidence; it must not preserve absolute-security claims.

Likewise, package presence, permissive direct licensing, an architecture diagram, a generated binding, or a merged foundation contract does not prove provider isolation, performance, cost, legal fitness, domain correctness or production readiness.

## 8. Final verdict

```text
Runtime contract plane:                 IMPLEMENTED
Bettor deterministic integration plane: IMPLEMENTED for named contracts
Bettor runtime projection freshness:    STALE_SOURCE_PIN
Agent Shield runtime foundation:        IMPLEMENTED
PDF local/cloud provider layer:         INCOMPLETE
PDF product/mobile layer:               INCOMPLETE
PDF security/settlement layer:          INCOMPLETE
Bettor reference-consumer acceptance:   NOT_EXERCISED
Live carrier/origin/provider evidence:   NOT_EXERCISED or ABSENT
Product-complete release:               NOT_AVAILABLE
```

The honest answer is: **Bettor and runtime-env are modularly connected, but the PDF architecture is not yet modularly integrated end to end.**