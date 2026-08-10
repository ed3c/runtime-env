# Local credential broker boundary

## Security claim

There is no absolute secrecy when an unrestricted agent and a plaintext
dotenv run as the same macOS user. If the agent can open the file, inspect a
secret-bearing child process, choose arbitrary commands, or send arbitrary
network requests, it can disclose the credential. Redacting command output
does not repair that architecture.

The supported local design separates four planes:

```text
/Users/neon/runtime-env/.env (0600, host-only staging)
              |
              v
   provider or typed host broker
              |
              +-- fixed workload + admitted Git revision
              +-- bounded filesystem/network/process policy
              +-- private material visible only to trusted workload process
              |
              v
 metadata-only receipt / exit-domain / artifact hash
              |
              v
       agent sandbox (no .env, keyring, cookie state, or auth cache)
```

`runtime-env workload show --id <id>` exposes the checked-in policy. Every
workload declares a fixed profile, entrypoints, mutation class, delivery mode,
agent access, receipt, and independent control. `agent_secret_access` is always
`denied`.

For local `none` workloads, `runtime-env workload run` is the narrow execution
surface: it accepts a workload ID and one manifest-owned entrypoint, never an
arbitrary command. It validates the target Git root and private dotenv metadata,
passes only selected non-secret names into a minimal environment, suppresses
child streams, and emits only their byte counts and SHA-256 hashes in a private
receipt. If the selected profile resolves any secret, execution fails closed.
`broker-only` and `openshell-provider` describe separate adapters; this local
runner intentionally does not imitate them by exporting plaintext secrets.
The workload's `entrypoint_environment` is the second boundary: it narrows the
profile independently for every fixed command. Carrier configuration names are
therefore not ambient merely because they coexist in `/Users/neon/runtime-env/.env`.

## Delivery classes

| Class | Meaning | Current safe use |
|---|---|---|
| `none` | No credential is delivered | deterministic proof/control workloads on an admitted clean revision |
| `openshell-provider` | The sandbox receives an opaque provider placeholder; the network proxy substitutes the value | Supported HTTP clients that put the placeholder directly in an inspected request and whose binary/host/path policy is bounded |
| `broker-only` | Session cache, cookie state, private file, or subscription login stays in a host process outside the agent filesystem | TestFlight, logged-in browser work, agy, Claude Code, Codex CLI, and other session-backed carriers |

Never add a generic `run -- <arbitrary command>` credential path. Any command
that receives an ordinary environment variable can print it. OpenShell `--env`
is therefore not a protected delivery mechanism; use provider placeholders
where the client and protocol are supported.

## Admitted revision rule

A credential-bearing workload must run only from a clean Git worktree whose
HEAD and runner bytes match a previously admitted receipt. Checking only the
runner script is insufficient: Fastlane loads a project `Fastfile`, browser
adapters import sibling modules, and research engines consume validators and
prompts. Admission therefore binds the complete Git tree plus the workload
manifest.

This rule creates a deliberate stop: an agent may prepare and test a new tree,
but that same unadmitted tree cannot immediately spend host credentials. GitHub
auto-merge authorization does not erase the need for a security admission
receipt; repository write permission and credential-use permission are
distinct.

## Claude Code and Codex CLI native settings

The two CLIs keep separate configuration roots and native policy files:

| Carrier | Config root | Native file | Runtime-env policy |
|---|---|---|---|
| Claude Code | `CLAUDE_CONFIG_DIR` | `settings.json` | `claude-code-native-isolation` |
| Codex CLI | `CODEX_HOME` | `config.toml` | `codex-cli-native-isolation` |

Claude Code requires sandbox enablement, fail-closed startup, no unsandboxed
escape hatch, disabled bypass-permissions mode, and both sandbox read/write and
tool-level `Read(...)`/`Edit(...)` denies. Render its placeholders as absolute
host paths and install them at a host or managed settings layer; a repository
projection is evidence and input, not the enforcement point. Codex requires `workspace-write`, `on-request`,
and a shell environment that inherits nothing by default. Codex native
workspace-write is not a general arbitrary-path deny-read policy, so an
OpenShell or managed OS sandbox must additionally hide the runtime dotenv and
the other carriers' homes.

Each policy explicitly removes the other carrier's config/auth environment.
Do not launch Claude from an environment containing `CODEX_HOME` or Codex auth
variables, and do not launch Codex with `CLAUDE_CONFIG_DIR`, Anthropic keys, or
Claude OAuth material. The shared repository projection contains settings
requirements only; host-specific homes and their contents never synchronize.
The fixed workload runner enforces the same split at process creation through
`entrypoint_environment`; native policy controls and process-environment
controls are complementary, and neither policy file is rewritten by the other
carrier.

On macOS, the existing Claude subscription login is Keychain-backed. Its fixed
status canary deliberately leaves `CLAUDE_CONFIG_DIR` unset because setting the
override—even to the textual default path—selects a separate Claude config
identity. The canary also fails if any Codex/OpenAI auth or config environment
is present. A separately logged-in Claude identity may use an explicit override
in a distinct admitted workload; it must not silently replace the default-login
canary.

Use `runtime-env policy show --id <policy>` to inspect a policy. Pass both
repeatable `--policy` options to `runtime-env sync`; consumer `sync --check` or
its staged pre-commit validator then detects either native policy drifting.

### OpenShell provider bootstrap is a third, separate plane

Carrier-native settings, credential transport, and sandbox policy are three
different controls. Creating an OpenShell provider must not write either
carrier's native settings file, and changing a native permission projection
must not recreate or widen a provider.

For a Codex ChatGPT login, OpenShell 0.0.59 exposes a typed `codex` profile but
does not discover `~/.codex/auth.json` through `--from-existing`. Run the
repository bootstrap only from a trusted host terminal:

```bash
python3 scripts/bootstrap-openshell-provider.py codex-chatgpt \
  --name codex-runtime-env \
  --receipt ~/.local/state/runtime-env/receipts/openshell/codex-runtime-env.json
```

The broker requires an owned, regular, non-symlink `0600` auth file. It passes
`CODEX_AUTH_ACCESS_TOKEN`, `CODEX_AUTH_REFRESH_TOKEN`,
`CODEX_AUTH_ACCOUNT_ID`, and optional `CODEX_AUTH_ID_TOKEN` to the OpenShell
client by environment-name lookup. Values never enter argv or receipts; child
stdout/stderr is suppressed. Its child environment is rebuilt from a small
host allowlist and therefore excludes `CLAUDE_CONFIG_DIR`, Anthropic keys, and
Claude OAuth state. The provider name, not `auth.json`, is the sandbox input.

Codex's ordinary ChatGPT login path cannot consume that placeholder through
`auth.json`: it parses the JWT before making a request. That is a limitation of
that credential-loading path, not a reason to put the real session in the
sandbox. Select the separately synchronized
`codex-openshell-chatgpt-placeholder` policy instead. Its custom Codex model
provider uses `CODEX_AUTH_ACCESS_TOKEN` as `env_key`, maps
`CODEX_AUTH_ACCOUNT_ID` to `ChatGPT-Account-ID`, targets
`https://chatgpt.com/backend-api/codex`, disables WebSocket transport, and sets
`requires_openai_auth=false`. Codex then places the opaque values directly in
the HTTPS request; the OpenShell proxy substitutes them after enforcing the
endpoint and executable policy. The sandbox must not receive `CODEX_AUTH_JSON`
or reconstruct `~/.codex/auth.json`.

This transport policy is intentionally separate from
`codex-cli-native-isolation`. The native policy controls the host CLI's
workspace, approvals, and inherited environment. The transport policy controls
only the disposable OpenShell sandbox's model-provider block. Synchronize both;
do not merge them into one ambient `CODEX_HOME`.

Claude subscription auth is deliberately not folded into that route. The
macOS Keychain-backed login is not equivalent to an Anthropic API key, while
OpenShell's built-in `claude-code` profile currently describes API-key auth.
For subscription use, a trusted operator runs `claude setup-token` and creates
or updates a dedicated generic `claude-code` provider; the sandbox must observe
only an `openshell:resolve:env:...` placeholder and prove a bounded real turn.
Do not copy Claude's Keychain/session files and do not place the setup token in
the shared dotenv.

This bootstrap is not an absolute same-UID secrecy boundary. A process that can
read `~/.codex/auth.json`, replace the broker, replace the `openshell` binary,
or inspect another same-user process can steal the session regardless of this
repository's redaction rules. Therefore an LLM shell with ordinary host read
access must not run the bootstrap. Absolute non-disclosure requires an OS
sandbox that denies the agent the carrier home plus a trusted host broker (or a
Keychain/secret-store service) outside that sandbox. Runtime-env supplies the
contract and content-free receipt; OpenShell/OS policy supplies enforcement.

## Workload-specific boundaries

### iOS TestFlight

`ios-testflight-verify` and `ios-testflight-beta` reuse the canonical
`ios-testflight-ship` scripts. The broker owns dotenv parsing, `.p8` access,
Keychain signing identity access, and the fixed `verify_asc`/`beta` lane. The
agent receives Fastlane exit state and a redacted receipt, never signing
material. The existing `boundary.sh` and `preflight.sh` directly inspect
`fastlane/.env` and `~/.appstoreconnect`; they may run inside the trusted broker,
not in an unrestricted agent shell.

### Gemini conversation research and stealth-browser

The browser owns its login cookies. Raw conversation text, DOM snapshots,
screenshots, OCR, prompts, and reports go directly to an admitted file sink.
The caller receives only the bounded receipt required by
`gemini-conversation-research/modules/browser-content-isolation.md`. The
dedicated `:9333` research profile and an interactive extension profile are
different carriers and must not be driven concurrently as if they were one
browser. The bettor binding includes a metadata-only `research-browser-health`
entrypoint. It accepts only loopback HTTP, reads `/json/version`, verifies the
debugger WebSocket is also loopback, and emits only a browser-version hash. It
does not enumerate tabs, inspect DOM, or transmit a prompt.

### Agy Gemini 3.6 Flash High

The exact runtime selector is `gemini-3.6-flash-high` with effort `high`.
`agy models` is the inventory receipt. A valid execution also requires a real
file-output canary because exit zero and stdout can be empty or merely summarize
an artifact. Agy produces independent findings; it is not the final judge or
Human admit authority.

### Bettor-arena proof workflow

The proof receipt and control receipt are independent outputs. A valid run
requires the positive path, ablation/control path, planted defect going red,
non-empty derived inventories, unchanged canonical digest on a repeated run,
and the declared `0/2/64` exit domain. Runtime-env points to this mechanism; it
does not duplicate the proof implementation.

## Cloud continuation

Codex cloud secrets are removed after setup, so they cannot directly back a
secret needed in the agent phase. A GitHub connector is a repository context
plane, not compute. Cloud continuation therefore uses either disposable
portable tests with no host credentials, or a narrow remote MCP/Secure MCP
Tunnel to a typed private-host broker. Secure MCP Tunnel is a reachability
bridge, not a sandbox. A generic remote shell or filesystem
tool would recreate the local disclosure problem over the network.

## Official anchors

- [OpenShell provider management](https://docs.nvidia.com/openshell/latest/sandboxes/manage-providers)
  defines opaque placeholders and proxy-side credential substitution.
- [OpenShell policy schema](https://docs.nvidia.com/openshell/latest/reference/policy-schema)
  defines filesystem, process, and network policy surfaces.
- [OpenShell security best practices](https://docs.nvidia.com/openshell/latest/security/best-practices)
  distinguishes ordinary visible environment variables from protected provider
  delivery.
- [Codex authentication](https://learn.chatgpt.com/docs/auth) documents the
  keyring/plaintext auth-store choices and the sensitivity of `auth.json`.
- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
  warns against exposing job-wide credentials to untrusted code.
- [Codex advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced)
  defines `shell_environment_policy` filtering and inheritance.
- [Codex model provider implementation](https://github.com/openai/codex/blob/main/codex-rs/model-provider-info/src/lib.rs)
  defines custom `env_key`, environment-backed HTTP headers, the ChatGPT Codex
  base URL, and the default-disabled WebSocket capability used by this adapter.
- [Anthropic self-hosted sandbox security](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes-security)
  assigns credential storage, network egress, and tool isolation to the
  self-hosted operator.
- [Claude Code permissions](https://code.claude.com/docs/en/permissions)
  defines deny/ask/allow precedence, permission modes, and settings precedence.
- [Claude Code sandboxing](https://code.claude.com/docs/en/sandboxing) defines
  fail-closed sandbox startup, filesystem/network restrictions, and the
  unsandboxed-command escape hatch.
- [Claude Code environment variables](https://code.claude.com/docs/en/env-vars)
  defines `CLAUDE_CONFIG_DIR` as the root for settings, credentials, sessions,
  and plugins.
- [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
  describes the private-network reachability bridge; it does not turn a broad
  remote shell into a credential-safe tool.
