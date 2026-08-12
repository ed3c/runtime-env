# Four-repository integration — runtime contract view

| Repository | Plane | Runtime-env relationship |
|---|---|---|
| `skills-shared` | Instruction / Method | supplies selected Skill/runtime requirement names |
| `runtime-env` | Runtime Contract | resolves secret-free variable/module/profile/workload/policy closure |
| `bettor-arena` | Integration / Acceptance | consumes immutable bindings, combines them with modules/Skills, runs acceptance |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | receives generated consumer surfaces and runs domain/provider canaries |

## Data flow

```text
Skill requirements
→ runtime-env requirements/profile/workload/policy selection
→ dry-run sync plan
→ secret-free consumer binding/workload/policy/example
→ bettor composition lock and proof subject
→ immutable CLI/MCP/bootstrap release
→ Agent Shield consumer canaries
→ acceptance receipt + Human promotion
```

Actual values enter only in the execution plane selected by the consumer. They never flow back into runtime-env Git, bettor locks, Skill bodies, or portable receipts.

Local authoring may use Forgejo and cloud distribution GitHub, but origin equivalence belongs to the integration plane and requires an exact receipt.
