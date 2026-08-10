# runtime-env

`runtime-env` is a secret-free, modular catalog of environment variable contracts for agent repositories. It records **names, requirements, safe defaults, and account links**—never credential values.

The repository separates three concepts that are often mixed together:

1. A **variable** is declared once in `catalog/variables.json`.
2. A **module** describes one provider or runtime and marks variables required or optional.
3. A **profile** composes modules for one executable workload.

This prevents an optional cloud backend from making a local workflow demand unrelated API keys.

## Quick start

```bash
./runtime-env validate
./runtime-env list --kind profiles
./runtime-env list --profile skill-bettor-e2b
./runtime-env render --profile skill-bettor-e2b --format dotenv
./runtime-env render --profile agent-github-action-openai --format github-actions
./runtime-env check --profile skill-bettor-e2b --env-file .env
```

Exit codes are part of the public contract:

| Exit | Meaning |
|---|---|
| `0` | Contract is valid or all required names are present |
| `2` | Catalog, profile, arguments, or dotenv input are invalid |
| `3` | Required configuration is absent; the workload did not run |

`check` prints variable names and presence states only. It never prints values.

## Skill-bettor profiles

| Profile | Requirement |
|---|---|
| `skill-bettor-local` | Ollama defaults; zero cloud keys |
| `skill-bettor-e2b` | `E2B_API_KEY` for real E2B acceptance |
| `skill-bettor-gemini` | `GEMINI_API_KEY` for Gemini-driven local Stagehand |
| `skill-bettor-sandbox-browser-cloud` | E2B, Gemini, and Browserbase cloud paths |

The split follows the observed `skill-bettor` behavior: local Ollama is the default, while E2B and Gemini are explicit cloud opt-ins. Browserbase names are cataloged because the upstream environment contract names them, but the currently verified Stagehand path uses local Chromium.

Generated examples live in [`examples/`](examples/). CI proves they equal current CLI output; edit the catalog, module, or profile instead of editing generated examples directly.

## Where values belong

| Execution plane | Correct value store |
|---|---|
| Developer machine | Untracked `.env`, OS keychain, or provider CLI keyring |
| GitHub Actions | Repository or Environment secrets; prefer OIDC over long-lived cloud keys |
| Codex cloud | Environment secrets configured in the Codex cloud environment |
| Dedicated self-hosted runner | Runner service environment or host secret manager, restricted to trusted private workflows |
| Secure MCP Tunnel | OpenAI runtime key and tunnel configuration on the machine that actually runs the typed tools |

A GitHub or ChatGPT connector supplies authorization and tools, not compute. An MCP configuration in a repository is inert until a reachable MCP server and an execution host exist. Do not add a generic shell-over-MCP tool.

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

The JSON Schemas under [`contracts/`](contracts/) document file shape. `./runtime-env validate` additionally checks cross-file references, filename identity, duplicate names, conflicting defaults, and the rule that a secret can never have a committed default.

## Development

```bash
bash tests/run-all.sh
```

Python 3.11+ and standard Unix tools are sufficient; runtime validation has no third-party package dependency.
