# Local runtime integration contract

## Canonical local entrypoint

The intended checkout is `/Users/neon/runtime-env`. Agents should run catalog
and host verification from that directory; do not copy this repository's files
into each consuming project.

Before claiming that a workload or consumer repository is integrated, read
[`docs/integration-requirements.md`](integration-requirements.md). It defines
the maturity levels, live evidence, consumer acceptance, and blocker receipts
required for that claim.

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
./runtime-env local-env migrate-forgejo-keychain # after filling Forgejo username/password
```

Fill the resulting file outside an agent session. Do not paste its values into
chat. A synchronized consumer reads its secret-free binding while the local
broker resolves values from this one canonical file; the dotenv itself is not
copied to that consumer.

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
