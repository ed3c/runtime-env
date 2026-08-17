# Dual-Agent Runtime Contract closure

This route maps the uploaded `双 Agent 架构：云端本地协同` source to `runtime-env` ownership, directory State Machines, process and Git DAGs, unfinished Issues, controls, evidence ceilings, and consumer handoff.

The source proposes an always-on cloud Agent, a local sovereign Agent, long-running task offload, disconnect/reconnect, and structured result return. Those are real product problems, not proof that a runtime exists. The PDF remains `SOURCE_PROPOSAL`.

Read [`AGENTS.md`](AGENTS.md), the parent [`../AGENTS.md`](../AGENTS.md), [`../README.md`](../README.md), and [`../SHADOW_ARCHITECT_LEDGER.md`](../SHADOW_ARCHITECT_LEDGER.md) before using this status.

## Current verdict

```text
existing secret-free Runtime Contract Plane         IMPLEMENTED
existing module/profile/workload/policy reducers    IMPLEMENTED
existing fixed-entrypoint and consumer sync laws    IMPLEMENTED
existing scheduler/process-worktree runtime         IMPLEMENTED MECHANISM / exact live closure varies
Dual-Agent portable method                          external issue open
Dual-Agent offload/receipt contracts                NOT_IMPLEMENTED / #57
SQLite outbox/inbox + NATS/JetStream adapter         NOT_IMPLEMENTED / #58
physical disconnect/reconnect/restart canary         NOT_EXERCISED / #58
workload identity/policy/secret-handle binding       NOT_IMPLEMENTED / #59
live identity rotation/revocation canary             NOT_EXERCISED / #59
Bettor durable workflow and effect admission         consumer issues open
selected provider isolation and API/browser route    provider issues open
end-to-end local → cloud → local user outcome        NOT_EXERCISED
Human admission and release                          OUTSIDE THIS REPOSITORY
```

The repository is structurally aligned with the PDF's runtime problem, but the problem is not closed. Declarations, schemas, provider names and issue creation cannot replace physical delivery, reconnect, identity, cleanup or consumer reconciliation evidence.

## Source-derived runtime denominator

| Runtime problem | Source locator | Current owner | Current state | Required next evidence |
|---|---|---|---|---|
| always-on cloud execution | PDF page 1, source lines 5–17 | Agent Shield provider plane plus Bettor Runtime Fabric | provider-neutral mechanisms exist; selected live cloud subject not proven here | exact provider/runtime/image/policy/workload and cleanup receipt |
| local sovereign execution | PDF page 1, source lines 12–17 | local runtime/profile/policy and consumer host | partial mechanisms; selected end-to-end local lane not proven | exact host identity, `LOCAL_ONLY` refusal, local submit/restart receipt |
| durable offload packet | PDF page 2, source lines 53–73 | #57 | `NOT_IMPLEMENTED` | closed schemas, cross-schema invariants and consumer fixtures |
| offline/reconnect delivery | PDF page 2, source lines 71–73 | #58 | `NOT_IMPLEMENTED`; live `NOT_EXERCISED` | SQLite outbox/inbox, at-least-once transport, duplicate/stale/restart canary |
| workload identity and policy | required by real deployment | #59 | `NOT_IMPLEMENTED`; live `NOT_EXERCISED` | exact audience/capability/policy/secret-handle binding and revocation controls |
| API-first/browser fallback | PDF page 3, source lines 85–107 | Agent Shield, not runtime-env | external issue open | provider-specific exact execution receipts |
| user-result reconstruction | implied by reconnect result return | Bettor physical canary | `NOT_EXERCISED` | consumer inbox commit, restart rebuild and user-visible verification |

## Directory → State Machine → DAG → data flow

| Directory / surface | State Machine | Input | Output / next owner | Issue / DAG owner | Evidence ceiling |
|---|---|---|---|---|---|
| `catalog/` | `UNDECLARED → METADATA_VALIDATED → VARIABLE_DECLARED` | runtime variable requirement | canonical secret-free variable vocabulary → modules | existing catalog owner | declaration only |
| `contracts/` | `BYTES → SHAPE_VALIDATED → VERDICT` | exact JSON subject | schema verdict → typed reducer/consumer | existing contract owner; proposed `contracts/dual-agent/` #57 | shape/contract only |
| proposed `contracts/dual-agent/` | `UNDECLARED → SCHEMA_VALIDATED → CROSS_SCHEMA_CLOSED` | skills-shared #359 method and exact problem requirements | offload, capability, effect, artifact and receipt contracts → #58/#59/Bettor/Agent Shield | #57 foundation | `NOT_IMPLEMENTED`; deterministic contract only |
| `modules/` | `MODULE_REQUESTED → REFERENCES_RESOLVED → MODULE_VALID` | catalog variables and capability requirements | runtime requirement unit → profiles | module leaf; shared index by convergence | declaration, not installed/live |
| `profiles/` | `PROFILE_SELECTED → MODULES_RESOLVED → PROFILE_RESOLVED` | modules and provider-independent policy | portable composition → workloads/policies | profile owner | composition only |
| `workloads/` | `WORKLOAD_SELECTED → EXACT_ENV → FIXED_ENTRYPOINT → RECEIPT` | profile, exact subject and environment-name allowlist | bounded invocation → scripts/runtime | workload owner | one exact invocation |
| `policies/` | `REQUIREMENT → CARRIER_PROJECTION → VERIFIED_PROJECTION` | carrier/runtime requirement | secret-free isolation/egress projection → consumer/provider | policy owner | projection only |
| `src/runtime_env/` | `PARSE → VALIDATE → RESOLVE → RENDER/CHECK/SYNC/RUN` | declarative planes | deterministic decisions and projections | reducer owner | deterministic semantics |
| proposed `scripts/dual_agent_transport/` | `PACKET_ACCEPTED → OUTBOX_COMMITTED → DELIVERY → RESULT → INBOX_COMMITTED → RECONCILED` | #57 packet plus host/transport profile | attempt/ack/result/restart/cleanup metadata receipts → Bettor | #58 | `NOT_IMPLEMENTED`; exact host canary only after execution |
| proposed identity/policy adapters | `IDENTITY_UNRESOLVED → AUDIENCE_BOUND → POLICY_BOUND → LEASED → ROTATED/REVOKED/EXPIRED` | workload, tenant, audience, policy epoch and opaque secret refs | runtime-admission metadata receipt → transport/provider/workflow | #59 | `NOT_IMPLEMENTED`; exact enrollment canary only |
| `scripts/` existing | bounded host/provider/process/worktree transitions | fixed workload inputs | metadata-only receipts | #37/#38/#45 and provider-specific owners | one exact adapter invocation |
| `tests/` | positive/disagreement/mutation controls | exact or fixture subject | deterministic verdict | each owning issue | fixture unless exact live subject |
| `.github-delivery/` | `ARTIFACT → RECEIPT → PUBLICATION → FRESHNESS` | tracked artifact plus GitHub state | publication evidence | delivery owner | publication only |
| `docs/architecture/` | `SOURCE/PROBLEM → OWNER → STATE → ISSUE → EVIDENCE` | source claims, GitHub/runtime observations | audit and handoff | #50 | documentation only |
| `docs/architecture/dual-agent-runtime/` | `DUAL_AGENT_PROBLEM → RUNTIME_OWNER → #57/#58/#59 → EVIDENCE_CEILING` | source denominator and current issues | specialized runtime map and machine matrix | #50 documentation leaf | documentation only |

## Runtime State Machine composition

```text
portable method requirement
        ↓
#57 exact secret-free contracts
  offload job
  capability grant
  effect intent
  artifact manifest
  execution receipt
        ↓
module/profile/workload/policy resolution
        ├───────────────────────┐
        ↓                       ↓
#58 transport              #59 identity/policy
SQLite outbox/inbox        workload/audience/capability
NATS/JetStream adapter     policy epoch/revocation
attempt/ack/result         opaque secret handles
restart/rebuild            short-lived credential metadata
        └───────────┬───────────┘
                    ↓
consumer durable workflow and provider execution
                    ↓
exact result/effect/artifact receipts
                    ↓
local inbox + consumer reconciliation
                    ↓
Human/release authority outside runtime-env
```

No arrow may be skipped. A profile resolution cannot manufacture a message delivery. A message delivery cannot manufacture task or effect success. An identity receipt cannot manufacture policy correctness. A provider execution cannot manufacture consumer reconciliation.

## Required runtime states

```text
CONTRACT_VALID
SUBJECTS_RESOLVED
READY_FOR_TRANSPORT
OUTBOX_COMMITTED
DELIVERY_PENDING
CONNECTED
DISCONNECTED
PUBLISHED
CONSUMER_ACKED
RESULT_PENDING
RESULT_RECEIVED
RESULT_VERIFIED
INBOX_COMMITTED
RECONCILED
```

Preserve all control and terminal states:

```text
ABSENT_SUBJECT
STALE_BINDING
LOCAL_ONLY_REFUSED
IDENTITY_ABSENT
SUBJECT_MISMATCH
AUDIENCE_REFUSED
ATTESTATION_ABSENT
POLICY_STALE
CAPABILITY_REFUSED
SECRET_HANDLE_ABSENT
LEASE_EXPIRED
TRANSPORT_UNAVAILABLE
DUPLICATE_DELIVERY
ACK_TIMED_OUT
DEADLINE_EXPIRED
CANCELLED
RESULT_MISMATCH
RESULT_STALE
FAILED_CLEANUP
UNKNOWN_RESIDUE
HUMAN_ADMIT_REQUIRED
```

## Process DAG

```text
skills-shared#359 portable method
        ↓ process prerequisite, never cross-repository Git ancestry
runtime-env#57 offload/receipt contract foundation
        ├──────────────────────────┐
        ↓                          ↓
runtime-env#58 transport      runtime-env#59 identity/policy/secret
        └──────────────┬───────────┘
                       ↓
bettor-arena#184 durable workflow
        ↓
bettor-arena#185 effect ledger
        ↓
Agent Shield provider and integration leaves
        ↓
bettor-arena#186 physical local → cloud → local canary
        ↓
truth-verify-loop#22 independent evidence
        ↓
bettor-arena#68 selected release and rollback
```

Existing runtime prerequisite:

```text
#45 bounded multi-Worker scheduler/process-worktree runtime
        ↓ exact admitted consumer binding and live canary where selected
#58/#59 and Bettor physical execution
```

Issue #50 remains the repository documentation/current-head/live-evidence convergence owner. It must not relabel #57–#59 as implemented from this branch.

## Molecular Stack PR plan

### #57 — exact offload contracts

```text
DA-RC-C  closed schemas and vocabulary
└─ DA-RC-K  cross-schema invariants and CLI validation
   └─ DA-RC-E  positive, hollow, stale, privacy and effect controls
      └─ DA-RC-D  nearest README/AGENTS and consumer handoff
```

### #58 — durable transport

```text
DA-TR-C  provider-neutral transport SPI + SQLite schema + fixed workload
├─ DA-TR-L  local outbox/inbox and deterministic replay
├─ DA-TR-N  NATS leaf/hub JetStream adapter and admission
└─ DA-TR-E  disconnect/duplicate/restart/stale/cleanup physical canary
        ↓
DA-TR-D  shared profiles/status/docs/receipt convergence
```

`DA-TR-L` and `DA-TR-N` are siblings only after one stable shared contract and only when paths/resources are disjoint. `DA-TR-E` is a true child only if it consumes unmerged implementation bytes; otherwise it starts from admitted `main`. Shared profiles and aggregate status belong to one convergence owner.

### #59 — workload identity, policy and secret handles

```text
DA-ID-C  identity/capability/policy/secret-handle contract
├─ DA-ID-L      local host binding
├─ DA-ID-CLOUD  cloud workload binding
├─ DA-ID-P      policy epoch, rotation and revocation
└─ DA-ID-E      wrong-audience/stale/revoked/leak live controls
        ↓
DA-ID-D  shared profile/docs convergence
```

Provider-specific identities or secret stores are sibling adapters. SPIFFE/SPIRE, Cedar/OPA, Keychain/OpenBao/KMS are candidates, not mandatory architecture facts.

### Git Town law

```text
path/resource-disjoint implementation   → siblings
named unmerged contract bytes consumed  → true child
shared profile/index/status              → convergence
cross-repository prerequisite            → process edge only
```

Git Town may move admitted branch ancestry. Its success cannot create contract, host, provider, cleanup, consumer, Human or release correctness.

## Data flow

```text
local consumer
  exact source/data/effect classification
        ↓
  runtime-env OffloadJob and runtime/profile/policy binding
        ↓
  SQLite outbox transaction
        ↓
  local transport adapter / NATS leaf
        ║ disconnect retained durably
        ║ at-least-once delivery
        ↓
  cloud transport adapter / NATS hub
        ↓
  consumer workflow/provider runtime
        ↓
  execution + artifact + effect result receipts
        ↓
  cloud-to-local result delivery attempts
        ↓
  SQLite inbox transaction
        ↓
  local restart and projection rebuild
        ↓
  consumer reconciliation
```

The runtime receipt contains identifiers, hashes, states, timings, bounded resource observations and cleanup metadata. It never contains credential values, browser cookies, private device sessions, local-only payloads, private reasoning or arbitrary owner paths.

## Tech Lead review of existing completed work

| Existing capability | Supported conclusion | Forbidden conclusion |
|---|---|---|
| catalog/modules/profiles/workloads/policies | runtime requirements can be declared, resolved and projected deterministically | the provider is installed, reachable or live |
| fixed workload execution | one checked-in entrypoint can be invoked with an exact environment allowlist | arbitrary offload or workflow durability exists |
| consumer sync and exact pins | generated consumer projection can bind source commit/tree and detect drift | consumer physical execution or provider correctness |
| local credential broker contract | secret ownership and metadata boundary are explicit | live secret store enrollment, rotation or revocation |
| scheduler/process-worktree runtime | bounded attempt, lease and Worker mechanisms exist | Dual-Agent transport, identity or user canary is closed |
| Forgejo/GitHub monitor routes | repository control-plane evidence can be collected separately | local/cloud task or effect correctness |
| issue #50 / existing Shadow ledger | current evidence ceilings and live gaps are named | #57–#59 implementation or live PASS |

## Required controls

### Contract controls

- mutable branch/tag/image/provider identity;
- job/receipt source mismatch;
- arbitrary `command`, `shell`, `cwd`, trailing arguments or environment widening;
- raw secret/session/host path;
- local-only remote route;
- write request without idempotency/effect identity;
- task success with cleanup failure;
- fixture/static validation promoted to live PASS.

### Transport controls

- publish before durable outbox commit;
- acknowledge before durable consumer/result commit;
- duplicate delivery creates another accepted result or external effect;
- disconnect becomes task failure;
- cross-tenant/project consumption;
- stale result after source/policy/runtime movement;
- restart loses a packet or manufactures PASS;
- cleanup reports green with process/socket/consumer/lease/WAL residue.

### Identity/policy controls

- local identity proxies cloud identity;
- wrong tenant/project/audience;
- stale policy after reconnect;
- revoked identity or expired lease executes;
- wildcard capability or fallback authority widening;
- raw secret in packet, argv, environment dump, log, receipt or artifact;
- transport mTLS represented as task/provider PASS;
- config/package presence represented as live enrollment.

## Shadow Architect closure matrix

| Issue | Exact problem | Current state | Next transition | Cannot close from this docs branch |
|---:|---|---|---|---|
| #45 | scheduler/process-worktree runtime | mechanism exists; exact live consumer evidence varies | preserve prerequisite and exact current receipt state | local/cloud transport or user result |
| #50 | directory DAG, current Shadow ledger, issue/live evidence convergence | active convergence owner | review this PR, current head/checks and all live receipts | #57–#59 implementation/live state |
| #57 | offload/capability/effect/artifact/receipt contracts | `OWNER_AND_CONTRACT_BOUND`; `NOT_IMPLEMENTED` | implement schemas, validator and controls | transport/provider/user PASS |
| #58 | SQLite outbox/inbox plus NATS/JetStream reconnect | `OWNER_AND_CONTRACT_BOUND`; live `NOT_EXERCISED` | implement deterministic transport and physical canary | workflow/provider/release correctness |
| #59 | workload identity, policy epoch and opaque secret handles | `OWNER_AND_CONTRACT_BOUND`; live `NOT_EXERCISED` | implement bindings and exact enrollment/revocation canary | provider task or Human authorization |

## Local Handoff

This documentation branch owns no provider enrollment or physical host operation. The next implementation Worker must choose only an issue whose exact prerequisites and host resources are available.

A valid handoff includes:

```text
issue and molecular atom
exact base/head/tree and rollback
path/worktree/resource leases
contract/profile/workload/provider identities
fixed commands actually available
required credential/host/server/Human inputs
positive and planted controls
expected receipts and residue
blocked/unexercised states
```

No future branch is created just because it appears in the DAG. Provider, credential, network or Human absence remains explicit.

## Completion boundary

This route can close only documentation routing and honest issue/evidence mapping for #50/#57–#59. It cannot close the source problem, transport, identity, provider, consumer workflow, user result, Human admission, release or production operation.