# Dual-Agent runtime Local Handoff Execution Queue

This queue begins only after the deterministic runtime subtree is present on the selected `main` subject. It does not grant provider, credential, network, Human, or release authority.

## Queue law

```text
one exact subject
→ one authorized runtime/provider owner
→ one bounded physical objective
→ complete attempts and cleanup denominator
→ evidence packet
→ independent readback
→ typed transition
```

No item may infer PASS from package presence, schema validity, CI, provider health, an ACK, or the absence of an authorized runtime.

## RH-01 — Current-main deterministic readback

Owner: repository Tech Lead.

1. fetch current `main` and all merged PR records;
2. confirm contract, module, profile, workload, script and test paths are present;
3. run `bash tests/run-all.sh` in a clean local worktree;
4. capture base/head/tree, contract-set digest and rollback subject;
5. verify no Draft-only or stale generated projection is being treated as current truth.

Output: `RUNTIME_MAIN_READBACK_PASS | BLOCKED`.

## RH-02 — Physical NATS/JetStream canary (`#73`)

Owner: trusted local/cloud transport runtime.

Required:

```text
real NATS server and JetStream domain
exact server/client/config identities
TLS material through opaque handles
local outbox committed while disconnected
local process restart before delivery
reconnect and at-least-once redelivery
intentional duplicate delivery
bounded ACK/redelivery budget
result/inbox commit
second local restart and projection rebuild
cleanup / socket / stream / consumer / temp residue readback
```

Refuse:

```text
ACK before durable commit
cross-tenant subject
wildcard subject widening
duplicate accepted as a second logical effect
provider absence represented as PASS
fixture represented as physical reconnect
```

Output: complete transport receipt bundle, not task/user/release PASS.

## RH-03 — Live local/cloud identity canary (`#83`)

Owner: trusted identity, policy and secret runtime.

Required:

```text
distinct LOCAL and CLOUD identities
exact audience and tenant bindings
live enrollment / attestation evidence
bounded credential or SVID lifetime
opaque local/cloud secret handles
queued job under policy epoch N
policy drift or revocation before reconnect
reconnect-time refusal
safe rotation / reissue
re-admission under current policy
cleanup and credential/session residue inventory
```

Refuse:

```text
local identity reused as cloud
wrong audience
authenticated transport as task authorization
package presence as enrollment
stale/revoked/expired identity accepted
raw secret/token/certificate bytes in repository evidence
fixture represented as live provider decision
```

Output: identity/policy receipt bundle, not provider/task/user/release PASS.

## RH-04 — Consumer handoff

Owner: `bettor-arena` workflow/effect plane.

Inputs:

- RH-02 complete delivery/restart denominator;
- RH-03 current identity/policy/secret-handle evidence;
- exact runtime contract-set digest;
- job, tenant, idempotency and artifact subjects.

The consumer must preserve typed stale/refused/revoked/expired/unknown states and may not collapse them into generic success or failure.

## RH-05 — Independent verification

Owner: `truth-verify-loop#22`.

Re-fetch and verify:

```text
source and binding subjects
delivery attempts and acknowledgements
workflow/result lineage
inbox and restart reconstruction
artifact bytes/readback
cleanup inventory
Human/release state
```

Technical consistency may remain `UNVERIFIABLE` when semantic or live evidence is absent.

## Completion packet

```text
repository / base / head / tree / rollback
contract-set and policy digests
server / stream / consumer / client identities
local and cloud identity subjects
secret handles only; never secret values
job / packet / delivery / attempt / result graph
all retries / duplicates / failures / timeouts / cancellations
restart and reconstruction receipts
artifact and readback digests
cleanup / residue inventory
remaining NOT_EXERCISED lanes
Human decision, only when explicitly performed
```

## Queue state

```text
RH-01  READY
RH-02  HUMAN_TRUSTED_RUNTIME_REQUIRED / NOT_EXERCISED
RH-03  HUMAN_TRUSTED_RUNTIME_REQUIRED / NOT_EXERCISED
RH-04  BLOCKED_BY_RH-02_AND_RH-03
RH-05  BLOCKED_BY_REAL_BUNDLE
```
