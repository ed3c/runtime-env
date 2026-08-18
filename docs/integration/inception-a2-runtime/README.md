# Inception A2R — runtime contract preflight

Status: **OWNER IMPLEMENTATION PREPARATION ONLY**  
Upstream profile issue: `ed3c/enterprise_agent_system#7`  
Owner issue: `ed3c/runtime-env#67`  
Sandbox/provider sibling: `ed3c/agent-shield-monorepo#153`

This leaf prepares secret-free runtime, workload, capability, lease, cancellation,
timeout and cleanup contracts consumed by the Inception sandbox/steering adapter.
It does not own provider execution, Agent task state, credentials or product
behavior.

## Exact preparation subject

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
catalog/    one declaration per variable name and security metadata
contracts/  strict document shapes
modules/    runtime/provider requirement units
profiles/   composition
workloads/  fixed entrypoints and exact environment-name allowlists
policies/   carrier/isolation projections
src/        typed reducers and cross-file invariants
tests/      positive and disagreement controls
```

A module declaration, profile resolution or provider-health observation cannot
produce live workload or sandbox evidence.

## Target contract State Machine

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

Capability fields must preserve explicit `UNKNOWN`, `UNSUPPORTED`,
`NOT_EXERCISED` and `BLOCKED` states for streaming visibility, safe transaction
boundary, cancellation, resume, assistant prefill, tokenizer identity, context
limit and tool-call semantics. Hidden reasoning is not a control surface.

## Data flow

```text
exact runtime/image/policy identity
+ fixed workload name and argv entrypoint
+ environment variable names only
+ workspace/path/resource lease and expiry
        ↓
strict runtime contract validation
        ↓
offline policy and capability consistency gates
        ↓
secret-free consumer projection
        ↓
separate local sandbox/provider observation lane
```

## Provisional lease

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

`catalog/variables.json` remains read-only unless a required name is proven
absent and the new declaration carries no value. Existing generic runtime
contracts and generated consumer projections are not hand-edited.

## First implementation commit admission

The next commit must add the strict capability/workload contract and a hollow or
failing control for mutable identity, secret value, missing cleanup, stale lease,
path escape or false local/provider parity. It must use a fixed entrypoint and
must not expose a trailing generic command.

## Evidence ceiling

```text
OWNER_PREPARATION_READY
runtime contract code    NOT_STARTED
offline contract tests   NOT_EXERCISED
local sandbox execution  NOT_EXERCISED
provider observation     NOT_EXERCISED
secret values            ABSENT_BY_DESIGN
Human admission/release  NOT_PERFORMED
```

Machine authority: [`preflight.json`](preflight.json).
