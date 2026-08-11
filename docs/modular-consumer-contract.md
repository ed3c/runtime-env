# runtime-env modular consumer contract

## Lifecycle shared with skills-shared

Canonical SSOT → module → profile/collection → consumer requirements → resolved binding → carrier adapter → receipt/control。

兩者的治理 lifecycle 相同，transport 不同：runtime-env 不把整個 checkout symlink 進 consumer，
只同步 secret-free binding、dotenv example、fixed workload 與 carrier policy。secret values 永遠留在
host-owned store/broker。

## Desired and resolved state

Consumer 提交 `.runtime-env/requirements.json`，明列 profile 與預期 module closure：

```json
{
  "schema": "runtime-env/consumer-requirements/v1",
  "binding": "bettor-arena-local",
  "profile": "bettor-arena-runtime-local",
  "required_modules": ["agent-actor-claude-code", "agent-actor-codex-cli"],
  "workload": "bettor-arena-proof",
  "policies": ["claude-code-native-isolation", "codex-cli-native-isolation"]
}
```

`runtime-env sync --requirements ... --target-root ... --apply` 解析後產
`consumer-binding/v2`。binding 固定 source commit/tree、requirements digest、module id/interface/digest、
variables 與 projection closure。profile 增減 module 但 requirements 未更新時 sync fail closed。

## Channels and rollback

- development：從乾淨的 runtime-env worktree 顯式 sync；允許 consumer review 新 binding diff。
- stable：consumer 已提交的 binding；CLI、CI 與 Agent 只讀這份 closure，不讀 sibling checkout。
- rollback：checkout 舊 clean runtime-env commit，使用同一 requirements sync；不得手改 resolved binding。

## Agent boundary

Agent 可以讀名稱、presence、scope、safe default 與 receipt，不得讀或同步 secret value。
離線 binding 綠只證 contract closure；host service、provider、Claude/Codex login 與真 model turn必須各有
live receipt，否則狀態是 `NOT_EXERCISED`。
