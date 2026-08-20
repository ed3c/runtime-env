# Inception A2R — runtime capability contract

Status: **FIRST PUBLIC IMPLEMENTATION CANDIDATE**  
Upstream profile issue: `ed3c/enterprise_agent_system#7`  
Owner issue: `ed3c/runtime-env#67`  
Sandbox/provider consumer: `ed3c/agent-shield-monorepo#153`

This leaf owns the secret-free runtime/workload/capability contract consumed by
the Inception sandbox/steering adapter. The first implementation candidate adds
a strict closed schema and deterministic disagreement controls. It still does not
own provider execution, Agent task state, credentials or product behavior.

## Exact lineage

```text
repository        ed3c/runtime-env
base commit       c0790b9a8c81d7eb45ed45ac3d761c7fad5baa9b
base tree         df39f33f7a5278d255a022789b9f94c9b4a073b9
branch            agent/inception-a2-runtime-contracts
controller commit 6e0a916fd06dd8635d77c9a8c4d1b475185ea13e
controller tree   c3851a6953d456d0342a9776eed28561c1af0ca1
packet digest     sha256:18e6a7c89d6f6de322b68fd1c2928fcc6c4cd42508236bb1ca03957435106aec
packet bundle     sha256:dc4473b3195a738e55eb49c43661b6e1f4ea7f95c66749454776f2003b18ebc3
```

## Canonical ownership reused

```text
catalog/    variable names and security metadata only
contracts/  strict document shapes
modules/    runtime/provider requirement units
profiles/   composition
workloads/  fixed entrypoints and environment-name allowlists
policies/   carrier/isolation projections
src/        typed reducers and cross-file invariants
tests/      positive and disagreement controls
```

A module declaration, profile resolution or offline PASS cannot produce local or
provider execution evidence.

## Implementation subjects

```text
contracts/inception-runtime-capability.schema.json
tests/inception-agent-runtime/test_contract.py
```

The contract is closed with `additionalProperties: false` and binds:

```text
immutable image digest
fixed argv + timeout + CPU/memory/PID/output bounds
policy digest + NONE/ALLOWLIST_ONLY network
privileged=false + run_as_root=false + no host mounts
environment variable names only
workspace lease + timezone-aware expiry
explicit capability states
hidden_reasoning_access = ABSENT
mandatory descendant/workspace/residue cleanup
offline/local/provider evidence as separate lanes
```

## Contract State Machine

```text
RUNTIME_REQUIREMENT_DECLARED
→ IMMUTABLE_WORKLOAD_AND_POLICY_BOUND
→ ENVIRONMENT_NAME_ALLOWLIST_BOUND
→ RESOURCE_AND_WORKSPACE_LEASE_BOUND
→ CAPABILITY_MATRIX_DECLARED
→ CANCELLATION_TIMEOUT_CLEANUP_BOUND
→ OFFLINE_CONTRACT_VERIFIED
→ LOCAL_EXECUTION_ELIGIBLE | BLOCKED | NOT_EXERCISED
```

Capability fields preserve explicit `UNKNOWN`, `UNSUPPORTED`, `NOT_EXERCISED`
and `SUPPORTED` states for streaming visibility, safe transaction boundary,
cancellation, resume, assistant prefill, tokenizer identity, context limit and
tool-call semantics. Hidden reasoning is not a control surface.

## Deterministic disagreement controls

The public test fixture refuses:

```text
mutable image identity
generic shell entrypoint
secret value disguised as an environment name
privileged/root execution or host mounts
workspace escape
stale lease or naive evaluation clock
missing cleanup
hidden reasoning represented as SUPPORTED
offline PASS promoted to local/provider PASS
```

The fixture's clock is explicit and timezone-aware so tests remain reproducible;
it does not weaken runtime lease expiry semantics.

## Data flow

```text
exact runtime/image/policy identity
+ fixed workload argv
+ environment variable names only
+ workspace/resource lease and expiry
        ↓
strict closed contract validation
        ↓
offline deterministic evidence
        ↓
secret-free consumer projection
        ↓
separate local sandbox/provider observation lanes
```

## Writer lease

```text
docs/integration/inception-a2-runtime/**
contracts/inception-runtime-capability.schema.json
modules/inception-agent-runtime.json
profiles/inception-agent-local.json
workloads/inception-agent-probe.json
policies/inception-agent-local.json
tests/inception-agent-runtime/**
.github/workflows/inception-a2-runtime-contracts.yml
```

`catalog/variables.json` remains conditional: a name may be added only if proven
absent and no value is committed. Existing generic runtime contracts and generated
consumer projections remain read-only.

## Current deterministic evidence

The implementation workflow executes the strict contract controls and the full
repository `tests/run-all.sh` suite. The machine-readable state is
[`preflight.json`](preflight.json).

## Next transition

`ADD_FIXED_WORKLOAD_PROFILE_POLICY_FIXTURES_AND_CONSUMER_READBACK`

The next atom may add the concrete secret-free workload/profile/policy fixture and
consumer readback. Local execution and provider observation must remain separate.

## Evidence ceiling

```text
strict runtime contract       DETERMINISTIC_PASS
repository deterministic suite PASS
local workload execution      NOT_EXERCISED
sandbox execution             NOT_EXERCISED
provider observation          NOT_EXERCISED
secret values                 ABSENT_BY_DESIGN
Human admission/release       NOT_PERFORMED
```
