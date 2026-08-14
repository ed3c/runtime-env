# Traceability index — runtime-env document routing

```text
source / requirement
→ variable/module/profile/workload/policy decision
→ issue / molecular leaf or convergence owner
→ PR base/head and exact commit/tree
→ test and disagreement control
→ consumer projection / receipt
→ provider/product canary
→ Human Admit or rollback
```

## Four-repository documentation convergence

| Subject | Issue | PR | Stack class | Current publication state |
|---|---|---|---|---|
| Parent routing/integration contract | `ed3c/bettor-arena#35` | n/a | parent | open |
| Runtime Contract binding | `ed3c/runtime-env#29` | `ed3c/runtime-env#30` | independent sibling | **MERGED** at `4a333ccf106ef60bc6942b922b7f5efffb3876f5` |
| Instruction/Method binding | `ed3c/skills-shared#84` | `ed3c/skills-shared#85` | independent sibling | **MERGED** at `e3b327ad49c088f1962c33167ecd5ac9d28125fb` |
| Agent Shield product binding | `ed3c/agent-shield-monorepo#77` | `ed3c/agent-shield-monorepo#78` | independent terminal sibling | **MERGED** at `1af04c1ef5cb68eab198987feba008c93d3ec22f` |
| Bettor integration binding | `ed3c/bettor-arena#36` | `ed3c/bettor-arena#37` | independent sibling | **MERGED** at `1f94d3d77992a1396959a15b2ada7836c07bf300` |
| Exact merged/cold-start convergence | `ed3c/bettor-arena#38` | Bettor PR `#58` contributes the PDF/Stack audit; final cold-start convergence remains pending | convergence workstream | **UNBLOCKED**; Claude/Codex cold-start remains `NOT_EXERCISED` |

The old `Draft`/blocked descriptions are historical and must not be reused as current truth.

## PDF modular-integration audit

| Hop | Exact subject | Finding | Next owner |
|---|---|---|---|
| PDF source | `科技巨頭開源授權與AI框架v2.pdf`, pages 25–41 | proposes Agent Shield product/runtime/mobile/security topology; prose claim of full integration is not evidence | repository decision + exact implementation |
| Runtime implementation baseline | commit `4a333ccf106ef60bc6942b922b7f5efffb3876f5`, tree `68cda3d0ce7f1df26475a5d7322968194e794046` | immutable contract baseline evaluated before later docs-only audit commits | this repository |
| Bettor runtime projection | `.runtime-env/bindings/bettor-arena-local.json` pins `142e1ed278bf18f9c5c09186e28db16b623cdaee`, tree `1bd5c97e6f5519182d151055cf5f83fccb7ff5fa` | `STALE_SOURCE_PIN` relative to the evaluated baseline | explicit dry-run sync and review |
| Bettor Integration / Acceptance | deterministic catalog, proof, Context Capsules, MCP and bootstrap | implemented for named deterministic contracts | Bettor exact-subject gates |
| Agent Shield runtime foundation | issue `#38`, PR `#79`, merge `7d28a8cada03726b2b8966d9a229500f285d1b2b` | provider-neutral SPI implemented; no native provider PASS | Phase 3 leaves `#39–#43`, convergence `#44` |
| Agent Shield product/mobile | issues `#45–#53` | current live product routes remain incomplete/not exercised | product leaves and convergence |
| Agent Shield security/settlement | issues `#54–#64` | native security providers remain not implemented | security leaves and convergence |
| Bettor reference consumer | issues `#65–#75` | consumer and carrier/origin acceptance not exercised | Phase 6 terminal/convergence owners |

Canonical audit documents:

- [`../integration/README.md`](../integration/README.md)
- [`../integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md`](../integration/BETTOR_PDF_MODULAR_INTEGRATION_AUDIT.md)
- [`../integration/AGENTS.md`](../integration/AGENTS.md)
- Bettor PR `#58`, a true child of Bettor PR `#57`

The repository branch `docs/bettor-agent-shield-pdf-audit-2026-08-14` currently points at the default-branch audit state. The connector writes landed directly on `main`; there is no separate runtime-env PR for these documentation commits.

## Git Town ownership

This repository has no admitted `.git-town.toml`. The PDF domain-product Stack belongs to `agent-shield-monorepo`:

```text
Phase 3 #38–#44  runtime fabric
Phase 4 #45–#53  product/mobile
Phase 5 #54–#64  security/hardware/settlement
Phase 6 #65–#75  Bettor reference consumer
```

Use the canonical Agent Shield `docs/implementation/STACKED_IMPLEMENTATION_PLAN.md` and GitHub base/head metadata. Git Town synchronization is branch-movement evidence only.

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
- Bettor's checked `.runtime-env/requirements.json` and generated binding/workload/policies
- Agent Shield's `data/status/integration.json`, release manifests, exact issues/PRs and provider receipts

## Evidence boundary

A declared variable/module/profile/workload/policy can be validated without proving host/provider execution. Consumer projection proves deterministic resolution only for its pinned source. A live canary proves one selected execution subject. Product convergence and Human promotion remain separate.

Documentation completion does not imply runtime projection freshness, provider execution, GitHub/Forgejo equivalence, Claude/Codex cold-start, product integration or release promotion.