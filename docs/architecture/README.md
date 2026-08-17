# Runtime architecture index

This directory is the Agent-readable architecture control plane for `runtime-env`. It maps repository directories to State Machines, DAG ownership, evidence ceilings, issues, and molecular Stack PR routing. Machine truth remains in JSON/schema/code/tests/receipts; this README is the route map.

## Read order

```text
README.md
→ AGENTS.md
→ CONTEXT.md
→ ARCHITECTURE.md
→ docs/INDEX.md
→ docs/architecture/README.md
→ STATE_MACHINES.md
→ SHADOW_ARCHITECT_LEDGER.md
→ nearest directory README
→ exact issue / PR / commit / receipt
```

## Repository DAG

```text
SOURCE_PROPOSAL / runtime requirement
        │
        ▼
catalog/ ── variable vocabulary + security metadata
        │
        ▼
modules/ ── provider/runtime requirement units
        │
        ▼
profiles/ ── explicit module composition
        │
        ├─────────────┐
        ▼             ▼
workloads/         policies/
fixed execution    carrier isolation
        │             │
        └──────┬──────┘
               ▼
src/runtime_env/ ── typed reducers + transition guards
               │
               ├─────→ examples/ ── generated secret-free projections
               ├─────→ scripts/  ── bounded host adapters
               └─────→ consumer sync / verify
                              │
                              ▼
                         tests/ controls
                              │
                              ▼
                exact host/provider/consumer canary
                              │
                              ▼
                 .github-delivery/ publication evidence
                              │
                              ▼
                    Human Admit / rollback
```

No arrow may be collapsed. `module exists` does not mean `provider runs`; `test PASS` does not mean `live canary PASS`; `issue closed` does not mean `operationally closed`.

## Directory → State Machine → DAG ownership

| Directory | State Machine | Upstream input | Downstream output | DAG role | Evidence ceiling |
|---|---|---|---|---|---|
| `catalog/` | `UNDECLARED → METADATA_VALIDATED → VARIABLE_DECLARED` | source/runtime requirement | canonical variable declaration | root vocabulary | declaration only |
| `contracts/` | `DOCUMENT → SHAPE_VALIDATED` | JSON subject | schema agreement | orthogonal validator | shape only |
| `modules/` | `MODULE_REQUESTED → REFERENCES_RESOLVED → MODULE_VALID` | catalog variables | requirement unit | capability leaf definition | declared, not live |
| `profiles/` | `PROFILE_SELECTED → MODULES_RESOLVED → DEFAULTS_CHECKED → PROFILE_RESOLVED` | modules | portable closure | composition node | resolved, not executed |
| `workloads/` | `WORKLOAD_SELECTED → ENV_BUILT → FIXED_ENTRYPOINT → RECEIPT` | profile + exact environment | bounded execution result | execution edge | exact invocation only |
| `policies/` | `POLICY_SELECTED → CARRIER_PROJECTION` | carrier requirements | secret-free policy | parallel composition edge | projection only |
| `src/runtime_env/` | typed cross-document reducers | all declarative planes | decisions + guards | central reducer | deterministic semantics |
| `scripts/` | host adapter lifecycle | admitted fixed inputs | metadata-only host receipts | terminal runtime adapter | exact host invocation only |
| `examples/` | `SOURCE_CLOSURE → GENERATED_PROJECTION` | CLI producer | deterministic example | generated leaf | no authority |
| `tests/` | `SUBJECT → POSITIVE/NEGATIVE CONTROL → VERDICT` | exact code/config | falsifiable result | verification fan-in | deterministic fixture unless live subject |
| `.github-delivery/` | `ARTIFACT → RECEIPT → PUBLICATION_ATTESTATION` | tracked artifact + GitHub state | publication evidence | delivery convergence | publication only |
| `docs/integration/` | `SOURCE_PROPOSAL → OWNER → EVIDENCE STATE` | PDF/article/cross-repo requirement | integration audit | cross-repo routing | documentation/audit only |

## Molecular implementation Stack

`runtime-env` does not claim a repository-owned Git Town configuration. We still record the molecular Stack topology that `git-town-stacked-pr-worker` must preserve. GitHub base/head metadata is publication truth.

```text
main
└─ #50 Shadow Architect convergence                    [convergence parent]
   ├─ #37 GitHub read-only monitor live closure       [terminal leaf]
   ├─ #38 Forgejo exact-host lifecycle live closure   [terminal leaf]
   ├─ #45 multi-Worker live closure                   [terminal leaf]
   └─ #51 current-head CI repair                      [terminal sibling, CONTRACT_CLOSED via PR #52]

#51 → PR #52 head CI #95 PASS → merged main cd926854... → main CI #97 PASS

remaining #37/#38/#45
→ #50 convergence
→ live receipts + zero residue
→ Human Admit / rollback
```

### Stack PR index

| Stack node | Issue / PR | Role | Closure evidence |
|---|---|---|---|
| Convergence | #50 / PR #53 | shared README/AGENTS/index/ledger | all leaves classified + current-head truth |
| GitHub monitor | #37 | terminal implementation leaf | real read-only fetch, pagination/rate, replay/failure/dedup, zero writes |
| Forgejo host | #38 | terminal implementation leaf | activation/health, credential canary, restore drill, rollback |
| Scheduler | #45 | terminal implementation leaf | admitted consumer concurrency, stale refusal, straggler reassignment, budget, zero residue |
| CI repair | #51 / PR #52 | merged terminal sibling | PR-head CI #95 PASS + merged-main CI #97 PASS |

A true child PR is used only when it consumes unmerged parent bytes. Otherwise terminal leaves are siblings from the same admitted base. Do not manufacture Stack ancestry for visual neatness.

## Data-flow closure rule

Every real-world problem from an issue, article, PDF, incident, or host observation must be represented as:

```text
claim/problem
→ classification: SOURCE_PROPOSAL | OBSERVED_GAP | IMPLEMENTED_CONTRACT | LIVE_EVIDENCE
→ repository + directory owner
→ State Machine transition
→ exact issue
→ implementation PR/commit
→ positive control
→ disagreement/negative control
→ live canary when applicable
→ receipt + residue result
→ closure state
```

Allowed closure states:

```text
CONTRACT_CLOSED
LIVE_CLOSED
PARTIAL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
FAIL
STALE_SOURCE_PIN
SKIPPED_BY_POLICY
```

GitHub `CLOSED` alone is not a runtime closure state.

## Shadow Architect monitor

Read [`SHADOW_ARCHITECT_LEDGER.md`](SHADOW_ARCHITECT_LEDGER.md) for the current exact-head assessment.