# Four-repository integration — runtime contract view

| Repository | Plane | Runtime-env relationship |
|---|---|---|
| `skills-shared` | Instruction / Method | supplies selected Skill/runtime requirement names |
| `runtime-env` | Runtime Contract | resolves secret-free variable/module/profile/workload/policy closure |
| `bettor-arena` | Integration / Acceptance | consumes immutable bindings, combines them with modules/Skills, runs acceptance |
| `agent-shield-monorepo` | Domain Product / Reference Consumer | receives generated consumer surfaces and runs domain/provider canaries |

## Data flow

```text
Skill and PDF-derived requirements
→ classify portable runtime requirement versus domain-product behavior
→ runtime-env requirements/profile/workload/policy selection
→ dry-run sync plan
→ secret-free consumer binding/workload/policy/example
→ Bettor composition lock and proof subject
→ immutable CLI/MCP/bootstrap release
→ Agent Shield provider/product canaries
→ Bettor external-release acceptance
→ Human promotion or rollback
```

Actual values enter only in the execution plane selected by the consumer. They never flow back into runtime-env Git, Bettor locks, Skill bodies or portable receipts.

Local authoring may use Forgejo and cloud distribution GitHub, but origin equivalence belongs to the integration plane and requires an exact receipt.

## Current PDF integration finding

The PDF's monorepo target is the Agent Shield Domain Product plane, not `runtime-env` or `bettor-arena`. The current four-repository system is connected at the contract and deterministic acceptance layers, but it is not product-complete:

- Bettor's checked runtime binding is pinned to an older runtime-env commit than current `main`;
- Agent Shield's provider-neutral runtime SPI foundation is merged;
- Apple Container, E2B, OpenShell/tmux, mobile automation, native security, settlement and Bettor reference-consumer live evidence remain incomplete or unexercised.

Read:

- [`README.md`](README.md) for directory → State Machine ownership and the Git Town phase index;
- [`BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md) for exact subjects, states and required transitions;
- [`AGENTS.md`](AGENTS.md) for the nearest Agent audit contract.

A valid upstream declaration cannot proxy a fresh consumer binding; a fresh binding cannot proxy a provider canary; a provider canary cannot proxy product convergence or Human promotion.