# `contracts/`

Owner: JSON document shapes for variables, modules, profiles, workloads, carrier policies, consumer requirements, bindings, workloads, and policies.

```text
instance → schema validation → accepted / rejected
```

Dual-Agent offload wire contracts are owned by [`dual-agent/`](dual-agent/README.md). That subdirectory binds an immutable `skills-shared` method subject and owns only secret-free wire shapes; transport, identity, provider execution and effects remain separate lanes.

Schemas do not prove cross-file reference existence or live execution; `runtime-env validate`, tests, and canaries own those layers.
