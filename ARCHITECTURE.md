# Architecture

```text
catalog/variables.json        one declaration per name
          │
          ▼
modules/*.json                provider/runtime requirements
          │
          ▼
profiles/*.json               workload composition
          │
          ▼
runtime-env                   validate / list / render / check / sync
          │
          ├── dotenv example output
          ├── GitHub Actions env mapping
          ├── presence-only readiness receipt
          └── explicit consumer projection
                    │
                    ├── .runtime-env/bindings/<id>.json
                    └── .runtime-env/examples/<id>.env.example
```

The catalog is the security and vocabulary SSOT. Modules own requirement semantics. Profiles own workload composition. Generated examples and workflow fragments are projections, not additional sources of truth.

Validation is dependency-free Python so a repository can run it before installing its own toolchain. JSON Schema describes individual documents; the CLI owns cross-document invariants that JSON Schema alone cannot express, such as reference existence and profile default conflicts.

Consumer projection is one-way and explicit. A clean source Git revision is
the provenance boundary; the consumer receives only the selected variable
metadata, safe defaults, hashes, and source commit/tree. It never receives
credential values. Consumer hooks validate their staged local projection and
therefore remain offline and independent of checkout layout.
