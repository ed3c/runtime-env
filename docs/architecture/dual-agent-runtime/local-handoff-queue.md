# Dual-Agent runtime Local Handoff Execution Queue

This queue starts only after the current-main documentation convergence is admitted. It is a trusted/local execution queue, not a GitHub Actions fixture plan.

## Queue law

- Re-read current `main`, open PRs/issues, host/runtime inventory, credentials, and target policy before starting.
- Use one isolated worktree and one writer per branch/path lease.
- Bind exact repository commit/tree, runtime/profile/workload/policy/config and rollback subject.
- Preserve failed, duplicate, timeout, cancelled, stale, revoked, cleanup-failed, and skipped attempts.
- Do not publish raw credentials, certificates/private keys, cookies, session bytes, browser profiles, personal paths, or private reasoning.
- Stop for Human/trusted authority whenever terms, billing, credentials, destructive cleanup, merge, release, or rollback are involved.

## LH-R01 — Rebind merged runtime subject

Owner: local Tech Lead.

```text
fetch current main
→ verify clean isolated worktree
→ run full repository test suite
→ inventory exact contracts/modules/profiles/workloads/scripts
→ record main commit/tree and rollback
```

Required output: exact runtime subject and full local test receipt. Repository CI from historical PR heads is not a substitute.

## LH-R02 — Physical NATS/JetStream topology admission

Owner: issue #73 plus trusted runtime/operator.

Required inputs:

```text
NATS server/version/binary or image digest
JetStream domain/stream/consumer config digests
TLS/mTLS identity and opaque credential handles
DNS/IP/port allowlist
retention, ACK wait, max delivery and redelivery bounds
safe tenant/job target
cleanup plan
```

Stop if there is no authorized server/runtime, network policy, TLS identity, or cleanup authority.

## LH-R03 — Offline enqueue and first restart

```text
local transport disconnected
→ submit exact job
→ SQLite outbox commit
→ close process
→ reopen process
→ rebuild one pending logical packet
```

Controls:

- ACK before durable commit;
- same identity with different bytes;
- LOCAL_ONLY packet with cloud/egress;
- raw secret/session/host path;
- packet loss or duplicate logical packet after restart.

## LH-R04 — Reconnect, duplicate/redelivery, and durable consumer

```text
connect leaf/client to admitted server
→ publish pending packet
→ intentionally redeliver duplicate
→ consume under exact tenant subject
→ ACK only after admitted durable observation/result
```

Required receipts include server/stream/consumer identities, delivery sequence, duplicate disposition, ACK timing, redelivery count and transport-only evidence ceiling.

Transport ACK must never become task, effect, user, Human, or release PASS.

## LH-R05 — Second restart and inbox reconciliation

```text
receive result bound to job/tenant/policy/runtime/artifact digests
→ durable inbox commit
→ close process
→ reopen process
→ rebuild exactly one reconciled result
```

Plant stale policy/runtime/result and cross-tenant/job mismatches. Record DB/WAL/SHM/temp/socket/process cleanup and retained-state inventory.

## LH-I01 — Distinct local/cloud workload enrollment

Owner: issue #83 plus trusted identity/operator plane.

Required inputs:

```text
local workload subject and enrollment evidence
cloud workload subject and enrollment/attestation evidence
distinct audiences
capability grants
policy digest/epoch
opaque secret handles and broker/KMS/Keychain authority
credential lifetime and rotation path
revocation path
```

A package, adapter, identity reference, or transport mTLS session is not enrollment/authorization evidence.

## LH-I02 — Policy drift, revocation, expiry, rotation

```text
queue job under policy epoch N
→ change policy to N+1 or revoke identity
→ reconnect
→ deterministic revalidation
→ POLICY_STALE / REVOKED_IDENTITY / EXPIRED_IDENTITY_LEASE
→ authorized reissue/rotation
→ re-admit only under exact new subjects
```

Keep all terminal states distinct. Do not downgrade capability or audience checks during fallback.

## LH-RI01 — Runtime convergence packet

After transport and identity live lanes complete, produce:

```text
exact main/head/tree and rollback
local host/runtime identity
server/stream/consumer identities
complete packet/delivery/restart history
local and cloud identity/enrollment evidence
policy/revocation/rotation history
secret-handle metadata without values
result/inbox/reconciliation receipts
cleanup/residue inventory
all failures/blocks/skips
remaining NOT_EXERCISED lanes
Human/operator decisions
```

Update #73, #83, parents #57/#58/#59, the cross-repository integration index, and `bettor-arena#186` prerequisites. Close #73/#83 only when their physical acceptance criteria are satisfied by exact receipts.

## Completion packet

Every handoff response must state:

```text
subject commit/tree
branch/worktree/writer lease
commands and runtime/provider versions
inputs and policy/identity/config digests
positive and disagreement-control results
complete attempts and state transitions
artifacts/receipt digests
cleanup/residue
known limitations
NOT_EXERCISED / HUMAN_REQUIRED / NOT_PERFORMED states
rollback
next owner and transition
```
