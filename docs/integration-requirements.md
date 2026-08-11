# Runtime integration completion requirements

## Purpose

This document tells an Agent exactly what must be true before it may say that a
`runtime-env` capability is integrated. It is both an execution specification
and a handoff document: a reader does not need the conversation that created it.

`runtime-env` is a secret-free control plane. It catalogs variable contracts,
composes modules into profiles, projects selected contracts into consumer
repositories, and runs fixed workload entrypoints with restricted environment
delivery and metadata-only receipts. It does not install every provider, start
every host service, supply consumer application code, or turn a repository MCP
declaration into compute.

The desired outcome is therefore not one global "everything" profile. The
desired outcome is independent evidence for every selected workload on its
actual execution host and, where applicable, in each consumer repository.

## Required reading and source of truth

An Agent performing integration work must read these files in order:

| Source | What it controls |
|---|---|
| `AGENTS.md` | Repository invariants, test-first procedure, and the route into local integration documentation. |
| `docs/local-integration.md` | Canonical checkout, credential placement, local Forgejo verification, and host-only stores. |
| `docs/integration-requirements.md` | Completion levels, acceptance evidence, and the work queue defined here. |
| `catalog/variables.json` | The only declaration of variable names and security metadata. |
| `modules/*.json` | Provider and runtime requirements that reference catalog variables. |
| `profiles/*.json` | Least-privilege compositions selected by workloads. |
| `workloads/*.json` | Fixed commands, host, mutation class, secret-delivery mode, and evidence contract. |
| `policies/*.json` | Carrier-native isolation settings synchronized into a consumer. |

Generated files under `examples/` and a consumer's `.runtime-env/` directory
are projections, not independent sources of truth. Change their generating
contract and regenerate them.

## Terms used in this document

| Term | Meaning |
|---|---|
| Canonical checkout | The clean Git checkout at `/Users/neon/runtime-env` from which catalog validation, synchronization, and trusted runtime-owned entrypoints run. |
| Consumer repository | A target repository that receives a pinned, secret-free `.runtime-env/` projection and supplies any target-relative workload scripts. |
| Execution plane | The host that actually runs a command: local macOS, GitHub Actions, Codex cloud, or another explicitly named host. A connector is not an execution plane. |
| Broker | A host process that resolves a value from the canonical dotenv, Keychain, provider session, or private file without exposing the value to the Agent. |
| Fixed entrypoint | A checked-in command from `workloads/*.json`; `workload run` does not accept an arbitrary trailing shell command. |
| Receipt | A private, metadata-only record binding the attempted workload, result, source revision, and evidence hashes without storing child output or secret values. |
| Live acceptance | A real command against the named host capability, not a schema check, rendered template, mock, fixture, or declaration. |

## Integration maturity levels

Every workload-to-consumer pairing is assessed independently. Report its exact
level; never collapse these levels into a single word such as "supported".

| Level | Name | Required evidence |
|---|---|---|
| L0 | Declared | Catalog, module, profile, workload, and policy documents parse and `./runtime-env validate` succeeds. |
| L1 | Projected | `runtime-env sync --apply` created the explicitly selected binding, workload, and policies; `sync --check` reports no drift. |
| L2 | Configured | `runtime-env check --profile <profile> --env-file /Users/neon/runtime-env/.env` exits `0`. This proves names/defaults only, not service availability or credential validity. |
| L3 | Host-ready | Required binaries, target-relative files, local services, provider sessions, private paths, and network routes exist on the named execution plane. No secret value is printed during the checks. |
| L4 | Live-passed | Every required fixed entrypoint exits successfully against the real dependency and produces the workload's required receipt/control evidence. |
| L5 | Consumer-accepted | The consumer's staged projection verifies offline, its own public-seam tests pass, and its accepted workload receipt is bound to the intended consumer revision. |

L0 is a catalog claim. L2 is a configuration claim. Neither is evidence of a
working integration. A local workload with no consumer-specific code may stop
at L4; a workload that operates on a consumer is complete only at L5.

## Result states and failure taxonomy

The maturity level says how far integration has progressed. The result state
says what happened on the latest attempt.

| State | Use it when |
|---|---|
| `NOT_RUN` | No real acceptance attempt has been made for the current source and target revisions. |
| `PASSED` | The required command exited `0`, evidence was verified, and no forbidden state changed. |
| `BLOCKED` | A named prerequisite is absent or unreachable, so the real acceptance command cannot validly complete. Record the exact missing dependency and the safe command that observed it. |
| `FAILED` | Prerequisites were present and the real command ran, but authentication was refused, output/evidence was invalid, or a policy was violated. |

Do not convert `BLOCKED` into `PASSED` by weakening isolation, adding an
unscoped secret, substituting a mock, or skipping an entrypoint. Distinguish:

- **missing**: required input or program does not exist;
- **unreachable**: a service or execution plane cannot be contacted;
- **refused**: a reachable service rejected authentication or authorization;
- **invalid**: a contract, receipt, or target state did not meet its schema or policy;
- **unsafe**: permissions, ownership, helper configuration, or secret routing violate the security contract.

After three unsuccessful attempts at the same problem, stop. Record the three
attempts, exact redacted errors, why each failed, and the smaller or simpler
route that should be evaluated next.

## Security and value-placement requirements

For local execution there is one canonical host dotenv:
`/Users/neon/runtime-env/.env`. It must be a user-owned regular file, mode
`0600`, ignored by Git, and rejected if it is a symlink or contains unknown
names. It is an import/staging surface for the broker, not a file made visible
inside an agent sandbox.

A consumer repository must not create its own `.env` to consume runtime-env.
It receives only secret-free generated projections. Session stores and private
files also remain outside dotenv and outside the consumer:

- Codex CLI login remains in its configured OS keyring or Codex-owned auth file.
- Claude Code subscription login remains in Claude-owned host state and Keychain.
- Antigravity login and artifacts remain under its host-owned state directory.
- Browser cookies and local storage remain in broker-owned profiles outside Git.
- App Store Connect private-key bytes remain in a broker-owned `0600` file;
  dotenv may contain only the allowed path metadata.
- GitHub Actions and Codex cloud values are configured in those remote execution
  planes. A local dotenv does not authorize copying them into a remote runner.

An acceptance receipt may contain names, presence states, paths approved by the
contract, exit codes, revisions, byte counts, and hashes. It must not contain
credential values, cookies, tokens, private-key bytes, child stdout, or child
stderr.

## Consumer repository acceptance

Complete these steps separately for each consumer and selected capability.
The consumer selects the smallest profile closure; no consumer receives all
profiles by default.

1. Identify the consumer Git root and the exact runtime capability it needs.
2. Select one profile, and explicitly select a workload and every required
   carrier policy. Omitting `--workload` or `--policy` is not workload support.
3. Verify that every target-relative fixed entrypoint in the selected workload
   exists in the consumer and is covered by a public-seam test. Runtime-env does
   not generate those application scripts.
4. From a clean canonical runtime-env checkout, run `sync` without `--apply` and
   review `WOULD-CREATE` and `WOULD-UPDATE` paths.
5. Run the same command with `--apply`. Commit the generated binding, dotenv
   example, workload projection, and policy projections in the consumer.
6. Pin a compatible runtime-env CLI in the consumer development environment.
7. Add an offline pre-commit check using `runtime-env verify-consumer
   --target-root "$(git rev-parse --show-toplevel)" --binding <binding>
   --staged`. The hook must not access a sibling checkout or the network.
8. Run `sync --check` against the canonical source revision and resolve any
   drift before live acceptance.
9. Run each required fixed entrypoint on its named execution plane. Verify the
   receipt, control evidence, mutation boundary, and consumer revision.
10. Run the consumer's full test suite and `git diff --check`; review the staged
    diff before committing with a message that explains why the integration is
    needed.

The generated consumer surface is:

| Consumer path | Acceptance purpose |
|---|---|
| `.runtime-env/bindings/<binding>.json` | Pinned profile closure and immutable runtime-env source receipt. |
| `.runtime-env/examples/<binding>.env.example` | Secret-free names/defaults for documentation; never a value store. |
| `.runtime-env/workloads/<binding>.json` | Fixed entrypoints, mutation class, evidence, and control projection. |
| `.runtime-env/policies/<policy>.json` | Native carrier settings and cross-carrier isolation projection. |

## Live acceptance matrix

The table below is the required work queue. A row is not complete merely
because its workload document exists. Replace `NOT_RUN` with `PASSED`,
`BLOCKED`, or `FAILED` only after recording a dated receipt for the exact source
and target revisions. For workloads with multiple consumer repositories, copy
the row once per consumer rather than overwriting evidence from another target.

| Workload | Profile | Real target prerequisite | Required entrypoints | Mutation | Initial state |
|---|---|---|---|---|---|
| `agy-gemini36-flash-high-replay` | `agy-gemini36-flash-high-local` | Target contains the admitted replay-request executor and verification script; host `agy` session exposes the exact admitted model. | `inventory`, `replay` | workspace | `NOT_RUN` |
| `bettor-arena-proof` | `bettor-arena-runtime-local` | Bettor-arena target contains `loopctl` and runtime checks; Claude, Codex, agy, research CDP, stealth browser, approval receipt, peer repositories, and local Forgejo are independently available. | All 11 entrypoints declared in `workloads/bettor-arena-proof.json`. | workspace | `NOT_RUN` |
| `dr-research-loop` | `dr-research-loop-local` | Target contains `loop_wiki/engine.sh` and the selected topic verifier; required browser and independent agent carriers are live. | `engine`, `verify` | workspace | `NOT_RUN` |
| `forgejo-delivery-loop` | `forgejo-delivery-keychain-local` | Forgejo is reachable at loopback port `3000`; the URL-scoped Git helper chain is reset then `osxkeychain`; authenticated read-only canary succeeds. | `broker-selftest`, `credential-canary` | read-only | `BLOCKED`: the 2026-08-11 local probe found `localhost:3000` unreachable. |
| `gemini-conversation-research` | `gemini-conversation-research-local` | Target contains the Node/Bun browser-runtime scripts; the dedicated logged-in browser and file-only sink are live. | `carrier-gate`, `extract`, `guided-edge` | workspace | `NOT_RUN` |
| `ios-testflight-beta` | `ios-testflight-ship-local` | Admitted iOS target revision, Xcode/JDK, signing identity, team metadata, App Store Connect broker, and explicit release authority are present. | `upload` | external release | `NOT_RUN`; never run upload merely to test configuration. |
| `ios-testflight-verify` | `ios-testflight-ship-local` | Same broker and toolchain as TestFlight upload, but no release mutation is authorized or required. | `preflight`, `verify-asc` | read-only | `NOT_RUN` |
| `local-jdk-verify` | `java-build-local` | `JAVA_HOME` names a real JDK whose `java` and `javac` feature releases agree and can compile/run a probe. | `verify` | read-only | `NOT_RUN`; the repository selftest passed, but that fixture is not a current live workload receipt. |
| `repo-wiki-converge` | `repo-wiki-converge-local` | Target contains author, claim-verification, and knowledge-graph ingest implementations; Antigravity carrier and output paths are valid. | `author`, `verify`, `ingest` | workspace | `NOT_RUN` |
| `stealth-browser-mcp` | `gemini-conversation-research-local` | Stealth-browser source root, dependencies, broker-owned profile root, bounded file sink, and loopback transport are available. | `serve`, `test` | workspace | `NOT_RUN` |

For each row, the acceptance record must include:

- runtime-env commit and tree hash, plus clean/dirty state;
- consumer path, commit and tree hash, plus clean/dirty state when a consumer is used;
- profile, workload, entrypoint, execution host, and mutation class;
- environment check result containing names/presence only;
- dependency and service canaries used to establish L3;
- live command exit status and private receipt path;
- control evidence path or hash required by the workload;
- final maturity level and result state;
- a redacted blocker with an owner or next action when state is `BLOCKED` or `FAILED`.

## Commands that establish evidence

Run repository-level contract verification from the canonical checkout:

```bash
cd /Users/neon/runtime-env
./runtime-env validate
bash tests/run-all.sh
git diff --check
./runtime-env local-env doctor
```

`local-env doctor` establishes metadata hygiene only. To assess one profile's
configuration, run:

```bash
./runtime-env check \
  --profile <profile> \
  --env-file /Users/neon/runtime-env/.env
```

Use this shape for explicit consumer synchronization:

```bash
./runtime-env sync \
  --profile <profile> \
  --binding <binding> \
  --workload <workload> \
  --policy <required-policy> \
  --target-root <absolute-consumer-root>

# Apply only after reviewing the dry-run receipt.
./runtime-env sync \
  --profile <profile> \
  --binding <binding> \
  --workload <workload> \
  --policy <required-policy> \
  --target-root <absolute-consumer-root> \
  --apply

./runtime-env sync \
  --profile <profile> \
  --binding <binding> \
  --workload <workload> \
  --policy <required-policy> \
  --target-root <absolute-consumer-root> \
  --check
```

Use the workload runner only with a checked-in entrypoint:

```bash
./runtime-env workload run \
  --id <workload> \
  --entrypoint <fixed-entrypoint> \
  --target-root <absolute-target-root> \
  --env-file /Users/neon/runtime-env/.env \
  --json
```

An entrypoint with `secret_delivery=broker-only` must use its dedicated adapter;
ordinary environment injection is not a substitute. A read-only workload must
fail if it changes the target Git state. An external-release workload requires
explicit human authorization for the release action even when L0 through L3
are already satisfied.

For the canonical local Forgejo route, use:

```bash
bash scripts/verify-local-runtime.sh \
  --canonical-path /Users/neon/runtime-env
```

This verifier proves only the local catalog, Forgejo reachability, credential
helper or explicit fallback contract, authenticated read-only user canary, and
output redaction. It does not prove GitHub Actions, Codex cloud, browser login,
or any other workload.

## Current measured baseline

The following snapshot was measured on 2026-08-11 before this requirements
document was added, at runtime-env commit `b8c768d23cf3`:

- `./runtime-env validate` reported 69 variables, 44 modules, 24 profiles, 10
  workloads, and 3 policies.
- All 23 `tests/test_*.sh` public-seam test files passed through
  `bash tests/run-all.sh`.
- `local-env doctor` found all 69 declared names structurally valid and reported
  10 names present; it printed no values.
- Profile-level `check` exited `0` for 12 of the 24 profiles. This means only
  that required names or safe defaults were available.
- `scripts/verify-local-runtime.sh` validated the catalog and canonical path,
  then exited `4` because Forgejo at `http://localhost:3000` was unreachable.

These measurements establish catalog health and a starting work queue. They do
not establish that 12 profiles or 10 workloads are live. Future Agents must
rerun the commands and attach new receipts rather than copying these numbers
into a completion claim.

## Completion definition

The integration program is complete only when all of the following are true:

1. The canonical catalog and full test suite pass from a clean revision.
2. Every selected consumer has a pinned, drift-free projection and offline
   staged verification.
3. Every target-relative entrypoint exists and passes a public-seam test in its
   owning repository.
4. Every non-release row in the live acceptance matrix has current `PASSED`
   evidence at its required maturity level.
5. Release rows have current read-only preflight evidence; an actual external
   release is required only when separately authorized.
6. Every secret and session remains in its declared execution plane, and all
   receipts are metadata-only.
7. No row is described as complete while its latest state is `NOT_RUN`,
   `BLOCKED`, or `FAILED`.

If work must continue in repositories or execution planes outside the current
authorized scope, the Agent stops after producing the matrix row, exact target,
required command, and blocker. It must not silently broaden filesystem access,
copy a credential, start an external release, or claim completion on another
repository's behalf.
