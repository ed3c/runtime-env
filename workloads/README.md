# `workloads/`

Owner: fixed executable entrypoints, allowed environments, mutation/control classes, and receipt locations.

```text
workload selected → profile resolved → required names present → exact env built → fixed entrypoint → receipt
```

No trailing arbitrary command is allowed. Missing configuration is an explicit not-run/exit state, not PASS. Live credentials and sessions remain host/provider owned.
