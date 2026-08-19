# Dual-Agent runtime wire contracts

This directory is the **Runtime Contract Plane** owner for the secret-free wire
shapes consumed by the local/cloud offload method. The portable method lives in
`ed3c/skills-shared`; this directory does not copy or redefine its method schema.

## Immutable method dependency

```text
repository  ed3c/skills-shared
commit      7e33890e9e3763e0cd6188fdc68fce96e1caaba3
tree        7e2293b52b48394e4aa905d61fb5782f55110a67
path        skills/agentic-tech-lead-orchestration/references/dual-agent-offload/method-contract.v1.schema.json
$id         https://skills-shared.invalid/agentic-tech-lead-orchestration/dual-agent-offload/method-contract.v1.schema.json
sha256      83e1393a87c7caee5bc7cb8772b3706d3114b568b11a916609dccf723b251daf
```

The method-plane handoff fixture carries the same digest. Runtime-env owns these
wire identities:

```text
runtime-env/dual-agent/offload-job/v1
runtime-env/dual-agent/capability-grant/v1
runtime-env/dual-agent/effect-intent/v1
runtime-env/dual-agent/artifact-manifest/v1
runtime-env/dual-agent/execution-receipt/v1
runtime-env/dual-agent/contract-set-manifest/v1
```

## State Machine

```text
PORTABLE_METHOD_SUBJECT_BOUND
→ RUNTIME_SCHEMA_IDS_RESERVED
→ WIRE_SHAPES_IMPLEMENTED
→ CONTRACT_SET_MANIFEST_BOUND
→ POSITIVE_EXAMPLES_FROZEN
→ CONSUMER_HANDOFF_READY
```

This branch may reach `CONSUMER_HANDOFF_READY` only for deterministic contract
bytes. Transport, workload identity enrollment, provider execution, external
effects, user outcome, merge and release are separate states.

## Data flow and authority

```text
skills-shared method subject
        ↓ exact commit/tree/$id/sha256
contract-set-manifest.json
        ↓
offload job ──→ capability grant
     │
     ├── read-only execution ─────────────→ execution receipt
     │
     └── write ─→ effect intent ──────────→ execution receipt
                                  │
                                  └────────→ artifact manifest
```

Transport acknowledgement never upgrades workflow, task, effect, artifact,
user-outcome or release state. Local and cloud execution are independent lanes.
At-least-once delivery is expected; writes require a stable idempotency key and
effect identity. Secret values, cookies, browser profiles, host paths, arbitrary
shell commands and caller-selected working directories are outside every wire
shape.

`contract-set-manifest.json` binds the immutable method dependency and the
SHA-256 of each runtime schema. Its runtime commit/tree remain
`CANDIDATE_SUBJECT_PENDING` until a later publication/convergence owner freezes
the exact published subject; schema digests are already exact and are checked by
`tests/dual_agent_contract_selftest.py`.

## Verification

```sh
bash tests/test_dual_agent_contract.sh
python3 tests/dual_agent_contract_selftest.py
bash tests/run-all.sh
```

The selftest validates the positive P1–P6 denominator and the pre-registered
R01–R18 disagreement controls. It uses only the Python standard library. When
the optional `jsonschema` module is present it additionally executes
`Draft202012Validator.check_schema`; absence of that optional package is
reported explicitly and is not misrepresented as independent meta-schema
validation.

Evidence ceiling: deterministic secret-free contract compatibility only.
