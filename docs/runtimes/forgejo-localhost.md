# Forgejo localhost runtime placement

This contract is for the local instance at `http://localhost:3000`. It does not
authorize an external Forgejo server and it does not make localhost reachable
from GitHub-hosted or Codex-cloud runners.

## Optional injection contracts

| Profile | Variables | Intended consumer |
|---|---|---|
| `forgejo-delivery-local-password` | `FORGEJO_URL`, `FORGEJO_USERNAME`, `FORGEJO_PASSWORD` | Bootstrap only, when neither the existing Chrome session nor Git credential helper is usable |
| `forgejo-delivery-local-api` | `FORGEJO_URL`, optional `FORGEJO_USERNAME`, `FORGEJO_TOKEN` | Opt-in typed API client; the current delivery loop does not consume it |

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

This machine currently has a plaintext `~/.git-credentials` entry for
`localhost:3000`. That is an observed legacy fact, not a value this repository
creates. Migration means configuring `credential.helper=osxkeychain`, approving
the credential into the helper, verifying a credential lookup in memory, and
only then removing the plaintext entry. Removal is a separate destructive
operation and must not be inferred from adopting this contract.

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
