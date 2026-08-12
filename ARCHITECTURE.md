# Architecture — runtime-env

## Role

`runtime-env` is the secret-free Runtime Contract Plane. It owns vocabulary and portable runtime selection, not credential values or product behavior.

## Contract topology

```text
catalog/variables.json        one declaration per name
          |
          v
modules/*.json                provider/runtime requirements
          |
          v
profiles/*.json               workload composition
          |
          +--> workloads/*.json   fixed entrypoints and exact env allowlists
          +--> policies/*.json    carrier-native isolation projections
          |
          v
runtime-env CLI               validate / list / render / check / workload / sync
          |
          +--> deterministic examples
          +--> presence/readiness metadata
          +--> explicit consumer projection
                     |
                     +--> bindings
                     +--> workloads
                     +--> policies
                     +--> examples
```

The catalog is vocabulary/security SSOT. Modules own requirement semantics. Profiles own composition. Workloads own fixed execution shape. Policies own carrier projection. The CLI owns cross-document invariants. Generated examples and consumer files are projections, not parallel truth.

## State machines

### Contract resolution

```text
UNDECLARED
→ VARIABLE_DECLARED
→ MODULE_VALID
→ PROFILE_RESOLVED
→ WORKLOAD/POLICY_SELECTED
→ PORTABLE_CLOSURE_READY
```

### Consumer projection

```text
REQUIREMENTS_RECEIVED
→ SOURCE_CLEAN_AND_IDENTIFIED
→ SYNC_PLANNED
→ APPLY_EXPLICIT
→ PROJECTION_WRITTEN
→ STAGED_VERIFY
→ CANARY/RECEIPT
→ HUMAN PROMOTION OR ROLLBACK
```

### Secret materialization

```text
PORTABLE_NAME_DECLARED
→ EXECUTION_PLANE_SELECTED
→ HOST/PROVIDER SECRET BROKER
→ FIXED ENTRYPOINT RECEIVES MINIMAL ENV OR OPAQUE BROKER HANDLE
→ VALUE NEVER ENTERS PORTABLE RECEIPT
```

Detailed transitions are in [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).

## Security invariants

- Secret values never enter Git or deterministic projections.
- Secret variables have no committed defaults.
- Entry-point environment allowlists are exact.
- No generic shell-over-MCP or trailing arbitrary command surface.
- A consumer hook validates local staged projection without network or sibling checkout.
- GitHub/ChatGPT connectors provide authorization/tools, not compute.

## Cross-repository plane

`skills-shared` supplies procedures, `runtime-env` supplies secret-free runtime closure, `bettor-arena` supplies integration/proof/execution acceptance, and Agent Shield supplies domain consumer state. See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md).
