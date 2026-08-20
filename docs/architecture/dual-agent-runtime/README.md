# Dual-Agent runtime integration

Status: deterministic Runtime Contract, Transport, and Identity planes are merged to public `main`.

```text
implementation commit  92feed7c4e671dc63238155da9d4f394aac80d90
implementation tree    406895a4b0ac0df301d146aa89940c6adda402cd
contract-set digest    e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
highest evidence       DETERMINISTIC_DUAL_AGENT_RUNTIME_STACK_ONLY
```

This directory is the Agent-readable route for the Dual-Agent requirement described by the source PDF/article. The source remains a requirement denominator; deterministic contracts do not prove a 24/7 cloud Agent or a physical local→cloud→local run.

## Required read order

```text
../../../AGENTS.md
→ ../../INDEX.md
→ ../AGENTS.md
→ this README
→ AGENTS.md
→ stack-index.json
→ ../../../contracts/dual-agent/README.md
→ ../../../contracts/dual-agent/contract-set-manifest.json
→ ../../../scripts/dual_agent_transport.py
→ ../../../scripts/dual_agent_nats_adapter.py
→ ../../../scripts/dual_agent_identity.py
→ ../../../scripts/dual_agent_identity_local.py
→ ../../../scripts/dual_agent_identity_cloud.py
→ ../../../scripts/dual_agent_policy_revalidation.py
→ matching tests/test_*.sh
→ current GitHub issue / PR / Actions receipt
```

## Real-world problem denominator

The source architecture requires a real workflow:

```text
local request committed while offline
→ local process restart
→ network reconnect
→ cloud dispatch continues while local is unavailable
→ bounded isolated API-first or browser-fallback execution
→ structured result and content-addressed artifacts
→ local inbox commit
→ second local restart and deterministic reconstruction
→ user-visible result verification
→ optional effect admitted at most once
→ cleanup and Human review
```

`runtime-env` owns the exact method-to-runtime binding, transport semantics, identity/policy bindings, and fixed runtime entrypoints. It does not own cloud workflow progression, external effects, provider truth, user-result closure, Human admission, or release.

## Authority map

```text
skills-shared
  portable method laws
        ↓ exact method commit/tree/$id/digest
runtime-env contracts/dual-agent
  canonical secret-free wire schemas
        ↓
runtime-env transport adapters
  durable local packet/result semantics and provider-neutral network contract
        ↓
runtime-env identity adapters
  workload/audience/capability/policy/opaque-secret bindings
        ↓
bettor-arena
  workflow and effect authorities
        ↓
agent-shield-monorepo
  provider / sandbox / API-browser observations
        ↓
truth-verify-loop
  independent evidence verification
        ↓
Human / release authorities
```

No downstream plane may rewrite the Runtime Contract Plane. No runtime test or adapter may self-promote workflow, task, effect, user, Human, or release state.

## Directory → State Machine → DAG owner

| Directory / file | State Machine | Input | Output / owner | Evidence ceiling |
|---|---|---|---|---|
| `contracts/dual-agent/` | `METHOD_BOUND → SCHEMAS_VALID → MANIFEST_BOUND` | exact method subject | canonical wire contract set | deterministic schema/semantic contract |
| `examples/dual-agent/` | `FIXTURE_DECLARED → POSITIVE_CASE_VALIDATED` | contract set | P1–P6 examples | fixture only |
| `scripts/dual_agent_transport.py` | `OUTBOX_COMMITTED → PUBLISHABLE → ACKED` | offload packet | local SQLite transport receipt | local deterministic transport |
| `scripts/dual_agent_nats_adapter.py` | `PACKET_BOUND → DELIVERY → REDELIVERY → ACK` | transport packet + bounded adapter config | provider-neutral transport observation | no live socket/server proof |
| `scripts/dual_agent_identity.py` | `WORKLOAD_BOUND → AUDIENCE_BOUND → CAPABILITY/POLICY_CHECKED` | exact workload + identity contract | identity admission finding | deterministic identity semantics |
| `scripts/dual_agent_identity_local.py` | `LOCAL_IDENTITY → BROKER_HANDLE_BOUND` | local identity + opaque handle | broker-binding receipt | no secret read |
| `scripts/dual_agent_identity_cloud.py` | `CLOUD_IDENTITY → TRUST_REF_BOUND → CREDENTIAL_METADATA_CHECKED` | cloud workload + logical provider refs | cloud identity adapter receipt | no live attestation/issuance |
| `scripts/dual_agent_policy_revalidation.py` | `QUEUED → POLICY_REVALIDATED → ADMIT/REFUSE` | queued/current policy + identity lease | typed reconnect decision | no live Cedar/OPA proof |
| `profiles/` / `modules/` / `workloads/` | `DECLARED → RESOLVED → FIXED_ENTRYPOINT` | repository-owned configuration | bounded runtime selection | declared/fixed only |
| `tests/` | `SUBJECT → POSITIVE/NEGATIVE CONTROL → VERDICT` | exact code/config | deterministic CI receipt | not physical runtime evidence |
| `docs/architecture/dual-agent-runtime/` | `ISSUE/PR STATE → INTEGRATION TRACE → HANDOFF` | GitHub state + exact subjects | Agent route and queue | documentation only |

## Runtime State Machines

### Contract plane

```text
PORTABLE_METHOD_SUBJECT_BOUND
→ RUNTIME_SCHEMA_IDS_RESERVED
→ WIRE_SHAPES_IMPLEMENTED
→ SCHEMA_DIGESTS_VERIFIED
→ CONTRACT_SET_MANIFEST_BOUND
→ DETERMINISTIC_CONSUMER_HANDOFF_READY
```

### Local transport plane

```text
PACKET_PROPOSED
→ OUTBOX_COMMITTED
→ DISCONNECTED
→ PROCESS_RESTARTED
→ PENDING_PROJECTION_REBUILT
→ PUBLISHED
→ CONSUMER_ACKED
→ RESULT_PENDING
→ RESULT_RECEIVED
→ VERIFIED
→ INBOX_COMMITTED
→ RECONCILED
→ SECOND_RESTART_REBUILT
```

Refusal alternatives remain distinct:

```text
PACKET_DIGEST_COLLISION
CROSS_TENANT_DELIVERY
LOCAL_ONLY_REMOTE_EGRESS
STALE_RESULT
RESULT_MISMATCH
RESTART_LOSS
CLEANUP_WITH_RESIDUE
```

### Network-adapter plane

```text
ADAPTER_CONFIG_VALIDATED
→ TENANT_SUBJECT_BOUND
→ DELIVERY_RECORDED
→ ACKED | REDELIVERY_REQUIRED | REDELIVERY_BUDGET_EXCEEDED
```

This is a hermetic adapter contract. `LIVE_NATS_CONNECTED`, `LIVE_STREAM_CREATED`, `LIVE_CONSUMER_ACTIVE`, and `LIVE_TLS_ENROLLED` remain `NOT_EXERCISED`.

### Identity and policy plane

```text
WORKLOAD_SUBJECT_BOUND
→ LOCAL_IDENTITY_BOUND | CLOUD_IDENTITY_BOUND
→ AUDIENCE_BOUND
→ CAPABILITIES_CHECKED
→ POLICY_EPOCH_CHECKED
→ SECRET_HANDLE_LEASE_CHECKED
→ DETERMINISTIC_ADMISSION_ALLOW
```

Typed refusal terminals:

```text
WRONG_AUDIENCE
POLICY_STALE
POLICY_REFUSED
CAPABILITY_REFUSED
REVOKED_IDENTITY
EXPIRED_IDENTITY_LEASE
FAILED_CLEANUP
```

Transport authentication never implies execution authorization or task success.

## Process DAG

```text
skills-shared method subject
        ↓
DA-RC-C / #61 / PR #69
runtime wire contracts
        ├─────────────────────────────┐
        ↓                             ↓
DA-TR-C / #70 / PR #76          DA-ID-C / #75 / PR #79
        ├─────────────┐          ├──────────┬──────────┐
        ↓             ↓          ↓          ↓          ↓
DA-TR-L #71      DA-TR-N #72   DA-ID-L #80  CLOUD #81  POLICY #82
        │             │          │          │          │
        └──────┬──────┘          └──────────┼──────────┘
               ↓                            ↓
       #73 physical transport       #83 live identity canary
               └──────────────┬─────────────┘
                              ↓
                    bettor-arena #184/#185
                              ↓
                    bettor-arena #186 E2E
                              ↓
                    truth-verify-loop #22
                              ↓
                    Human / release authority
```

## Git Stack and merge chain

True byte dependencies were merged bottom-up:

```text
Transport branch
PR #77 → #76  merge 50f2001e31e44bd6d0f32ee1ae7c1f5e7411a345
PR #78 → #76  merge fdcdb9404439d1e524a6fb9b3b20b922b16810a4
PR #76 → #69  merge 6ac77e3925dc0b91e34d6cca70dfa87ea50f467f

Identity branch
PR #85 → #79  merge 454a7a482e39b940d156bfbaa445f3bd8ba4ee62
PR #86 → #79  merge 48330cefc608e08e7b24dd7f7a0563a9dbc261d2
PR #87 → #79  merge 3f2a7410377af3ffdcb69ba4f2be695f5b031e0e
PR #79 → #69  merge cd2c36970bb6b2248a146e98d083fa0a35ce99e1

Convergence
PR #69 → main merge 92feed7c4e671dc63238155da9d4f394aac80d90
```

### Molecular exact subjects

| Atom | Issue / PR | Exact head | Exact tree | Targeted CI |
|---|---|---|---|---|
| DA-RC-C | #61 / #69 | `1fd6a65a2e628ba1b31e89800297e7202dadf126` | `cc287010c96391e0a718141c2f4afb92bac3db06` | `32251505194` |
| DA-TR-C | #70 / #76 | `08fd712572ebe63b3c4286b361909a11ded9d172` | `a0971d7b4bb0f70548989582f54f522ce655c91b` | `32252919999` |
| DA-TR-L | #71 / #77 | `f910536b5a8ace7610eb8957cd3eb37f16c08065` | `a1aa879cbd9b0d8ddf9845183c4d1a3e3a6dc4e3` | `32253473378` |
| DA-TR-N | #72 / #78 | `ebf7e36387d4ffff8f8b428eb062525098013f5c` | `c706be102cb4466ffed041d7985e3713579528be` | `32254465413` |
| DA-ID-C | #75 / #79 | `5c9a960ed9883e294d6cdb5c949256cf937972ed` | `b8c7efc2a653a008cf12aa4f7120ed526eb80b3d` | `32254852893` |
| DA-ID-L | #80 / #85 | `8ea2667265b553059b2879f800c7bb1afc788d40` | `48a5744fd4ca6d6d7b6a4921dba81c02c7c3ddaf` | `32258804609` |
| DA-ID-CLOUD | #81 / #86 | `940f9c74be8b8f7b2c427e79725786059696cd45` | `61a7e346c6e0e0a1346d8363188db5128615fd35` | `32259034357` |
| DA-ID-P | #82 / #87 | `22bff7e329209491ee47e29c4cdd8c74b4725d81` | `8ddb3c88e80f76ef74210d9fba9b0c9a540404ce` | `32259277414` |

GitHub base/head metadata and exact commit trees are publication truth. Do not manufacture cross-repository Git ancestry; cross-repository prerequisites are Process DAG edges only.

## Data flow

```text
method contract
+ source commit/tree
+ job/idempotency/tenant
+ data/effect classification
+ capability/policy/runtime digests
        ↓
offload-job/v1 + capability-grant/v1
        ↓
SQLite outbox commit
        ↓
provider-neutral NATS packet/ACK/redelivery contract
        ↓
identity/audience/policy/opaque-secret revalidation
        ↓
workflow admission request
        ↓
execution-receipt/v1 + artifact-manifest/v1
        ↓
SQLite inbox/reconciliation/restart rebuild
        ↓
independent user-result and effect verification outside runtime-env
```

## Non-substitution laws

```text
schema PASS              != transport execution
SQLite replay PASS       != cross-host reconnect
NATS adapter PASS        != live NATS/JetStream/TLS
identity contract PASS   != enrollment/attestation
broker binding PASS      != secret resolution
policy revalidation PASS != live policy provider/revocation
transport auth PASS      != execution authorization
ACK                      != workflow/task/effect/user success
provider presence        != provider execution
CI PASS                  != physical canary/Human/release
```

## Closure matrix

| Requirement | State |
|---|---|
| Secret-free runtime wire contracts | `MERGED / CONTRACT_CLOSED` |
| Contract-set exact method/schema binding | `MERGED / BOUND` |
| SQLite durable outbox/event semantics | `MERGED / CONTRACT_CLOSED` |
| Local restart/replay/inbox reconciliation | `MERGED / CONTRACT_CLOSED` |
| Bounded NATS/JetStream adapter semantics | `MERGED / CONTRACT_CLOSED` |
| Workload identity/audience/capability contract | `MERGED / CONTRACT_CLOSED` |
| Local broker binding | `MERGED / CONTRACT_CLOSED` |
| Cloud identity adapter binding | `MERGED / CONTRACT_CLOSED` |
| Queued policy/revocation revalidation | `MERGED / CONTRACT_CLOSED` |
| Physical NATS disconnect/reconnect #73 | `NOT_EXERCISED` |
| Live local/cloud identity canary #83 | `NOT_EXERCISED` |
| Workflow/effect integration | `OUTSIDE_RUNTIME_ENV / NOT_EXERCISED_HERE` |
| Physical local→cloud→local user outcome #186 | `NOT_EXERCISED` |
| Human admission | `NOT_PERFORMED` |
| Release | `NOT_PERFORMED` |

Implementation issues #61, #70, #71, #72, #75, #80, #81, and #82 are eligible to close as completed after this trace finalization passes. Parent #57 may close for the exact contract objective. Parents #58 and #59 remain open until #73 and #83 produce live evidence. Documentation convergence issues #74 and #84 may close through this shared finalization.

## Local Handoff Execution Queue

### `LH-TR-001` — physical transport

```text
owner       runtime-env#73
exact base  runtime-env@92feed7c4e671dc63238155da9d4f394aac80d90
base tree   406895a4b0ac0df301d146aa89940c6adda402cd
state       HANDOFF_READY / NOT_EXERCISED
```

Required: authorized NATS/JetStream server, stream/consumer, TLS identities, two runtime processes or hosts, offline enqueue, reconnect, duplicate/redelivery, restart, stale-result refusal, bounded timeout/cancel, and cleanup/residue readback.

Idempotency: one packet identity and one logical result; duplicate delivery may occur but cannot create duplicate accepted state.

Receipt: preserve server/client/config identities, attempts, ACKs, redeliveries, process restarts, result/inbox state, network observations, and residue inventory.

Rollback: stop consumers/server, revoke temporary TLS/secret handles, delete disposable stream/consumer state, preserve immutable receipts, and return to the exact base.

Verifier: `truth-verify-loop#22` after actual receipts exist.

### `LH-ID-001` — live workload identity

```text
owner       runtime-env#83
exact base  runtime-env@92feed7c4e671dc63238155da9d4f394aac80d90
base tree   406895a4b0ac0df301d146aa89940c6adda402cd
state       HANDOFF_READY / NOT_EXERCISED
```

Required: distinct local/cloud identities, authorized enrollment/attestation, bounded credential issuance, opaque secret broker, live policy decision, queued policy change or revocation, reconnect revalidation, rotation/reissue, and cleanup/residue readback.

Idempotency: one workload subject per lane and no capability widening across fallback or renewal.

Receipt: preserve trust/provider subjects, audience, capability set, policy digest/epoch, revocation/rotation attempts, secret-handle metadata, and cleanup evidence without secret values.

Rollback: revoke disposable credentials/identities, remove test policy and broker leases, preserve receipts, and return to the exact base.

Verifier: `truth-verify-loop#22`; transport authentication cannot substitute for identity authorization.

## Stop condition

No additional deterministic adapter should be added merely to avoid #73 or #83. Any step needing a real endpoint, credential, trust domain, policy provider, billing, external effect, Human decision, merge/release, or destructive cleanup must stop at the Local Handoff queue and record `NOT_EXERCISED` or `NOT_PERFORMED`.