# `modules/`

Owner: one provider/runtime requirement unit per JSON file.

## State Machine

```text
MODULE_REQUESTED
→ VARIABLE_REFERENCES_RESOLVED
→ REQUIRED/OPTIONAL_SEMANTICS_CHECKED
→ MODULE_VALID
```

## DAG position and data flow

```text
catalog/variables.json
→ modules/<id>.json
→ profiles/<profile>.json
→ workload/policy selection
→ runtime reducer
→ exact execution/canary
```

| Input | Output | Downstream owner | Evidence ceiling |
|---|---|---|---|
| canonical variable names + security metadata | typed provider/runtime requirement unit | `profiles/` | declaration only |
| source/PDF/article capability requirement | explicit module ID | issue + implementation owner | not installation/authentication |

Modules may name actors, transports, providers, browsers, JDKs, Forgejo, E2B, scheduler or other runtime capabilities. Presence means **declared**, not installed, authenticated, exercised, isolated, performant, legally fit, or production-safe.

## Molecular leaf rule

A module-specific terminal PR owns only its module contract and directly matching tests. Shared profile registries, aggregate status and release evidence belong to a convergence PR. A terminal leaf must not claim live PASS unless an exact host/provider canary and receipt exist.

For current closure state and issue/Stack ownership, read `docs/architecture/SHADOW_ARCHITECT_LEDGER.md` and `docs/architecture/README.md`.