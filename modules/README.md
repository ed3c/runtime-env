# `modules/`

Owner: one provider/runtime requirement unit per JSON file.

```text
module requested → variable references resolved → required/optional semantics checked → module valid
```

Modules may name actors, transports, providers, browsers, JDKs, Forgejo, E2B, or other runtime capabilities. Presence means declared, not installed, authenticated, exercised, or safe for production. Profiles compose modules.
