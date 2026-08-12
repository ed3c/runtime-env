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

## Four-repository documentation stack

| Subject | Issue | PR | Stack class | State |
|---|---|---|---|---|
| Parent routing/integration contract | `ed3c/bettor-arena#35` | n/a | parent | open |
| Runtime Contract binding | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | Draft |
| Instruction/Method binding | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | Draft |
| Agent Shield product binding | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | Draft |
| Bettor integration binding | `ed3c/bettor-arena#36` | `ed3c/bettor-arena#37` | independent sibling | Draft |
| Exact merged/cold-start convergence | `ed3c/bettor-arena#38` | future | convergence leaf | blocked by four PRs |

Exact open-PR heads are read from GitHub metadata. The convergence leaf records immutable merged commits/trees after all inputs exist; it must not create a branch from unmerged sibling bytes.

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

## Runtime evidence boundary

A declared variable/module/profile/workload/policy can be validated without proving host/provider execution. Consumer projection proves deterministic resolution and source identity; a live canary proves the selected execution subject. Secret material, authentication, and Human promotion remain environment-owned.

PR and commit metadata remain publication truth. Documentation completion does not imply provider execution, GitHub/Forgejo equivalence, cold-start route verification, or release promotion.
