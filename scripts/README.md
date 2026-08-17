# `scripts/`

Owner: bounded host/runtime adapters for provider bootstrap, consumer CLI installation, repository-control-plane monitoring, Forgejo lifecycle, Git Town toolchain, multi-Worker scheduling, JDK verification and local-runtime verification.

## State Machine role

Scripts implement fixed transitions selected by checked-in workloads; they do not define arbitrary execution policy.

```text
ADMITTED_FIXED_INPUT
→ PREFLIGHT / IDENTITY BINDING
→ BOUNDED HOST OPERATION
→ READBACK / CONTROL
→ METADATA-ONLY RECEIPT
→ CLEANUP / RESIDUE CHECK
```

## DAG position and data flow

```text
module/profile/workload
→ runtime reducer
→ scripts/<fixed-adapter>
→ host/provider/process/worktree
→ receipt
→ tests + live readback
→ terminal issue / convergence
```

| Adapter class | Terminal issue/lane | Required live closure |
|---|---|---|
| `github-control-plane-monitor.py` | #37 | exact read-only GitHub fetch + replay/failure/dedup proof |
| `forgejo-host-service.py` | #38 | activation/health/credential/restore/rollback on exact host |
| `multi-worker-scheduler.py` + canary | #45 | admitted consumer concurrency/stale/straggler/budget/zero residue |
| `git-town-toolchain.py` | repository-control-plane support | exact installed binary/doctor evidence; no merge authority |
| other bootstrap/verification scripts | matching workload issue | fixed subject-bound receipt |

Scripts must use fixed operations, bounded outputs, no credential printing, and explicit receipts. They never provide generic shell-over-MCP, arbitrary model-selected commands, semantic conflict auto-resolution, merge authority or consumer product semantics.

## Molecular PR rule

One terminal script lane may own its directly coupled test and workload changes. Shared registries, architecture README/AGENTS changes, aggregate evidence and release state belong to the convergence owner (#50). True Stack child ancestry is used only when a child consumes unmerged parent bytes.

Read the script, matching workload, matching test, exact issue and `docs/architecture/SHADOW_ARCHITECT_LEDGER.md` before use.