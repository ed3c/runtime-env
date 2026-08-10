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
runtime-env                   validate / list / render / check
          │
          ├── dotenv example output
          ├── GitHub Actions env mapping
          └── presence-only readiness receipt
```

The catalog is the security and vocabulary SSOT. Modules own requirement semantics. Profiles own workload composition. Generated examples and workflow fragments are projections, not additional sources of truth.

Validation is dependency-free Python so a repository can run it before installing its own toolchain. JSON Schema describes individual documents; the CLI owns cross-document invariants that JSON Schema alone cannot express, such as reference existence and profile default conflicts.
