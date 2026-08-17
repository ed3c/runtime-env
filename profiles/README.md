# `profiles/`

Owner: explicit composition of modules for one workload/runtime class.

## State Machine

```text
PROFILE_SELECTED
→ MODULES_RESOLVED
→ DEFAULTS_AND_SCOPES_CHECKED
→ CONFLICTS_REFUSED
→ PROFILE_RESOLVED
```

## DAG position and data flow

```text
modules/*
→ profiles/<id>.json
├─→ workloads/<id>.json
└─→ policies/<id>.json
      ↓
 runtime reducer / sync
      ↓
 consumer projection or exact host execution
```

| Input | Output | Downstream owner | Evidence ceiling |
|---|---|---|---|
| validated module IDs | portable module closure | workload/policy/runtime reducer | composition only |
| local/cloud runtime choice | explicit scope separation | consumer binding / host adapter | no provider readiness |

Profiles never contain secret values. Local and cloud opt-in profiles remain distinct; adding a cloud module must not make unrelated local execution require its credentials.

## Molecular leaf rule

A profile leaf may change one explicit composition when its module requirements are already admitted. Shared composition used by multiple terminal leaves belongs to a convergence PR. A resolved profile is not a successful workload, provider canary, consumer acceptance or production promotion.

For current closure state and Stack ownership, read `docs/architecture/SHADOW_ARCHITECT_LEDGER.md` and `docs/architecture/README.md`.