# Traceability index — runtime-env document routing

```text
source / requirement
→ variable/module/profile/workload/policy decision
→ issue / PR
→ test and negative control
→ immutable source commit/tree
→ consumer projection / receipt
→ canary and Human Admit
```

## Documentation stack

| Subject | State |
|---|---|
| Parent four-repository contract | `ed3c/bettor-arena#35` open |
| Runtime documentation binding | `ed3c/runtime-env#29` this sibling |
| Shared method binding | `ed3c/skills-shared#84` sibling |
| Agent Shield binding | `ed3c/agent-shield-monorepo#77` sibling |
| Bettor integration binding | `ed3c/bettor-arena#36` sibling |
| Final exact merged/cold-start convergence | future bettor leaf; `NOT_IMPLEMENTED` until siblings merge |

## Current machine authorities

- `catalog/variables.json`
- `contracts/*.schema.json`
- `modules/*.json`
- `profiles/*.json`
- `workloads/*.json`
- `policies/*.json`
- `src/runtime_env/cli.py`
- `tests/run-all.sh`
- `.github-delivery/registry.json`, receipts, and publications

PR and commit metadata remain publication truth. A documentation link does not promote a provider or consumer canary.
