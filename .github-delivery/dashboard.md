# runtime-contracts delivery dashboard

> Snapshot: `2026-08-17T06:30:31Z`。本頁是 GitHub event truth 的時間點快照，
> 不是 registry 的第二份真相，也不是個人生產力排名。

## Truth boundary

```text
┌───────────────┐    ┌──────────────┐    ┌────────────────────────┐
│ GitHub events │ ─→ │ metrics.json │ ─→ │ Markdown decision view │
└───────────────┘    └──────────────┘    └────────────────────────┘
         │
         ├─→ GitHub Project (status projection only)
         └─→ publication attestation ─→ human visibility gate
```

## Current decision

- Repository: `ed3c/runtime-env` (`PUBLIC`)
- Remote tree: `e663b6f88de5b4e1d3e8965b4fb5cf7311018912` (236 files, orphan root: `YES`)
- Public ready: `NO`
- Blockers: `export-tree-drift, open-delivery-slices`
- Project: [ix-agy 開源交付儀表板](https://github.com/users/ed3c/projects/3)

## Flow health

| Signal | Value |
|---|---:|
| accepted slices | 8 |
| WIP | 1 |
| blocked | 0 |
| throughput 7d / 28d | 8 / 8 |
| closed_without_merge | 0 |

## Project projection

| Status | Items |
|---|---:|
| Done | 19 |
| Todo | 5 |

`closed_without_merge` 是證據缺口，不計入 throughput。p50/p85 只在有 merge event 樣本時顯示。

## Slice evidence

| Issue | State | Started PR | Accepted PR | Lead | Blocked |
|---:|---|---:|---:|---:|---:|
| #2 | CLOSED | 3 | 3 | 5286 | 0 |
| #4 | OPEN | 33 | — | UNKNOWN | 0 |
| #19 | CLOSED | 20 | 20 | 157 | 0 |
| #21 | CLOSED | 22 | 22 | 74 | 0 |
| #29 | CLOSED | 30 | 30 | 76604 | 0 |
| #31 | CLOSED | 32 | 32 | 381 | 0 |
| #35 | CLOSED | 39 | 39 | 117264 | 0 |
| #36 | CLOSED | 40 | 40 | 6717 | 0 |
| #37 | OPEN | — | — | UNKNOWN | 0 |
| #38 | OPEN | — | — | UNKNOWN | 0 |
| #45 | OPEN | — | — | UNKNOWN | 0 |
| #48 | CLOSED | 49 | 49 | 111 | 0 |

## Human gate

只有 blockers 清空、publication attestation 與遠端 HEAD 對齊後，人類才可執行 PR merge 與 PRIVATE→PUBLIC。

## MVP extraction

| Step | Direct? | Undecided dependency | Permission | Measurable change | Size |
|---|---|---|---|---|---|
| Clear mechanical blockers | direct | none | repository scope | blockers count decreases | small |
| Human visibility decision | direct | owner review | owner only | visibility becomes PUBLIC | human gate |

Rejected now: custom daemon (extra operational surface); personal ranking (Goodhart risk); automatic merge/public toggle (violates human gate).
