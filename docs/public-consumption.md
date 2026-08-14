# Consuming a public runtime-env

This document is for a repository outside this one that wants to consume the catalog
once `runtime-env` is public. It covers how to obtain the source without a credential
and how to pin it.

## No credential is required

A public repository is clonable over anonymous HTTPS. A consumer needs no personal
access token, no deploy key, and no GitHub App installation to read this catalog.

If a consuming workflow needs a token merely to *fetch* `runtime-env`, that is a defect
in the consuming workflow, not a missing credential here. The only secrets in this
system are the provider values a host owns; this repository stores names, security
metadata, and safe defaults, never values.

## Pin by commit SHA, not by branch

A consumer that tracks `main` inherits catalog changes at whatever moment it happens to
fetch. Module closures, required/optional markings, and safe defaults can all move, so
an unpinned consumer cannot reproduce a past resolution or attribute a change.

Pin the full 40-character commit SHA:

```bash
git clone --filter=blob:none https://github.com/ed3c/runtime-env.git
git -C runtime-env checkout 1afc2e64e298fa1beab3a4b2819f61c34c88460b
```

As a submodule, which records the SHA in the consuming repository's own tree:

```bash
git submodule add https://github.com/ed3c/runtime-env.git vendor/runtime-env
git -C vendor/runtime-env checkout 1afc2e64e298fa1beab3a4b2819f61c34c88460b
git add vendor/runtime-env
```

## Release tags are an entry point, not a pin

Release tags such as `v0.1.0` exist so a human can find a coherent starting revision.
They are not a pin: a Git tag is a mutable ref, so the same tag name can be moved to a
different commit, while a commit SHA is content-addressed and cannot.

Resolve the tag once, then record what it resolved to:

```bash
git ls-remote --tags https://github.com/ed3c/runtime-env.git 'v0.1.0^{}'
```

Record the resulting SHA. Do not record the tag name as the pin.

## The resolved binding carries the pin for you

`runtime-env sync --requirements <file> --target-root <consumer> --apply` writes a
`consumer-binding/v2` document into the consuming repository. Its `source` object is
the pin, and [`contracts/consumer-binding.schema.json`](../contracts/consumer-binding.schema.json)
enforces the shape rather than leaving it to convention:

| Field | Constraint | Why |
|---|---|---|
| `source.repository` | must match `^https://` | an anonymous, public-clonable URL, so the pin stays resolvable without a credential |
| `source.commit` | must match `^[0-9a-f]{40}$` | full SHA only; an abbreviated SHA is ambiguous and is rejected |
| `source.tree` | must match `^[0-9a-f]{40}$` | pins the content, so a rewritten commit with the same message does not silently pass |

Because the schema requires all three, a binding that omits the pin, uses a short SHA,
or points at an `ssh://` or `git@` URL fails validation instead of being accepted and
drifting later.

Verify a consumer's committed projection against its binding without network access:

```bash
runtime-env verify-consumer --target-root <consumer> --binding <binding-id>
```

## Upgrading a pin

Upgrading is an explicit, reviewable act, not a fetch:

1. Check out the newer `runtime-env` commit.
2. Re-run `sync` with the *same* `requirements.json` against the consumer.
3. Review the resulting binding diff. A changed module closure, a variable moving
   between required and optional, or a changed safe default all show up here.
4. Commit the new binding in the consuming repository.

Rolling back is the same procedure against the older commit. Never hand-edit a resolved
binding: the binding is a projection of a pinned source, and editing it makes the pin a
claim rather than a fact.
