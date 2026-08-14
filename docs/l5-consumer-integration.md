# Agent runbook: connect a consumer repository to runtime-env L5

This is the concrete execution contract for Agents integrating a repository.
Read `docs/local-integration.md` first for security boundaries and maturity
definitions. This runbook defines the repeatable mechanics; it is not evidence
that a particular consumer has passed.

For the current host rollout, read
[`l5-rollout-2026-08-11.md`](l5-rollout-2026-08-11.md) before running an
external entrypoint. It records completed transmissions, exhausted retry
budgets, revision changes, and the explicit prohibition on iOS build/upload.

## Non-negotiable model

- runtime-env owns variable names, security metadata, profiles, workload
  commands, and carrier policies.
- The consumer owns target-relative adapter scripts, public-seam tests, one
  requirements document, and its pre-commit hook.
- The host owns one canonical `~/runtime-env/.env`, provider sessions,
  credential files, browser profiles, and private receipt roots.
- A consumer repository must not create its own `.env`. Generated
  `.runtime-env/examples/*.env.example` files contain names and safe defaults
  only.
- Host values enter the canonical dotenv through `local-env set-path` for
  declared non-secret paths or `local-env set --stdin` for other declared
  values. Credential literals must never appear in argv, logs, receipts, or
  Agent prompts.
- L5 is per `(consumer, binding, workload, consumer commit, runtime commit)`.
  One passing repository never promotes another repository or workload.

## Current consumer map

| Consumer | Binding | Workload | Consumer verifier |
|---|---|---|---|
| `~/bettor-arena` | `bettor-arena-local` | `bettor-arena-proof` | `scripts/gates/check_runtime_env_binding.py` delegates to the installed `runtime-env verify-consumer` seam |
| `~/skill-bettor` | `skill-bettor-agy-replay` | `agy-gemini36-flash-high-replay` | `scripts/check_runtime_env_consumer.sh` |
| `~/skill-bettor` | `skill-bettor-dr-research` | `dr-research-loop` | `scripts/check_runtime_env_consumer.sh` |
| `~/ix-agy` | `ix-agy-repo-wiki` | `repo-wiki-converge` | `scripts/check_runtime_env_consumer.sh` |
| `~/ix-agy` | `ix-agy-ios-verify` | `ios-testflight-verify` | `scripts/check_runtime_env_consumer.sh` |
| `~/ix-agy` | `ix-agy-ios-beta` | `ios-testflight-beta` | `scripts/check_runtime_env_consumer.sh` |
| `~/stealth-browser` | `stealth-browser-local` | `stealth-browser-mcp` | `scripts/check-runtime-env-consumer.sh` |
| `~/ts-skill-bettor` | `ts-skill-bettor-gemini-research` | `gemini-conversation-research` | `scripts/check-runtime-env-consumer.sh` |

Runtime-owned `local-jdk-verify` and `forgejo-delivery-loop` stop at L4 because
they do not depend on consumer application code.

## Consumer files

Each binding requires these tracked files:

1. `.runtime-env/requirements/<binding>.json` — desired state only.
2. Generated `.runtime-env/bindings/`, `.runtime-env/workloads/`,
   `.runtime-env/examples/`, and selected `.runtime-env/policies/` files.
3. Target-relative scripts referenced by the projected workload.
4. Public tests named by `public_test_entrypoints`.
5. A tracked executable verifier containing the exact binding id and invoking
   `runtime-env verify-consumer`.
6. A tracked executable pre-commit hook that invokes that verifier with
   `--staged`; `core.hooksPath` must be a repo-relative path such as
   `.githooks`.

Generated projections must not be edited by hand. Change the catalog,
requirements, or consumer adapter, then synchronize again.

## Ordered integration procedure

Work from a clean runtime-env revision and an isolated standard Git worktree for
the consumer. Do not switch branches in a shared main working tree.

```bash
cd ~/runtime-env
./runtime-env validate
bash tests/run-all.sh

./runtime-env sync \
  --requirements /absolute/consumer/.runtime-env/requirements/<binding>.json \
  --target-root /absolute/consumer

./runtime-env sync \
  --requirements /absolute/consumer/.runtime-env/requirements/<binding>.json \
  --target-root /absolute/consumer \
  --apply

./runtime-env sync \
  --requirements /absolute/consumer/.runtime-env/requirements/<binding>.json \
  --target-root /absolute/consumer \
  --check
```

Review and commit the consumer adapter, tests, requirements, hook, and generated
projection together. Then install the exact committed runtime revision:

```bash
cd ~/runtime-env
bash scripts/install-consumer-cli.sh
```

Enable and verify the consumer gate without using a sibling checkout:

```bash
git -C /absolute/consumer config core.hooksPath .githooks
runtime-env verify-consumer \
  --target-root /absolute/consumer \
  --binding <binding>
runtime-env verify-consumer \
  --target-root /absolute/consumer \
  --binding <binding> \
  --staged
```

Only after the consumer and runtime-env are both clean and the host prerequisites
exist, run the consolidated acceptance:

```bash
cd ~/runtime-env
./runtime-env accept-consumer \
  --target-root /absolute/consumer \
  --binding <binding> \
  --hook-verifier scripts/<consumer-verifier>.sh \
  --env-file ~/runtime-env/.env \
  --receipt /absolute/private/0700/receipts/<binding>.json \
  --json
```

By default, `accept-consumer` executes every acceptance entrypoint. For an
external transmission, release operation, or another entrypoint whose authority
is intentionally single-use, execute it once with `workload run`, then bind that
exact receipt into the consolidated run instead of transmitting again:

```bash
./runtime-env accept-consumer \
  --target-root /absolute/consumer \
  --binding <binding> \
  --hook-verifier scripts/<consumer-verifier>.sh \
  --execution-receipt <entrypoint>=/absolute/private/receipt.json \
  --receipt /absolute/private/0700/receipts/<binding>.json \
  --json
```

`--execution-receipt` is repeatable. A reused receipt must be a user-owned
`0600` regular file and must bind the same runtime commit/tree, workload,
entrypoint command, broker adapter, evidence contract, target root and clean
target HEAD. A stale, failed, renamed, edited, cross-target, or policy-violating
receipt whose contract fields no longer match is rejected; acceptance never
silently falls back to rerunning that entrypoint. The consolidated receipt also
records the exact SHA-256 of the reused receipt bytes it accepted.

The receipt is L5 only when every acceptance entrypoint has either passed in the
current run or supplied one valid exact-revision receipt, the public tests are
part of that set, the worktree and staged projection both verify, the configured
hook is tracked and executable, the runtime source matches the pin, and the
consumer HEAD/tree/status are unchanged. Child stdout, stderr, dotenv values,
cookies, and credential bytes are never stored in the receipt.

The mutation class controls only ignored and untracked workspace evidence.
`mutation=read-only` requires its fingerprint to remain unchanged;
`mutation=workspace` permits that fingerprint to change and records both the
change and the permission in the receipt. Neither class permits a changed HEAD,
tree, staged index, or non-ignored worktree path. Use a broker-owned run root
instead when workspace output is not part of the consumer's declared contract.

## External blockers are not integration passes

- iOS requires a real admitted iOS target, App Store Connect identifiers, and a
  broker-owned private key. `ios-testflight-beta` additionally requires separate
  human authority because upload is an external release mutation.
- Gemini requires exactly one already-open logged-in conversation tab on the
  loopback CDP endpoint and a broker-owned `GEMINI_RESEARCH_RUN_ROOT` directory
  with mode `0700`.
- repo-wiki requires a broker-owned `REPO_WIKI_RUN_ROOT` directory with mode
  `0700`, an explicit `ANTIGRAVITY_KB_PYTHON` interpreter, and a working
  Antigravity session.
- DR verification requires its real citation endpoints to be reachable. An
  `OFFLINE=1` verification is diagnostic evidence, not L4/L5 evidence.

For a missing prerequisite, record `BLOCKED`, the safe observation command, and
the next human action. Never substitute a fixture, skip an entrypoint, weaken a
permission check, or reuse another consumer's receipt.
