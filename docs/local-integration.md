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
