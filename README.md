# runtime-env

> **Secret-free Runtime Contract Plane** for modular Agent repositories.

`runtime-env` records names, requirement semantics, safe defaults, profiles, fixed workloads, carrier policies, and consumer projections—never credential values. Start with [`AGENTS.md`](AGENTS.md), [`CONTEXT.md`](CONTEXT.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and [`docs/INDEX.md`](docs/INDEX.md).

## Directory → state machine → data flow

| Directory | State-machine responsibility | Core flow |
|---|---|---|
| `catalog/` | variable vocabulary/security | name proposed → validated → declared once |
| `contracts/` | document shapes | instance → schema validation → accepted/rejected |
| `modules/` | provider/runtime requirements | variables selected → requirement closure |
| `profiles/` | workload composition | modules composed → defaults/conflicts resolved |
| `workloads/` | fixed execution | entrypoint selected → exact env → receipt |
| `policies/` | carrier isolation projection | policy selected → consumer-native projection |
| `src/runtime_env/` | CLI transition engine | validate/list/render/check/workload/sync |
| `examples/` | generated projection | producer output → byte comparison |
| `.github-delivery/` | delivery evidence | artifact → receipt → publication attestation |
| `tests/` | falsification | positive/hollow/mutation/public-seam controls |

Nearest READMEs explain each owner and route to machine authority. Full transitions: [`docs/architecture/STATE_MACHINES.md`](docs/architecture/STATE_MACHINES.md).

## Four-repository integration

```text
skills-shared procedural requirements
→ runtime-env secret-free closure
→ bettor-arena binding/composition/proof/MCP
→ agent-shield-monorepo reference-consumer canaries
```

See [`docs/integration/CROSS_REPO_INTEGRATION.md`](docs/integration/CROSS_REPO_INTEGRATION.md). Local dotenv/Keychain/browser state and sibling checkouts are not portable release identity.

## Public lifecycle

1. A variable is declared once in `catalog/variables.json`.
2. A module references variables and declares requirement semantics.
3. A profile composes modules.
4. A workload declares fixed entrypoints and exact environments.
5. A policy projects carrier settings.
6. `sync` produces a dry-run plan; only `--apply` writes consumer projections.
7. Consumer hooks verify staged local projections offline.
8. Live canaries and promotion remain environment/Human owned.

## Quick start

```bash
./runtime-env validate
./runtime-env list --kind profiles
./runtime-env list --profile skill-bettor-e2b
./runtime-env render --profile skill-bettor-e2b --format dotenv
./runtime-env check --profile skill-bettor-e2b --env-file .env
./runtime-env workload list
./runtime-env workload show --id bettor-arena-proof
./runtime-env local-env init
./runtime-env local-env doctor
```

Exit codes are public contract:

| Exit | Meaning |
|---|---|
| `0` | valid / required names present / fixed workload accepted |
| `2` | invalid catalog, profile, arguments, policy, or dotenv shape |
| `3` | required configuration absent; workload did not run |

`check` prints names/presence only. `workload run` accepts a checked-in fixed entrypoint, verifies any dotenv is a user-owned `0600` regular file, constructs a minimal child environment, and stores metadata-only receipts. It does not expose a trailing arbitrary command.

## Explicit consumer synchronization

```bash
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root /path/to/bettor-arena

# after reviewing the plan
./runtime-env sync \
  --profile bettor-arena-runtime-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --target-root /path/to/bettor-arena \
  --apply
```

Generated consumer paths:

| Path | Purpose |
|---|---|
| `.runtime-env/bindings/<binding>.json` | portable closure and immutable source identity |
| `.runtime-env/examples/<binding>.env.example` | secret-free dotenv projection |
| `.runtime-env/workloads/<binding>.json` | fixed entrypoints and receipt/control projection |
| `.runtime-env/policies/<policy>.json` | carrier-native isolation projection |

Pre-commit verifies these staged consumer bytes only; it never invokes `sync`, uses network, or reads a sibling checkout.

## Value placement

| Execution plane | Correct store |
|---|---|
| Developer host | untracked private dotenv, OS Keychain, provider CLI keyring |
| GitHub Actions | repository/environment secrets; prefer OIDC |
| Codex cloud | environment secrets configured in that environment |
| Self-hosted runner | host secret manager/service environment |
| Secure MCP/provider broker | broker-owned secret/session store |

The catalog names the requirement; it never stores the value.

## Local and cloud are separate profiles

Optional E2B, browser, GitHub, Forgejo, JDK, mobile, and model/provider routes are selected by explicit modules/profiles/workloads. Package or profile presence does not mean the provider ran. Read [`docs/runtime-topology.md`](docs/runtime-topology.md), [`docs/local-integration.md`](docs/local-integration.md), and [`docs/local-credential-broker.md`](docs/local-credential-broker.md).

## Evidence states

```text
PASS
FAIL
ABSENT
NOT_IMPLEMENTED
NOT_EXERCISED
SKIPPED_BY_POLICY
```

A declaration, example, or generated binding is not a live canary. Source proposals—including E2B/Firecracker, OpenShell/tmux, Mutagen, mobile, wallet, security, cost, and license claims from the attached architecture document—require exact independent verification and execution.

## Development

```bash
bash tests/run-all.sh
git diff --check
```

Update the catalog/module/profile/workload/policy owner and its tests; do not hand-edit generated examples or consumer projections.
