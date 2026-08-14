# Forgejo localhost runtime placement

This contract is for the local instance at `http://localhost:3000`. It does not
authorize an external Forgejo server and it does not make localhost reachable
from GitHub-hosted or Codex-cloud runners.

## Optional injection contracts

| Profile | Variables | Intended consumer |
|---|---|---|
| `forgejo-delivery-local-password` | `FORGEJO_URL`, `FORGEJO_USERNAME`, `FORGEJO_PASSWORD` | Bootstrap only, when neither the existing Chrome session nor Git credential helper is usable |
| `forgejo-delivery-local-api` | `FORGEJO_URL`, optional `FORGEJO_USERNAME`, `FORGEJO_TOKEN` | Opt-in typed API client; the current delivery loop does not consume it |
| `forgejo-delivery-keychain-local` | none | Normal post-migration canary: fixed runtime-env-owned code inherits `HOME`, and Git resolves the URL-scoped Keychain helper without dotenv injection |

`FORGEJO_URL` defaults to `http://localhost:3000`. Account names and secrets
have no committed defaults. These profiles are not unconditional requirements
for `forgejo-delivery-loop`: an existing Chrome session or credential-helper
record is already a valid runtime input. A password and a token are alternatives;
do not require or store both merely because both names exist in the catalog.

## Every placement path

| Purpose | Exact path or surface | Secret handling |
|---|---|---|
| Contract source | `catalog/variables.json`, `modules/forgejo-local-*.json`, `profiles/forgejo-delivery-local-*.json` in this repository | Names and metadata only; no values |
| Generated template | `examples/forgejo-delivery-local-password.dotenv.example` or `examples/forgejo-delivery-local-api.dotenv.example` | Blank secret placeholders only |
| Untracked dotenv fallback | `~/.config/runtime-env/secrets/forgejo-local.env` | Mode `0600`; never copy into a repository |
| Preferred Git HTTP/browser credential source on macOS | `git credential fill`, backed by `credential.helper=osxkeychain` | Encrypted backing store is `~/Library/Keychains/login.keychain-db`; do not read or edit that database directly |
| One-time migration broker | `./runtime-env local-env migrate-forgejo-keychain` from `~/runtime-env` | Reads the private dotenv in-process, sends values to Git helpers over stdin, and emits status only |
| Existing legacy credential store on this machine | `~/.git-credentials` | Plaintext historical storage; do not print, copy, commit, or treat it as the recommended destination |
| Per-repository Forgejo commit identity | `<forgejo-repo>/.git/config` via repo-local `git config user.name` and `user.email` | Identity only, never password or token |
| Existing Chrome session | Logical surface: the user's current Chrome profile, controlled through the host's Chrome capability | Reuse the session; the profile's filesystem internals are intentionally not a credential API and cookies must never be exported |
| Token creation UI | `http://localhost:3000/user/settings/applications` in the existing browser session | Create once; the token value goes only to the chosen host secret store |

The fallback file can be checked without exposing values:

```bash
./runtime-env check \
  --profile forgejo-delivery-local-password \
  --env-file ~/.config/runtime-env/secrets/forgejo-local.env
```

The `forgejo-delivery-loop` runtime does **not** automatically source that
dotenv file. Its canonical credential seam is `git credential fill`: the
operator captures the result in memory and, only when the existing Chrome
session is logged out, fills the login form without echoing or persisting the
secret. Merely setting `FORGEJO_PASSWORD` does not bridge it into Git or Chrome.

For API mode, create a least-privilege token at
`http://localhost:3000/user/settings/applications` in the existing browser
session. On the current Forgejo 9.0.3 instance, scope to only the API route
families the typed client actually calls—for issue/PR delivery this normally
means `write:issue` and `write:repository`, verified against the exact endpoint
set before mutation. Store `FORGEJO_TOKEN` in
the same host secret store or fallback file, then inject it only into the local
API process. A GitHub connector, repository MCP declaration, or cloud runtime
cannot consume localhost credentials unless an explicitly reachable and typed
local execution bridge exists.

These names target a local process or GitHub-hosted secret mapping, **not custom
Forgejo Actions variables**. Forgejo reserves the `FORGEJO_`, `GITHUB_`, and
`GITEA_` prefixes in Actions; a Forgejo Actions job receives its own ephemeral
`FORGEJO_TOKEN`. Do not replace that job token with this long-lived local token.

## Migration away from plaintext Git credentials

After placing `FORGEJO_USERNAME` and `FORGEJO_PASSWORD` in the canonical private
dotenv, run:

```bash
cd ~/runtime-env
./runtime-env local-env migrate-forgejo-keychain
```

The broker accepts only `http://localhost:3000` or
`http://127.0.0.1:3000`. It stores and verifies the credential through
`git credential-osxkeychain`, resets the URL-specific helper chain before
selecting `osxkeychain`, removes only the matching localhost record from
`~/.git-credentials`, verifies `git credential fill`, and then atomically
replaces `FORGEJO_PASSWORD` with an empty assignment. It preserves
`FORGEJO_USERNAME`; no credential value enters output or a receipt. If any
pre-clear verification fails, the dotenv password remains present for recovery.

This is the supported handoff to `forgejo-delivery-loop`: that skill consumes
`git credential fill` and must not parse the dotenv or implement a second
password store.

## Modular delivery-loop workload

After migration, any Git consumer can select the same bounded broker workload;
the executed verifier comes from the selected runtime-env catalog checkout, not
from the consumer repository:

```bash
cd ~/runtime-env
./runtime-env workload run \
  --id forgejo-delivery-loop \
  --entrypoint broker-selftest \
  --target-root /absolute/path/to/consumer \
  --receipt ~/.local/state/runtime-env/receipts/forgejo-delivery/selftest.json

./runtime-env workload run \
  --id forgejo-delivery-loop \
  --entrypoint credential-canary \
  --target-root /absolute/path/to/consumer \
  --receipt ~/.local/state/runtime-env/receipts/forgejo-delivery/status.json
```

`broker-selftest` is offline. `credential-canary` uses
`--credential-helper-only` to check loopback reachability, Git helper resolution,
and authenticated `/api/v1/user` access. Before `fill`, it requires the effective
URL-scoped helper chain to be exactly an empty reset followed by `osxkeychain`;
an empty, `store`, or shell helper fails instead of reading a dotenv fallback.
The workload declares `secret_delivery=none`, passes no
`FORGEJO_*` environment variables, replaces child `PATH` with
`/usr/bin:/bin:/usr/sbin:/sbin`, and returns only child stream hashes in its
mode-`0600` receipt. Git can still reach Keychain because the fixed runner's
safe host allowlist includes `HOME`; the secret remains inside the Git helper
and runtime-owned verifier. The
`@runtime-env/` command prefix is resolved only to a regular file within the
selected catalog root, preventing a consumer path from replacing the broker.
The credential entrypoint also refuses a dirty or unversioned catalog root;
its receipt records the runtime-env HEAD, tree, and dirty state.
The runner also compares target HEAD and porcelain state before and after every
`mutation=read-only` workload; any change makes the receipt and process fail.
Forgejo line status and every mutation remain owned by
`forgejo-delivery-loop`; this workload only proves its credential precondition.

## Official contract anchors

- [Forgejo binary installation](https://forgejo.org/docs/latest/admin/installation/binary/)
  documents the default local UI at `http://localhost:3000/`.
- [Forgejo 9.0 access-token scopes](https://forgejo.org/docs/v9.0/user/token-scope/)
  documents the route-family scopes available on the installed major version.
  Repository-specific token restriction is a newer capability and must not be
  assumed until a version preflight proves the local instance supports it.
- [Forgejo Actions basic concepts](https://forgejo.org/docs/latest/user/actions/basic-concepts/)
  documents reserved variable prefixes and the ephemeral automatic token.
- [Git credentials](https://git-scm.com/docs/gitcredentials.html) documents
  credential helpers, including `osxkeychain`, and distinguishes secure helpers
  from the plaintext `store` helper.
