# Dual-Agent runtime wire contracts

This directory is the **Runtime Contract Plane** owner for secret-free wire shapes consumed by the local/cloud offload method. The portable method lives in `ed3c/skills-shared`; this directory does not copy or redefine its method schema.

## Integrated runtime subject

```text
repository          ed3c/runtime-env
implementation main 92feed7c4e671dc63238155da9d4f394aac80d90
implementation tree 406895a4b0ac0df301d146aa89940c6adda402cd
manifest state      BOUND
contract-set digest e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe
```

The bound implementation subject contains the deterministic runtime contract, local durable transport/replay, bounded NATS adapter contract, workload identity bindings, and queued policy/revocation revalidation. It does not prove any live cross-host provider or identity operation.

## Immutable method dependency

```text
repository  ed3c/skills-shared
commit      7e33890e9e3763e0cd6188fdc68fce96e1caaba3
tree        7e2293b52b48394e4aa905d61fb5782f55110a67
path        skills/agentic-tech-lead-orchestration/references/dual-agent-offload/method-contract.v1.schema.json
$id         https://skills-shared.invalid/agentic-tech-lead-orchestration/dual-agent-offload/method-contract.v1.schema.json
sha256      83e1393a87c7caee5bc7cb8772b3706d3114b568b11a916609dccf723b251daf
```

Runtime-env owns these wire identities:

```text
runtime-env/dual-agent/offload-job/v1
runtime-env/dual-agent/capability-grant/v1
runtime-env/dual-agent/effect-intent/v1
runtime-env/dual-agent/artifact-manifest/v1
runtime-env/dual-agent/execution-receipt/v1
runtime-env/dual-agent/contract-set-manifest/v1
```

## Contract State Machine

```text
PORTABLE_METHOD_SUBJECT_BOUND
→ RUNTIME_SCHEMA_IDS_RESERVED
→ WIRE_SHAPES_IMPLEMENTED
→ SCHEMA_DIGESTS_VERIFIED
→ CONTRACT_SET_MANIFEST_BOUND
→ POSITIVE_EXAMPLES_FROZEN
→ DISAGREEMENT_CONTROLS_PASS
→ DETERMINISTIC_CONSUMER_HANDOFF_READY
```

`DETERMINISTIC_CONSUMER_HANDOFF_READY` does not imply physical delivery, live workload identity, provider execution, workflow correctness, an accepted effect, a user result, Human admission, or release.

## Directory and authority flow

```text
skills-shared method subject
        ↓ exact commit/tree/$id/sha256
contract-set-manifest.json
        ↓
offload job ───────────→ capability grant
     │
     ├─ read-only lane ───────────────→ execution receipt
     │
     └─ write lane ─→ effect intent ─→ execution receipt
                                      │
                                      └→ artifact manifest
```

Transport acknowledgement never upgrades workflow, task, effect, artifact, user-outcome, Human, or release state. Local and cloud execution remain independent evidence lanes. At-least-once delivery is expected; writes require stable job/idempotency/effect identities and independent effect readback.

Secret values, cookies, browser profiles, host-account paths, arbitrary shell commands, caller-selected working directories, provider endpoints, and raw credentials remain outside the wire contract.

## Deterministic implementation DAG

```text
DA-RC-C  runtime wire contracts
├─ DA-TR-C  SQLite durable outbox/event authority
│  ├─ DA-TR-L  restart/replay/inbox reconciliation
│  └─ DA-TR-N  bounded NATS/JetStream adapter contract
└─ DA-ID-C  workload identity/policy/secret-handle contract
   ├─ DA-ID-L      local broker binding
   ├─ DA-ID-CLOUD  cloud identity adapter binding
   └─ DA-ID-P      queued policy/revocation revalidation
```

The exact Stack subjects and Local Handoff queues are maintained in `docs/architecture/dual-agent-runtime/stack-index.json`.

## Verification

```sh
bash tests/test_dual_agent_contract.sh
python3 tests/dual_agent_contract_selftest.py
bash tests/test_dual_agent_main_trace.sh
bash tests/run-all.sh
```

The contract selftest validates P1–P6 and R01–R18. Repository-wide tests also exercise transport, replay, NATS adapter, identity, and policy controls. Optional JSON Schema meta-validation is reported separately and is never inferred from package absence.

## Evidence ceiling

Closed deterministically:

```text
wire contracts
SQLite durable outbox/event semantics
local restart/replay/inbox reconciliation
bounded NATS adapter semantics
provider-neutral identity binding
local broker binding
cloud identity adapter binding
queued policy/revocation revalidation
```

Still unproven:

```text
physical cross-host disconnect/reconnect
live NATS/JetStream server, consumer, and TLS
live local/cloud identity enrollment or attestation
live secret resolution
live policy provider, revocation, and rotation
workflow/provider/effect/user execution
Human admission and release
```

Highest evidence ceiling: `DETERMINISTIC_DUAL_AGENT_RUNTIME_STACK_ONLY`.