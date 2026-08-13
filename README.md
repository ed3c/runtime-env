# runtime-env

`runtime-env` is a secret-free, modular catalog of environment variable contracts for agent repositories. It records **names, requirements, safe defaults, and account links**—never credential values.

> **Agent route:** read [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md). Directory/state-machine ownership is summarized in [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).

The portable desired-state and resolved-binding lifecycle is specified in
[`docs/modular-consumer-contract.md`](docs/modular-consumer-contract.md).

The repository separates three concepts that are often mixed together:

1. A **variable** is declared once in `catalog/variables.json`.
2. A **module** describes one provider or runtime and marks variables required or optional.
3. A **profile** composes modules for one executable workload.

This prevents an optional cloud backend from making a local workflow demand unrelated API keys.

## Directory → state machine

| Directory | State-machine responsibility |
|---|---|
| [`catalog/`](catalog/README.md) | variable vocabulary and security metadata |
| [`contracts/`](contracts/README.md) | document shape validation |
| [`modules/`](modules/README.md) | provider/runtime requirements |
| [`profiles/`](profiles/README.md) | module composition |
| [`workloads/`](workloads/README.md) | fixed entrypoints and receipt shape |
| [`policies/`](policies/README.md) | carrier-native isolation projection |
| [`src/runtime_env/`](src/runtime_env/README.md) | CLI transitions and cross-file invariants |
| [`examples/`](examples/README.md) | generated secret-free projections |
| [`tests/`](tests/README.md) | positive, hollow, mutation, and public-seam controls |
| [`.github-delivery/`](.github-delivery/README.md) | delivery receipt/publication binding |

## Quick start

```bash
./runtime-env validate
./runtime-env list --kind profiles
./runtime-env list --profile skill-bettor-e2b
./runtime-env render --profile skill-bettor-e2b --format dotenv
./runtime-env render --profile agent-github-action-openai --format github-actions
./runtime-env check --profile skill-bettor-e2b --env-file .env
./runtime-env local-env init      # first use: blank, untracked, mode 0600
./runtime-env local-env doctor    # names and presence only; never values
./runtime-env local-env reconcile # preserve values; organize local/cloud/portable sections
./runtime-env local-env set-path --name CODEX_HOME --path /absolute/existing/path
credential-broker-command | ./runtime-env local-env set --name E2B_API_KEY --stdin
./runtime-env local-env migrate-forgejo-keychain # one-time localhost password migration
./runtime-env workload list
./runtime-env workload show --id ios-testflight-beta
./runtime-env workload show --id local-jdk-verify
./runtime-env workload run --id bettor-arena-proof --entrypoint prove-harness \
  --target-root /path/to/bettor-arena --env-file /path/to/runtime-env/.env --json
./runtime-env inventory skills --repo-root /path/to/consumer
```

Exit codes are part of the public contract:

| Exit | Meaning |
|---|---|
| `0` | Contract is valid or all required names are present |
| `2` | Catalog, profile, arguments, or dotenv input are invalid |
| `3` | Required configuration is absent; the workload did not run |

`check` prints variable names and presence states only. It never prints values.
`workload run` accepts only a checked-in fixed entrypoint; there is no trailing
arbitrary command surface. It verifies an optional dotenv is a user-owned
regular file with mode `0600`, constructs a minimal child environment, and
returns metadata plus a private `0600` receipt. Child stdout/stderr and dotenv
values are neither printed nor stored. A `none` workload refuses configured
secrets; provider/broker workloads refuse ordinary child-environment secret
injection and must use their dedicated adapter.
Each `entrypoint_environment` allowlist is exact: variables selected by the
profile but not named for that entrypoint are absent from its child. This lets
one host-only dotenv hold both `CLAUDE_CONFIG_DIR` and `CODEX_HOME` while the
existing macOS Keychain-backed Claude login receives neither override and the
Codex entrypoint receives only `CODEX_HOME`. Neither receives the other
carrier's authentication or configuration environment.

The canonical `.env` is mechanically grouped by each variable's required
`runtime_scope`: `LOCAL-ONLY HOST SETTINGS`, `CLOUD / REMOTE RUNTIME SETTINGS`,
and `PORTABLE RUNTIME SETTINGS`. `local-env reconcile` preserves assignments,
adds new empty names, and rewrites those sections without printing any value.
`local-env set --stdin` is the only general value-writing seam: the value stays
off argv and stdout, the destination must already be a user-owned `0600`
regular file, and the name must exist in the catalog.
The cloud section is still stored only in the host-owned dotenv; it identifies
the intended consumption plane and does not authorize copying the file into a
cloud runner.

`local-env migrate-forgejo-keychain` is the broker for the
`forgejo-local-password` module. It accepts only the local Forgejo endpoints on
port 3000, writes the credential to macOS Keychain through
`git credential-osxkeychain`, installs a URL-scoped helper override, verifies
the configured Git lookup in memory, removes the matching plaintext
`~/.git-credentials` record, and only then clears `FORGEJO_PASSWORD` in the
private dotenv. It never prints credential values. `FORGEJO_USERNAME` remains
as non-secret local configuration.

For an OpenShell sandbox, bootstrap the Codex ChatGPT provider once from a
trusted host terminal. OAuth components travel in the `openshell` child
environment, never argv, stdout, a repository, dotenv, or the sandbox:

```bash
python3 scripts/bootstrap-openshell-provider.py codex-chatgpt \
  --name codex-runtime-env \
  --receipt ~/.local/state/runtime-env/receipts/openshell/codex-runtime-env.json
```

The bootstrap strips all Claude/Anthropic variables before launching
OpenShell. It does not modify `CODEX_HOME`, `CLAUDE_CONFIG_DIR`,
`config.toml`, or `settings.json`. See
[`docs/local-credential-broker.md`](docs/local-credential-broker.md) for the
trust boundary and the separate Claude subscription route. Consumer sandboxes
also select `codex-openshell-chatgpt-placeholder`: Codex sends the provider's
opaque access-token and account-id placeholders through a custom HTTPS model
provider, so no sandbox-side `auth.json` is needed.

## Explicit consumer synchronization

`sync` exports a profile into a consuming repository without copying this
repository or any credential value:

```bash
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /path/to/bettor-arena

# Review the WOULD-CREATE / WOULD-UPDATE receipt, then write explicitly:
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /path/to/bettor-arena \
  --apply

# Read-only freshness check against this checked-out runtime-env revision:
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /path/to/bettor-arena \
  --check
```

The default is a dry-run. `--apply` is the only mode that writes. The source
must be a clean Git checkout with a credential-free `origin`; generated files
pin its repository URL, commit, and tree:

| Consumer path | Purpose |
|---|---|
| `.runtime-env/bindings/<binding>.json` | Portable profile closure and immutable source receipt |
| `.runtime-env/examples/<binding>.env.example` | Deterministic, secret-free dotenv projection |
| `.runtime-env/workloads/<binding>.json` | Fixed entrypoints, mutation class, receipt, and control projection |
| `.runtime-env/policies/<policy>.json` | Carrier-native settings and cross-carrier isolation projection |

A consumer pre-commit hook should validate all staged projections from its own
Git index. It must not invoke `sync`, access a sibling checkout, or use the
network: synchronization is an explicit maintenance action, while pre-commit
only prevents a partially staged or locally corrupted binding from landing.

Install the committed catalog and CLI behind a stable, host-local launcher:

```bash
bash scripts/install-consumer-cli.sh
runtime-env validate
```

The installer archives `HEAD` rather than working-tree bytes, stores it under
`~/.local/lib/runtime-env/<commit>/`, writes a metadata-only install receipt,
and atomically updates `~/.local/bin/runtime-env`. It refuses to replace an
unmanaged launcher. Ensure `~/.local/bin` is on `PATH`, then make the consumer
hook run:

```bash
runtime-env verify-consumer \
  --target-root "$(git rev-parse --show-toplevel)" \
  --binding bettor-arena-local \
  --staged
```

The verifier intentionally does not load the source catalog. A sibling path
such as `/path/to/runtime-env` is suitable for explicit maintenance sync, not
as the consumer hook's runtime dependency.

`--workload` and repeatable `--policy` are explicit. Omitting them preserves the
older profile-only projection; it must not be interpreted as workload or native
permission support.

## Skill-bettor profiles

| Profile | Requirement |
|---|---|
| `skill-bettor-local` | Ollama defaults; zero cloud keys |
| `skill-bettor-e2b` | `E2B_API_KEY` for real E2B acceptance |
| `skill-bettor-gemini` | `GEMINI_API_KEY` for Gemini-driven local Stagehand |
| `skill-bettor-sandbox-browser-cloud` | E2B, Gemini, and Browserbase cloud paths |
| `bettor-arena-local` | `OLLAMA_URL` defaults to the service root used by bettor-arena bootstrap |

The split follows the observed `skill-bettor` behavior: local Ollama is the default, while E2B and Gemini are explicit cloud opt-ins. Browserbase names are cataloged because the upstream environment contract names them, but the currently verified Stagehand path uses local Chromium.

Generated examples live in [`examples/`](examples/README.md). CI proves they equal current CLI output; edit the catalog, module, or profile instead of editing generated examples directly.

## Local Forgejo profiles

| Profile | Requirement |
|---|---|
| `forgejo-delivery-local-password` | Optional bootstrap input: `FORGEJO_USERNAME` and `FORGEJO_PASSWORD` when no helper/session is usable |
| `forgejo-delivery-local-api` | Opt-in typed API client: `FORGEJO_TOKEN`; not consumed by the current Chrome/helper loop |
| `forgejo-delivery-keychain-local` | Runtime-owned authenticated canary through `git credential fill`; no dotenv variable is injected |

Both default `FORGEJO_URL` to `http://localhost:3000`. Exact template, local
secret-store, Git credential helper, Keychain, legacy plaintext store, repo
identity, Chrome logical surface, and token UI route are listed in
[`docs/runtimes/forgejo-localhost.md`](docs/runtimes/forgejo-localhost.md).
The fixed `forgejo-delivery-loop` workload runs the catalog's offline
`broker-selftest` or live `credential-canary` from versioned runtime-env code
and emits a metadata-only receipt bound to the catalog HEAD/tree. The credential
canary refuses a dirty catalog, does not execute consumer-repo code, and exposes
no Forgejo mutation entrypoint. It is Keychain-only (URL-scoped reset plus
`osxkeychain`), runs with a fixed system `PATH`, and fails if a read-only
workload changes the target Git state.

## Local and cloud JDK 21

`java-build-local` requires an explicit host `JAVA_HOME`; `java-build-cloud`
uses the separate `JAVA_VERSION=21` and `CLOUD_JDK_DISTRIBUTION=temurin`
selectors and contains no host path. The `local-jdk-verify` workload proves
that both `java` and `javac` match the requested feature release, then compiles
and executes a temporary probe. Android Studio's bundled JBR is a valid local
candidate when that probe passes. See [`docs/jdk-runtime.md`](docs/jdk-runtime.md)
for the exact boundary and license caveat.

## Where values belong

| Execution plane | Correct value store |
|---|---|
| Developer machine | Untracked `.env`, OS keychain, or provider CLI keyring |
| GitHub Actions | Repository or Environment secrets; prefer OIDC over long-lived cloud keys |
| Codex cloud | Environment secrets configured in the Codex cloud environment |
| Dedicated self-hosted runner | Runner service environment or host secret manager, restricted to trusted private workflows |
| Secure MCP Tunnel | OpenAI runtime key and tunnel configuration on the machine that actually runs the typed tools |

A GitHub or ChatGPT connector supplies authorization and tools, not compute. An MCP configuration in a repository is inert until a reachable MCP server and an execution host exist. Do not add a generic shell-over-MCP tool.

The complete decision matrix for GitHub app context, Codex cloud containers,
local execution, self-hosted runners, and Secure MCP Tunnel is in
[`docs/runtime-topology.md`](docs/runtime-topology.md).

## Public repository consumption

This repository is private during bootstrap. A public workflow cannot safely import it without an additional credential, and a personal access token would expand the attack surface. Before public projects consume it directly:

1. complete a public-release security review;
2. make the repository public or publish immutable release artifacts;
3. pin consumers to a release tag or commit SHA;
4. keep actual values in the consuming execution plane.

Do not copy a global `.env.example` into every project. Select the smallest profile, or add a project-specific profile that composes existing modules.

## Add a provider or runtime

1. Add new variable metadata once to `catalog/variables.json`.
2. Add one `modules/<id>.json` referencing those names.
3. Add or update a workload profile under `profiles/`.
4. Run `bash tests/run-all.sh`.
5. If an example is useful, generate it from the CLI and add a comparison to `tests/test_examples.sh`.

The JSON Schemas under [`contracts/`](contracts/README.md) document file shape. `./runtime-env validate` additionally checks cross-file references, filename identity, duplicate names, conflicting defaults, and the rule that a secret can never have a committed default.

Local credential isolation, session-backed carriers, TestFlight, logged-in
browser workloads, agy Gemini 3.6 Flash High, and proof/control receipts are
specified in [`docs/local-credential-broker.md`](docs/local-credential-broker.md).
The canonical dotenv is a host-only staging surface; consumer repositories
receive only the secret-free binding generated by `sync`.

## Four-repository integration

```text
skills-shared procedural requirements
→ runtime-env secret-free closure
→ bettor-arena composition/proof/stateless MCP/bootstrap
→ agent-shield-monorepo product/provider canaries
```

See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). A declaration in an upstream plane cannot proxy downstream live evidence.

## Evidence boundary

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

The attached architecture document is a source proposal. Its E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, cost, license, performance, and recovery statements require independent verification and subject-bound canaries.

## Development

```bash
bash tests/run-all.sh
git diff --check
```

Python 3.11+ and standard Unix tools are sufficient; runtime validation has no third-party package dependency.
