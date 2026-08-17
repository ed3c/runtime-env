# AGENTS.md — Dual-Agent Runtime Contract closure

This directory specializes the repository Tech Lead + Shadow Architect route for the uploaded `双 Agent 架构：云端本地协同` source and the cross-repository Dual-Agent program.

The source is `SOURCE_PROPOSAL`. It identifies real runtime problems but does not prove a provider, transport, identity system, credential broker, workflow, user outcome, license, release, or production state.

## Mandatory read order

1. [`../../../AGENTS.md`](../../../AGENTS.md)
2. [`../../../CONTEXT.md`](../../../CONTEXT.md)
3. [`../../../ARCHITECTURE.md`](../../../ARCHITECTURE.md)
4. [`../../INDEX.md`](../../INDEX.md)
5. [`../AGENTS.md`](../AGENTS.md)
6. [`../README.md`](../README.md)
7. [`../SHADOW_ARCHITECT_LEDGER.md`](../SHADOW_ARCHITECT_LEDGER.md)
8. [`README.md`](README.md)
9. [`closure-matrix.json`](closure-matrix.json)
10. [`../../integration/README.md`](../../integration/README.md)
11. nearest directory README, exact JSON/schema/code/test/workload/receipt and current GitHub/runtime subject
12. current Issues #45, #50, #57, #58 and #59 and their exact PR/check state

No Markdown, issue state, tag, package, environment-variable declaration, old receipt, another host or another provider can raise a runtime evidence state.

## Runtime authority boundary

`runtime-env` owns:

```text
secret-free variable and capability vocabulary
closed offload/artifact/effect/receipt schemas
module/profile/workload/policy composition
fixed-entrypoint host and provider adapters
local outbox/inbox and transport metadata when implemented
workload-identity, policy-epoch and opaque secret-handle bindings
exact invocation, cleanup and metadata-only receipts
consumer synchronization and freshness
```

`runtime-env` does not own:

```text
portable Skill procedure             → skills-shared
canonical task/workflow state        → Bettor LoopX reducer
canonical external-effect state      → Bettor effect ledger
provider product adapters            → agent-shield-monorepo
independent claim closure             → truth-verify-loop
Human approval, merge or release     → Human / final consumer authority
```

A transport acknowledgement is not task success. Authentication is not authorization. A provider invocation is not Gate PASS. A schema verdict is not live execution.

## Dual-Agent runtime problem IDs

```text
DA-R01  exact secret-free offload and receipt boundary
DA-R02  durable local outbox/inbox and at-least-once delivery
DA-R03  disconnect, reconnect, duplicate and restart semantics
DA-R04  exact workload identity, audience and capability binding
DA-R05  policy epoch, revocation and opaque secret-handle binding
DA-R06  local/cloud evidence separation and provider-independent SPI
DA-R07  cleanup, residue, cancellation, timeout and rollback evidence
DA-R08  immutable consumer projection and stale-binding refusal
```

Issue ownership:

```text
#57  DA-R01 and shared contract vocabulary
#58  DA-R02 / DA-R03 and physical transport canary
#59  DA-R04 / DA-R05
#45  scheduler/process-worktree runtime prerequisite
#50  repository Shadow/docs/current-head convergence
```

## Evidence ladder

Use this ladder for each runtime problem independently:

```text
SOURCE_PROPOSAL
→ CONTRACT_DECLARED
→ CONTRACT_VALIDATED
→ ADAPTER_IMPLEMENTED
→ DETERMINISTIC_CONTROLS_PASS
→ EXACT_HOST_OR_PROVIDER_EXECUTED
→ CONSUMER_RECONCILED
→ HUMAN_ADMITTED
→ RELEASED
```

Keep these states distinct:

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
STALE_BINDING
POLICY_REFUSED
IDENTITY_REFUSED
LOCAL_ONLY_REFUSED
TRANSPORT_UNAVAILABLE
DUPLICATE_DELIVERY
ACK_TIMED_OUT
RESULT_MISMATCH
FAILED_CLEANUP
UNKNOWN_RESIDUE
HUMAN_ADMIT_REQUIRED
```

## Required Tech Lead packet

Before mutating a runtime plane, freeze:

```text
exact repository commit/tree and consumer subject
problem IDs and explicit non-goals
contract or interface owner
input/output schemas and version/digest
process DAG prerequisites
branch class: sibling | true child | convergence
allowed/excluded paths
worktree, writer, path and external-resource leases
host/provider/platform/version/artifact/image/config identities
data classification and egress boundary
workload identity, audience, policy epoch and secret-handle refs
fixed argv/cwd/environment-name allowlist
timeout, retry, cancellation and cleanup budgets
positive assertions and planted disagreement controls
receipt and residue shape
rollback subject
Human-owned operations and Local Handoff
```

Reject cycles, multiple writers, mutable refs, wildcard capabilities, arbitrary command/cwd/env surfaces, raw secrets, local-only remote egress, missing cleanup, fake parallelism, missing convergence owner, or Worker merge/release authority.

## Directory writer and State Machine law

| Directory | State Machine | Writer rule | Evidence ceiling |
|---|---|---|---|
| `contracts/dual-agent/` proposed | `UNDECLARED → VALIDATED → CROSS_SCHEMA_CLOSED` | #57 contract owner only | schema/contract |
| `modules/` | `REQUESTED → REFERENCES_RESOLVED → MODULE_VALID` | module leaf; shared index by convergence | declaration only |
| `profiles/` | `SELECTED → MODULES_RESOLVED → PROFILE_RESOLVED` | profile owner; no secret values | composition only |
| `workloads/` | `SELECTED → EXACT_ENV → FIXED_ENTRYPOINT → RECEIPT` | fixed workload owner | one exact invocation |
| `scripts/dual_agent_transport/` proposed | `OUTBOX_COMMITTED → DELIVERY → RESULT → RECONCILED` | #58 runtime owner | exact host canary only |
| identity/policy adapters proposed | `IDENTITY_BOUND → POLICY_BOUND → LEASED → REVOKED/EXPIRED` | #59 owner | exact enrollment/canary only |
| `tests/` | controls and mutation disagreement | test owner; fixture labeled | deterministic/fixture only |
| `docs/architecture/dual-agent-runtime/` | source problem → owner → issue → evidence state | #50 documentation owner | documentation/audit only |
| generated consumer projections | requirements → resolve → digest → projection | repository generator only | projection only |

Generated files may be refreshed only by the repository-owned deterministic generator and must identify the producing workflow/commit. An Agent must not hand-edit generated bytes to make a gate pass.

## Molecular Stack law

```text
#57 DA-RC-C  schemas and vocabulary
└─ DA-RC-K  cross-schema invariants
   └─ DA-RC-E  positive, hollow, stale and privacy controls
      └─ DA-RC-D  contract docs and handoff

#58 DA-TR-C  transport SPI + SQLite schema + fixed workload
├─ DA-TR-L  local outbox/inbox and replay
├─ DA-TR-N  NATS/JetStream adapter
└─ DA-TR-E  disconnect/duplicate/restart/stale physical canary
        ↓
DA-TR-D  shared status/docs/receipt convergence

#59 DA-ID-C  identity/policy/secret-handle contract
├─ DA-ID-L      local binding
├─ DA-ID-CLOUD  cloud binding
├─ DA-ID-P      policy/revocation
└─ DA-ID-E      live wrong-audience/stale/revoked/leak controls
        ↓
DA-ID-D  shared profile/docs convergence
```

Sibling leaves require disjoint paths and external resources. A true child must consume named unmerged parent bytes. A cross-repository prerequisite is not Git ancestry. Shared indexes, public profiles and aggregate status have one convergence owner.

## Transport and identity hard laws

1. Durable local commit precedes publish.
2. Delivery is at-least-once; idempotency and logical result/effect identity are mandatory.
3. Acknowledgement is separate from workflow, task, effect and user success.
4. One packet may have many attempts but one accepted logical result.
5. Disconnect is not task failure; restart must rebuild from canonical local records.
6. `LOCAL_ONLY`, raw credentials, personal sessions and machine-local paths never leave the local execution boundary.
7. Local and cloud workload identities, audiences and receipts are independent.
8. Transport authentication does not authorize execution; policy and capabilities are checked separately.
9. Stale policy, revoked identity, expired lease or moved runtime binding refuses execution.
10. Secret handles and metadata may be portable; secret values are not.
11. Cleanup checks process, socket, stream/consumer, lease, DB/WAL/SHM, workspace and temp residue.
12. Provider/package/config presence is not live enrollment, isolation or transport evidence.

## Shadow Architect review

Independently compare:

```text
source problem
contract and profile
exact consumer binding
current host/provider subject
positive execution
planted controls
all attempts and duplicate dispositions
cleanup/residue
consumer readback
Human/release state
```

Stop as `CONTESTED`, `UNKNOWN`, `STALE_BINDING`, `REPLAN_REQUIRED`, or the exact refusal state when:

- one host/provider proxies another;
- a fixture or old receipt is promoted to live PASS;
- acknowledgement proxies result or effect success;
- a secret or local-only payload crosses the boundary;
- policy, identity, source, image, workload or consumer binding is stale;
- failed, duplicate, timeout, cancelled or superseded attempts disappear;
- cleanup or artifact readback is unknown;
- the consumer cannot reproduce the exact projection without a sibling checkout;
- multiple branches own one shared profile/index/status path;
- a source recommendation is treated as a mandatory provider.

## Stop and Local Handoff conditions

Stop mutation when the exact base/head, consumer pin, contract, path lease, provider, identity, policy, network, credential, server, host, runtime or Human decision changes or is unavailable. Do not create a later implementation branch merely because it appears in the process DAG.

The handoff must state:

```text
exact repository/head/tree and rollback
issue and molecular atom
current transition and blocked state
allowed/excluded paths and leases
contract/provider/host/consumer identities
commands that were actually executed
positive and planted-control results
receipts and residue
remaining NOT_IMPLEMENTED / NOT_EXERCISED / HUMAN_ADMIT_REQUIRED
next executable action and owner
```

## Completion boundary

This directory may document and audit #57–#59 and their relationship to #45/#50. It cannot mark them implemented or live. A final completion claim requires exact contract bytes, deterministic controls, physical host/provider receipts where claimed, consumer reconciliation, current-head delivery evidence, and explicit Human/release authority.