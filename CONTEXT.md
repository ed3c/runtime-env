# CONTEXT.md — runtime-env current handoff

`runtime-env` is the secret-free Runtime Contract Plane between portable Skills and executable consumers.

```text
skills-shared requirements
        |
        v
runtime-env variable/module/profile/workload/policy closure
        |
        v
bettor-arena binding + composition + acceptance
        |
        v
agent-shield-monorepo consumer/provider canaries
```

## Current contract boundary

- Variables, modules, profiles, workloads, policies, CLI, and explicit consumer sync exist.
- Secret values remain host/provider owned.
- Consumer verification is offline and sibling-checkout independent.
- A declaration does not prove provider execution.
- The common multi-hop document routes are being added under issue `ed3c/runtime-env#29`, parent `ed3c/bettor-arena#35`.
- A mechanical four-repository route checker is `NOT_IMPLEMENTED` unless a later issue/PR supplies it.

Read [`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md) for the desired/resolved lifecycle and [`docs/local-integration.md`](docs/local-integration.md) for host-local maintenance boundaries.
