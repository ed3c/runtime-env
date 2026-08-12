# Local runtime integration contract

## Canonical local entrypoint

The intended checkout is `/Users/neon/runtime-env`. Agents should run catalog
and host verification from that directory; do not copy this repository's files
into each consuming project.

`AGENTS.md` is loaded only when a new chat starts. Editing it does not retrofit
the current chat. The root `AGENTS.md` therefore contains a short routing rule
to this document, while this file owns the detailed integration requirements.

## What the local checkout proves

Run:

```bash
cd /Users/neon/runtime-env
bash scripts/verify-local-runtime.sh \
  --canonical-path /Users/neon/runtime-env
```

The verifier checks the following independent facts:

1. the checked-out catalog validates;
2. the Forgejo loopback version endpoint is reachable;
3. either Git's credential helper can supply a username and secret entirely in
   memory, or the explicit fallback dotenv contract is complete and mode `0600`;
4. that credential passes an authenticated, read-only `/api/v1/user` canary;
5. no credential value is printed by the verifier, including under `bash -x`.

This does not prove that GitHub-hosted Actions, Codex cloud, or a ChatGPT GitHub
connector can reach localhost. Those are different execution planes. A
repository MCP declaration is also inert until a reachable local host runs the
typed MCP server.

## Values and exact storage locations

- Contract names and empty templates: `/Users/neon/runtime-env/catalog/`,
  `/Users/neon/runtime-env/modules/`, `/Users/neon/runtime-env/profiles/`, and
  `/Users/neon/runtime-env/examples/`.
- Canonical host-only dotenv entry: `/Users/neon/runtime-env/.env`, mode
  `0600`, owned by the local user, untracked, and ignored by Git. It is an
  import/staging surface for the host broker, not a file that is copied into
  consumer repositories or mounted into an agent sandbox.
- Preferred Git credential source: macOS Keychain through
  `credential.helper=osxkeychain`; Git resolves it through
  `git credential fill` without the Agent reading the Keychain database.
- Untracked fallback file:
  `~/.config/runtime-env/secrets/forgejo-local.env`, mode `0600`.
- Existing plaintext legacy source: `~/.git-credentials`. The verifier may read
  it only through Git's credential helper and must not print credential values.
- Forgejo password parameters: `FORGEJO_URL`, `FORGEJO_USERNAME`, and
  `FORGEJO_PASSWORD`.
- Typed API opt-in: `FORGEJO_TOKEN`; the current Chrome/helper delivery loop
  does not consume this variable automatically.

The fallback can be selected explicitly without sourcing it into the shell:

```bash
bash scripts/verify-local-runtime.sh \
  --canonical-path /Users/neon/runtime-env \
  --env-file ~/.config/runtime-env/secrets/forgejo-local.env
```

Absence, refusal, and inability remain distinct: no credentials is a missing
runtime input; an invalid credential is an authentication refusal; an
unreachable localhost service is an execution-plane failure. Do not fix one by
widening another plane's permissions.

The canonical dotenv metadata check is:

```bash
cd /Users/neon/runtime-env
./runtime-env local-env init   # first use only; creates blank 0600 file
./runtime-env local-env doctor
./runtime-env local-env reconcile # preserve values and organize scope sections
credential-broker-command | ./runtime-env local-env set --name NAME --stdin
./runtime-env local-env migrate-forgejo-keychain # after filling Forgejo username/password
```

Never place a credential literal on the command line. `local-env set --stdin`
accepts exactly one non-empty line, validates the catalog name and destination
metadata, preserves mode `0600`, and reports only the updated name. A legacy
consumer dotenv must first be made user-owned mode `0600`; after its declared
values have been brokered into this canonical file, the consumer must stop
depending on that legacy dotenv. Do not paste values into chat. A synchronized
consumer reads its secret-free binding while the local
broker resolves values from this one canonical file; the dotenv itself is not
copied to that consumer.

Install the committed consumer-verification CLI once per selected runtime-env
revision with `bash scripts/install-consumer-cli.sh`. This installs committed
bytes under `~/.local/lib/runtime-env/<commit>/` and exposes
`~/.local/bin/runtime-env`; consumer hooks must not point at a sibling checkout
or source an application-local dotenv. Re-run the installer after intentionally
updating and re-synchronizing the catalog revision.

It rejects symlinks, the wrong owner, any mode other than `0600`, unknown
variable names, and a catalog-local dotenv that Git would track. It reports
only names and `PRESENT`/`EMPTY`; it never prints values. This is a redaction
control, not a filesystem sandbox: the agent process must also be unable to
open `/Users/neon/runtime-env/.env` directly.

The Forgejo migration command is the only component allowed to bridge the
`forgejo-local-password` module into Git credentials. It reads the private
dotenv inside the local process, passes the password to Git helpers over stdin,
and suppresses helper output. It refuses any non-loopback URL or port other
than 3000. The commit point is deliberately last: `FORGEJO_PASSWORD` is cleared
only after Keychain store/get, URL-scoped helper configuration, plaintext-store
erase/get, and `git credential fill` all agree. A failed intermediate step
leaves the dotenv password available for recovery.

Normal post-migration delivery uses the `forgejo-delivery-keychain-local`
profile and fixed `forgejo-delivery-loop` workload. That profile has no
variables: the child receives neither `FORGEJO_PASSWORD` nor `FORGEJO_TOKEN`.
The live canary inherits only the runner's safe host surface (including `HOME`)
and executes runtime-env's own versioned verifier, not consumer-repo code. The
verifier runs in `--credential-helper-only` mode, invokes `git credential fill`,
requires the effective `credential.http://localhost:3000.helper` chain to be
exactly reset-then-`osxkeychain`, and refuses both dotenv fallback and
`store`/shell helpers. Its child `PATH` is replaced with the fixed
system path `/usr/bin:/bin:/usr/sbin:/sbin`; runtime-env records output as hashes
rather than returning the stream to the Agent. The credential entrypoint refuses
a dirty or unversioned catalog root, and the receipt binds the runtime-env HEAD,
tree, dirty state, and read-only target policy result. Consumer repositories
must not add a second `.env`.

The sections come from catalog metadata, not hand-written comments.
`local-only` identifies host paths, loopback services, and local carrier
selectors. `cloud-runtime` identifies remote-service inputs even though their
values remain staged in this one local file. `portable` identifies selectors
shared by both planes. Reconciliation preserves values and rewrites all three
sections without emitting them.

## Session and private-file locations that never move into dotenv

| Capability | Host-only location | Agent-visible representation |
|---|---|---|
| Codex CLI ChatGPT login | OS keyring or `~/.codex/auth.json`, according to Codex configuration | authenticated/not-authenticated receipt only |
| Claude Code subscription login | macOS Keychain and Claude-owned host state | authenticated/not-authenticated receipt only |
| Antigravity `agy` login and artifacts | `~/.gemini/antigravity-cli/` | exact model inventory plus file-output canary receipt |
| Stealth-browser login profiles | `$STEALTH_PROFILE_ROOT/<name>/state.json`; recommended `/Users/neon/.local/share/runtime-env/stealth-browser/profiles`, directories `0700`, files `0600`, outside every Git checkout | typed browser operation plus metadata-only receipt |
| App Store Connect private key | `~/.appstoreconnect/private_keys/AuthKey_<KEYID>.p8` or another broker-owned `0600` path | `verify_asc`/upload receipt only |

Do not copy, bind-mount, upload, render, or synchronize any of these stores.
Render the dedicated `<stealth-profile-root>` placeholder into host sandbox deny
rules; denying the historical `<stealth-browser-root>/profiles` path does not
protect the new broker-owned credential store.
`ASC_KEY_PATH` may identify the host file to the broker, but the `.p8` bytes are
never dotenv content. A logged-in browser is also a credential store: cookies
and localStorage are credential material even when no API key is visible.

OpenShell provider bootstrap receipts live at
`~/.local/state/runtime-env/receipts/openshell/<provider>.json`, mode `0600`.
They contain carrier/provider/status metadata only. They do not replace the
carrier-owned session source and are never synchronized into a repository.

## Integration completion contract

This section defines when an Agent may claim that a `runtime-env` capability is
integrated. Runtime-env is a secret-free control plane: it catalogs variable
contracts, projects selected contracts, and runs checked-in workload
entrypoints. It does not install every provider, start host services, supply
consumer application code, or turn a connector declaration into compute.

The goal is not a global "everything" profile. Each workload and consumer pair
must independently prove the capability it selects.

### Terms

| Term | Meaning |
|---|---|
| Consumer repository | A target repository that receives a pinned, secret-free `.runtime-env/` projection and supplies target-relative workload scripts. |
| Execution plane | The named host that runs the command, such as local macOS, GitHub Actions, or Codex cloud. A connector is not an execution plane. |
| Fixed entrypoint | A command checked into `workloads/*.json`; the runner accepts no arbitrary trailing command. |
| Live acceptance | A fixed entrypoint run against the real dependency, not a schema check, render, mock, or fixture. |
| Receipt | A private metadata-only record binding source revisions, the attempted workload, result, and evidence hashes without storing secret values or child streams. |

### Integration maturity levels

Report the exact level for each workload and consumer pair. Do not collapse the
levels into the ambiguous word "supported."

| Level | Name | Required evidence |
|---|---|---|
| L0 | Declared | `./runtime-env validate` succeeds for the catalog, modules, profiles, workloads, and policies. |
| L1 | Projected | Explicit `sync --apply` created the selected binding, workload, and policies; `sync --check` reports no drift. |
| L2 | Configured | `check --profile <profile> --env-file /Users/neon/runtime-env/.env` exits `0`. This proves names and defaults only. |
| L3 | Host-ready | Required binaries, target files, services, sessions, private paths, and routes exist on the named execution plane. |
| L4 | Live-passed | Every required fixed entrypoint exits successfully against the real dependency and produces the declared receipt/control evidence. |
| L5 | Consumer-accepted | The consumer's staged projection verifies offline, its public-seam tests pass, and live evidence is bound to the intended consumer revision. |

L0 and L2 are not live-integration claims. A runtime-owned workload with no
consumer code may stop at L4; a consumer workload is complete only at L5.

### Result states

| State | Meaning |
|---|---|
| `NOT_RUN` | No real attempt exists for the current source and target revisions. |
| `PASSED` | The required command exited `0`, evidence passed, and no forbidden state changed. |
| `BLOCKED` | A named prerequisite is absent or unreachable. Record the safe command that observed it and the next action. |
| `FAILED` | Prerequisites existed and the real command ran, but authentication, evidence, or policy validation failed. |

Keep missing input, unreachable service, refused authentication, invalid
evidence, and unsafe permissions as distinct blockers. Do not turn a blocker
into a pass by weakening isolation, adding an unscoped secret, substituting a
mock, or skipping an entrypoint. After three unsuccessful attempts at the same
problem, including any combination of `BLOCKED` and `FAILED`, stop and record
the commands, redacted errors, reasons, and a simpler route to evaluate.

### Fixed adapters and unresolved workload placeholders

`runtime-env workload run` deliberately refuses any command containing an
unresolved `<placeholder>`. Before running a placeholder-bearing workload, make
a test-first catalog/CLI change that does one of the following:

1. replace the placeholder with one concrete, versioned fixed entrypoint; or
2. introduce a typed, allowlisted parameter contract with validation and no
   arbitrary-command surface.

Do not substitute text in a generated consumer projection or invoke the command
outside the runner and call it accepted. Current consumer workloads use fixed,
target-relative adapters; missing external targets, credentials, services, or
sessions remain separate L2/L3 blockers.

A workload with `secret_delivery=broker-only` has a separate prerequisite. Its
L3 evidence must name a dedicated broker adapter, its trusted implementation
path, the fixed adapter entrypoint, the store or session that remains outside
the Agent, and the metadata-only receipt. The generic workload runner is an
orchestrator, not that adapter. If the catalog does not map these facts, the row
is `BLOCKED`; an Agent must not infer an adapter from an executable name or run
the child directly and claim secret isolation.

### Consumer repository acceptance

A consumer repository must not create its own `.env` to consume runtime-env.
Local values come from the one canonical host dotenv or the host brokers above;
remote values belong to their remote execution plane. The consumer receives
only secret-free projections.

For each consumer and capability:

1. Select the smallest profile plus an explicit workload and all required
   policies. Omitting `--workload` or `--policy` is not workload support.
2. Verify that every target-relative entrypoint exists and has a public-seam
   test in the consumer. Runtime-env does not generate application scripts.
3. From a clean canonical checkout, review the `sync` dry run, then use
   `--apply`; follow it with `sync --check`.
4. Pin a compatible runtime-env CLI in the consumer and make its pre-commit hook
   run `runtime-env verify-consumer --target-root "$(git rev-parse
   --show-toplevel)" --binding <binding> --staged` without network or sibling
   checkout access.
5. Run every required fixed entrypoint on its execution plane, verify its
   receipt, control, mutation boundary, and source revisions, then run the
   consumer's full tests and `git diff --check`.
6. Run `accept-consumer` with the consumer's tracked hook verifier and a private
   receipt path. For an entrypoint whose external authority is single-use, pass
   its exact workload receipt with repeatable `--execution-receipt
   <entrypoint>=<absolute-path>`; do not retransmit merely to consolidate. Only
   the resulting `maturity=L5` receipt is an L5 claim.

The exact Agent procedure and current consumer-to-binding map live in
[`docs/l5-consumer-integration.md`](l5-consumer-integration.md).

Synchronization must produce the binding, secret-free dotenv example, workload
projection, and every selected policy under the consumer's `.runtime-env/`
directory. A missing mapping in the matrix below is not permission to invent
one: add and test an explicit mapping in the owning contract first.

### Live acceptance matrix

This is the concrete work queue. Known physical roots come from
`docs/skill-runtime-inventory.md`; that inventory proves only path existence.
`UNRESOLVED` means this repository has no authoritative mapping yet. Copy a row
for each additional consumer rather than replacing evidence from another.

| Workload | Consumer / target root | Binding and policies | Required entrypoints or gap | Current result |
|---|---|---|---|---|
| `agy-gemini36-flash-high-replay` | `/Users/neon/skill-bettor` | `skill-bettor-agy-replay`; no carrier policy | Public replay-contract test, model inventory, then the approved file-based replay. | `BLOCKED` above L3: the public replay test passes and the current `agy models` execution-plane canary passed on 2026-08-11. Sending the versioned replay payload to the external model still requires explicit data-transmission authority; no consolidated L5 receipt exists. |
| `bettor-arena-proof` | `/Users/neon/bettor-arena` | `bettor-arena-local`; `claude-code-native-isolation`, `codex-cli-native-isolation`, `codex-openshell-chatgpt-placeholder` | All 11 declared acceptance entrypoints and their separate broker adapters. | `BLOCKED` below L2/L5: the canonical main-tree binding and installed verifier gate are committed, but `EQUIVALENCE_APPROVAL_RECEIPT_PATH` is absent and the current equivalence proof records `live=NOT_EXERCISED` plus admitted-mirror drift. |
| `dr-research-loop` | `/Users/neon/skill-bettor` | `skill-bettor-dr-research`; all three carrier policies | Fixed `run-dr-acceptance.sh` routes a versioned topic through harness tests, real engine, and verify. | `BLOCKED` above L3: the current `agy models` canary and live public-citation verifier both passed on the host on 2026-08-11. The remaining engine entrypoint transmits the versioned proposal to an external model and requires explicit data-transmission authority. |
| `forgejo-delivery-loop` | Runtime-owned verifier; target may be any admitted local Git consumer | No consumer binding or carrier policy is required for the runtime-owned canary. | `broker-selftest`, `credential-canary`; must preserve the target Git state. | `PASSED` at L4 on the host execution plane on 2026-08-11; the earlier sandbox-only loopback failure is retained as failed evidence, not the final host result. |
| `gemini-conversation-research` | `/Users/neon/ts-skill-bettor` | `ts-skill-bettor-gemini-research`; no carrier policy | Three public adapter tests, fixed live extraction, and a dry-run guided decision edge; content sinks stay under `GEMINI_RESEARCH_RUN_ROOT`. | `BLOCKED` at L3: loopback CDP was reachable on 2026-08-11 but exposed zero pages and no logged-in Gemini conversation tab. |
| `ios-testflight-beta` | Broker implementation: `/Users/neon/ix-agy`; release target selected by `IOS_TARGET_ROOT` | `ix-agy-ios-beta`; no carrier policy | Fixed adapter tests and read-only preflight. Upload remains a separately authorized external mutation and is not part of ordinary acceptance. | `PASSED` at L5 readiness on 2026-08-11: skill tests, adapter test and the real target preflight passed against the configured iOS sample. This does **not** claim that a build was uploaded; release mutation remains separately authorized. Receipt: `/Users/neon/.local/state/runtime-env/receipts/l5-20260811/ix-agy-ios-beta-current.json`. |
| `ios-testflight-verify` | Broker implementation: `/Users/neon/ix-agy`; target selected by `IOS_TARGET_ROOT` | `ix-agy-ios-verify`; no carrier policy | Fixed adapter tests, target preflight, and read-only App Store Connect authentication verification. | `PASSED` at L5 on 2026-08-11: skill tests, adapter test, target preflight and real read-only App Store Connect authentication all passed. Receipt: `/Users/neon/.local/state/runtime-env/receipts/l5-20260811/ix-agy-ios-verify-current.json`. |
| `local-jdk-verify` | `/Users/neon/runtime-env` | No consumer binding or policy for the local verifier. | `verify`; real `JAVA_HOME`, matching `java`/`javac`, and compile/run receipt. | `PASSED` at L4 on 2026-08-11 with a clean runtime-env revision and compile/run receipt. |
| `repo-wiki-converge` | `/Users/neon/ix-agy` | `ix-agy-repo-wiki`; no carrier policy | Fixed author/verify/ingest adapter plus consumer and adapter public tests; mutable output is broker-owned. | `BLOCKED` above L3: `REPO_WIKI_RUN_ROOT` is user-owned mode `0700`, the explicit Python runtime is configured, and the adapter and 14 consumer tests pass. The broker output is empty, so verify correctly fails until author runs; author would transmit repository content to an external model and requires explicit authority. |
| `stealth-browser-mcp` | `/Users/neon/stealth-browser` | `stealth-browser-local`; no carrier policy | Isolated full tests plus a real stdio MCP handshake, tool listing, and `stealth_health` call. | `PASSED` at L5 on the local host: the isolated suite and real MCP stdio smoke passed with consumer HEAD/tree/status and ignored-file fingerprint unchanged. The current private receipt is `/Users/neon/.local/state/runtime-env/receipts/l5-20260811/stealth-browser-current.json`; inspect its `runtime_source` rather than copying this claim. |

Each row's acceptance record must include runtime-env commit/tree/dirty state;
consumer path and commit/tree/dirty state when applicable; profile, workload,
entrypoint, execution host, and mutation class; metadata-only configuration and
dependency checks; live exit status and private receipt path; control evidence;
final maturity/result; and a redacted next action for `BLOCKED` or `FAILED`.
Separate execution receipts plus terminal output are not a consolidated L5
acceptance record. Until a fail-closed verifier binds those receipts, the
consumer gate, and the public-seam test result into one current consumer
revision, report the row as no higher than L4.

### Current measured baseline

On 2026-08-11, before this completion contract was added, commit
`b8c768d23cf3` produced this baseline:

- `validate` reported 69 variables, 44 modules, 24 profiles, 10 workloads, and
  3 policies.
- All 23 `tests/test_*.sh` public-seam test files passed through
  `bash tests/run-all.sh`.
- `local-env doctor` found all 69 declared names structurally valid and 10
  names present without printing values.
- Profile `check` exited `0` for 12 of 24 profiles. That proves only required
  names or safe defaults.
- The canonical local verifier exited `4` because Forgejo at
  `http://localhost:3000` was unreachable.

Future Agents must rerun the commands and attach current receipts rather than
copying these numbers into a completion claim.

### Completion definition

Integration is complete only when the catalog and full tests pass from a clean
revision; every selected consumer has a pinned, drift-free projection; every
target-relative entrypoint exists and has public-seam coverage; every
non-release matrix row has current evidence at its required maturity level;
release rows have current read-only preflight evidence and separate authority
for mutation; secrets remain in their declared planes; and no row called
complete is `NOT_RUN`, `BLOCKED`, or `FAILED`.

When the next action requires another repository, credential, service, or
execution plane outside the authorized scope, stop with the exact target,
required command, and blocker. Do not broaden filesystem access, copy a secret,
start a release, or claim completion for that external system.
