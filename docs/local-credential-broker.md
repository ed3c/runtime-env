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
| `openshell-provider` | The sandbox receives an opaque provider placeholder; the network proxy substitutes the value | API-key HTTP clients whose TLS request is inspected and whose binary/host/path policy is bounded |
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

Use `runtime-env policy show --id <policy>` to inspect a policy. Pass both
repeatable `--policy` options to `runtime-env sync`; consumer `sync --check` or
its staged pre-commit validator then detects either native policy drifting.

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
browser.

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
