# Documentation index

## Root routes

- [`../README.md`](../README.md) — repository entry and public CLI.
- [`../AGENTS.md`](../AGENTS.md) — repository-wide Agent procedure and safety boundaries.
- [`../CLAUDE.md`](../CLAUDE.md) — Claude thin projection.
- [`../CONTEXT.md`](../CONTEXT.md) — mutable current handoff.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — stable contract topology.

## PRD / requirement traceability

- [`../prd/README.md`](../prd/README.md) — requirement graph purpose, closure laws and update procedure.
- [`../prd/AGENTS.md`](../prd/AGENTS.md) — nearest Agent rules for requirement identity and evidence ceilings.
- [`../prd/requirements.json`](../prd/requirements.json) — machine-verifiable `REQ-*` graph from PRD requirement to owner, implementation, issue/PR lineage, controls and closure state.
- [`../contracts/prd-requirements.schema.json`](../contracts/prd-requirements.schema.json) — graph shape contract.

Before claiming that a PRD requirement is implemented or live, Agents must resolve its `REQ-*` entry and then inspect the named machine authority and evidence subject. GitHub issue state alone is not requirement closure.

## Architecture / Shadow Architect routes

- [`architecture/README.md`](architecture/README.md) — directory → State Machine → DAG → evidence owner map and molecular Stack index.
- [`architecture/AGENTS.md`](architecture/AGENTS.md) — Tech Lead / Shadow Architect issue-audit procedure.
- [`architecture/STATE_MACHINES.md`](architecture/STATE_MACHINES.md) — stable transition definitions.
- [`architecture/DOCUMENT_ROUTING.md`](architecture/DOCUMENT_ROUTING.md) — document routing contract.
- [`architecture/SHADOW_ARCHITECT_LEDGER.md`](architecture/SHADOW_ARCHITECT_LEDGER.md) — current exact-head/live-evidence convergence ledger. Mutable; never treat as machine implementation SSOT.
- [`architecture/dual-agent-runtime/README.md`](architecture/dual-agent-runtime/README.md) — merged Dual-Agent contracts/transport/identity State Machines, Process/Git DAGs, data flow, molecular Stack, closure matrix, and Local Handoff queues.
- [`architecture/dual-agent-runtime/AGENTS.md`](architecture/dual-agent-runtime/AGENTS.md) — nearest Agent authority, path leases, evidence non-substitution laws, stop conditions, and zero-context continuation for the Dual-Agent runtime.
- [`architecture/dual-agent-runtime/stack-index.json`](architecture/dual-agent-runtime/stack-index.json) — machine-readable exact implementation heads/trees/runs/merges, closure actions, live frontier, and handoff packets.

For completion, integration, issue-closing, article/PDF, provider, scheduler, Forgejo or Stack work, Agents must read the architecture README + AGENTS + current ledger before claiming PASS. Dual-Agent work must additionally read the nearest Dual-Agent route above.

## Integration routes

- [`integration/README.md`](integration/README.md) — directory → State Machine → data-flow ownership for cross-repository integration.
- [`integration/AGENTS.md`](integration/AGENTS.md) — nearest Agent contract for audits in `docs/integration/`.
- [`integration/CROSS_REPO_INTEGRATION.md`](integration/CROSS_REPO_INTEGRATION.md)
- [`integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md) — exact runtime pin, Bettor integration, Agent Shield status and Git Town Stack verdict for the PDF architecture.
- [`traceability/TRACEABILITY_INDEX.md`](traceability/TRACEABILITY_INDEX.md)

## Existing detailed contracts

- [`modular-consumer-contract.md`](modular-consumer-contract.md) — desired/resolved consumer lifecycle.
- [`public-consumption.md`](public-consumption.md) — credential-free consumption and SHA/tag pinning for public consumers.
- [`local-integration.md`](local-integration.md) — local Forgejo/host integration.
- [`local-credential-broker.md`](local-credential-broker.md) — secret/session ownership.
- [`runtime-topology.md`](runtime-topology.md) — execution-plane distinctions.
- [`skill-runtime-inventory.md`](skill-runtime-inventory.md) — Skill/runtime inventory.
- [`jdk-runtime.md`](jdk-runtime.md) — local/cloud JDK boundary.
- [`runtimes/forgejo-localhost.md`](runtimes/forgejo-localhost.md) — Forgejo runtime details.

## Nearest-directory rule

After the PRD and architecture routes, read the nearest directory README/AGENTS and exact machine authority. Current key routes include:

```text
prd/README.md
prd/AGENTS.md
catalog/README.md
contracts/README.md
contracts/dual-agent/README.md
docs/architecture/dual-agent-runtime/README.md
docs/architecture/dual-agent-runtime/AGENTS.md
catalog/README.md
modules/README.md
profiles/README.md
workloads/README.md
policies/README.md
src/runtime_env/README.md
scripts/README.md
examples/README.md
tests/README.md
.github-delivery/README.md
```

README/ledger text explains ownership and evidence ceilings. JSON/schema/code/tests/receipts plus exact GitHub provider state remain the authoritative subjects.