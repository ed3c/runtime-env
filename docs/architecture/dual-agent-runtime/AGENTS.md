# AGENTS.md — Dual-Agent runtime integration

This file governs `docs/architecture/dual-agent-runtime/`. Repository-root `../../../AGENTS.md` and parent `../AGENTS.md` remain authoritative for global safety and architecture procedure.

## Integrated subject

```text
repository          ed3c/runtime-env
implementation main 92feed7c4e671dc63238155da9d4f394aac80d90
implementation tree 406895a4b0ac0df301d146aa89940c6adda402cd
contract-set digest e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
state               DETERMINISTIC_RUNTIME_STACK_MERGED
```

This subject proves deterministic contracts and adapters. It does not prove physical transport, live identity, workflow/provider execution, user outcome, Human admission, or release.

## Read order

Before changing or consuming the Dual-Agent runtime route:

1. `../../../AGENTS.md`;
2. `../../INDEX.md`;
3. `../AGENTS.md`;
4. this `AGENTS.md`;
5. `README.md`;
6. `stack-index.json`;
7. `../../../contracts/dual-agent/README.md`;
8. `../../../contracts/dual-agent/contract-set-manifest.json`;
9. the exact implementation script/module/profile/workload being changed;
10. its matching tests;
11. current GitHub issue, PR, commit/tree, and Actions run.

The Stack index is a trace projection. Current GitHub state and machine contracts remain canonical.

## Authority map

```text
skills-shared             portable method laws
runtime-env contracts     wire-schema authority
runtime-env transport     packet/result persistence and adapter semantics
runtime-env identity      workload/audience/policy/secret-handle semantics
bettor-arena              workflow and effect authorities
agent-shield-monorepo     provider/sandbox/API-browser observations
truth-verify-loop         independent evidence verification
Human/release systems     admission, release, rollback, production authority
```

No file in this directory may execute a provider, resolve a secret, create a trust domain, append workflow/task/effect state, approve a Human gate, or release a product.

## State Machine

```text
SOURCE_PROPOSAL
→ METHOD_SUBJECT_BOUND
→ RUNTIME_CONTRACTS_BOUND
→ DETERMINISTIC_TRANSPORT_BOUND
→ DETERMINISTIC_IDENTITY_BOUND
→ IMPLEMENTATION_MERGED_TO_MAIN
→ LOCAL_HANDOFF_READY
→ PHYSICAL_TRANSPORT_EVIDENCE | LIVE_IDENTITY_EVIDENCE
→ DOWNSTREAM_WORKFLOW_EFFECT_E2E
→ INDEPENDENT_VERIFICATION
→ HUMAN_ADMIT
→ RELEASE | ROLLBACK
```

The current state is `LOCAL_HANDOFF_READY`. Both live evidence alternatives are `NOT_EXERCISED`.

## Path and writer leases

| Owner | Writable scope | Must not write |
|---|---|---|
| DA-RC-C / #61 | `contracts/dual-agent/**`, examples/contract tests | transport/identity implementation or live state |
| DA-TR-C / #70 | local transport core, fixed module/profile/workload/test | identity, shared docs, live NATS claims |
| DA-TR-L / #71 | replay/inbox additions and tests | network provider or aggregate status |
| DA-TR-N / #72 | NATS adapter contract and hermetic test | live endpoint/credential or physical PASS |
| DA-ID-C / #75 | identity contract root and deterministic test | provider-specific enrollment or shared docs |
| DA-ID-L / #80 | local broker binding and test | secret values or Keychain access |
| DA-ID-CLOUD / #81 | cloud adapter binding and test | trust-domain creation or credential issuance |
| DA-ID-P / #82 | policy/revocation revalidation and test | live policy provider or release state |
| Shared trace / #50, #74, #84 | README, AGENTS, Stack index, closure/handoff route | implementation semantics or evidence promotion |
| LH-TR-001 / #73 | trusted physical receipts only | modifying deterministic law during the canary |
| LH-ID-001 / #83 | trusted identity receipts only | storing secret values or self-approving admission |

A second writer for a listed path or state authority is a stop condition.

## Git Stack law

- True children consume named unmerged parent bytes.
- Transport and identity branches are siblings under the wire-contract root.
- Terminal leaves merge into their nearest parent, then parents converge into #69, then #69 merges to `main`.
- Cross-repository prerequisites are Process DAG edges, not Git ancestry.
- GitHub base/head/commit/tree metadata is publication truth.
- Do not merge an already materialized leaf a second time.
- Do not force-push away failed-head or retry history to make the graph look simpler.

Merged chain:

```text
#77 → #76
#78 → #76
#76 → #69
#85 → #79
#86 → #79
#87 → #79
#79 → #69
#69 → main@92feed7c4e671dc63238155da9d4f394aac80d90
```

## Evidence non-substitution laws

```text
schema PASS              != execution
SQLite PASS              != cross-host delivery
NATS adapter PASS        != live NATS/JetStream/TLS
ACK                      != workflow/task/effect/user success
identity contract PASS   != enrollment or attestation
broker binding PASS      != secret resolution
cloud adapter PASS       != certificate/token issuance
policy revalidation PASS != live Cedar/OPA or revocation
provider health          != provider execution
CI PASS                  != physical canary
issue closed             != live closure
```

Keep `ABSENT`, `UNSUPPORTED`, `NOT_EXERCISED`, `DENIED`, `STALE`, `REFUSED`, `UNKNOWN`, `FAILED_CLEANUP`, and successful states distinct.

## Sensitive-data boundary

Never add raw passwords, tokens, certificates, private keys, cookies, browser profiles, storage state, device identifiers, private host paths, personal data, or private reasoning to contracts, fixtures, logs, receipts, or docs. Use opaque `secret://` references and evidence-safe digests only.

## Current closure

Closed deterministically:

```text
DA-RC-C   wire contracts
DA-TR-C   SQLite durable packet authority
DA-TR-L   restart/replay/inbox reconciliation
DA-TR-N   bounded NATS adapter semantics
DA-ID-C   identity contract root
DA-ID-L   local broker binding
DA-ID-CLOUD cloud identity adapter binding
DA-ID-P   queued policy/revocation revalidation
```

Open/live:

```text
#73 / LH-TR-001 physical NATS disconnect/reconnect
#83 / LH-ID-001 live identity/policy/secret canary
bettor-arena #184 workflow execution
bettor-arena #185 effect execution
bettor-arena #186 physical local→cloud→local user result
truth-verify-loop #22 independent live receipt verification
Human admission and release
```

## Local Handoff Execution Queue

### LH-TR-001

```text
owner       ed3c/runtime-env#73
base        92feed7c4e671dc63238155da9d4f394aac80d90
base tree   406895a4b0ac0df301d146aa89940c6adda402cd
state       HANDOFF_READY_NOT_EXERCISED
```

Required packet:

- authorized NATS/JetStream server/stream/consumer and TLS/secret handles;
- exact client/server/config subjects;
- offline enqueue and process restart before reconnect;
- reconnect, duplicate/redelivery, bounded ACK wait/max delivery;
- stale result and cross-tenant controls;
- result/inbox reconciliation and second restart;
- timeout/cancel and cleanup/residue observations;
- no task/effect/user/Human/release promotion.

Idempotency: one packet identity and one accepted logical result. Timeout: every network/process action bounded. Receipt: complete attempt/ACK/redelivery/restart/residue ledger. Rollback: remove disposable stream/consumer/server state, revoke temporary TLS handles, preserve receipts, return to exact base. Verifier: `truth-verify-loop#22`.

### LH-ID-001

```text
owner       ed3c/runtime-env#83
base        92feed7c4e671dc63238155da9d4f394aac80d90
base tree   406895a4b0ac0df301d146aa89940c6adda402cd
state       HANDOFF_READY_NOT_EXERCISED
```

Required packet:

- distinct LOCAL and CLOUD identities;
- authorized enrollment/attestation and bounded credential issuance;
- exact audiences/capabilities and no wildcard widening;
- opaque secret broker resolution without secret persistence;
- live policy decision, queued epoch change or revocation, reconnect revalidation;
- rotation/reissue path and cleanup/residue observation;
- transport auth kept separate from execution authorization.

Idempotency: one workload subject per lane. Timeout: enrollment, issuance, policy, rotation, and cleanup bounded. Receipt: provider/trust/audience/policy/revocation/lease metadata only. Rollback: revoke temporary credentials/identities and leases, remove test policy state, preserve receipts, return to exact base. Verifier: `truth-verify-loop#22`.

## Shadow stop conditions

Stop and update the handoff issue instead of self-promoting when the next action requires:

- a real endpoint, socket, provider, trust domain, credential, secret resolution, policy engine, or billing account;
- a physical cross-host or local→cloud→local run;
- an external write/effect;
- private-source access;
- Human approval/admission;
- release, rollback, production promotion, or destructive cleanup.

Use `NOT_EXERCISED` or `NOT_PERFORMED`, never fake PASS.

## Zero-context continuation

A new Agent should:

1. verify `92feed7c4e671dc63238155da9d4f394aac80d90` remains an ancestor of current public `main`;
2. read this file, `README.md`, and `stack-index.json`;
3. inspect current #57/#58/#59/#73/#83 and downstream #184/#185/#186/#22 state;
4. execute no live handoff without explicit trusted/Human authority;
5. preserve all duplicate/retry/timeout/failure attempts and cleanup evidence;
6. bind every receipt to exact repository/runtime/provider/policy subjects;
7. keep workflow, effect, user, Human, and release state external;
8. update the relevant Local Handoff queue with exact base, actions, idempotency, timeout, receipt, rollback, verifier, and remaining gaps.