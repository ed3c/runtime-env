# Bettor Tech Lead runtime rebind

Authority chain: `ed3c/bettor-arena#161` → `#146`, `ed3c/runtime-env#48/#45`, and `ed3c/skills-shared#231/#234/#256`.

The first physical Bettor Tech Lead scheduler canary must bind the consumer to `bettor-arena-tech-lead-local`. This profile is the existing `bettor-arena-runtime-local` closure plus exactly one `multi-worker-scheduler` module. It does not admit Git Town, start Forgejo, activate providers, or grant merge/promotion authority.

From a clean checkout of the exact admitted `runtime-env` revision, preview the consumer projection first:

```bash
./runtime-env sync \
  --profile bettor-arena-tech-lead-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /absolute/path/to/bettor-arena
```

Review the `WOULD-CREATE` / `WOULD-UPDATE` receipt. Only an explicit host maintenance action may apply it:

```bash
./runtime-env sync \
  --profile bettor-arena-tech-lead-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /absolute/path/to/bettor-arena \
  --apply
```

Then verify freshness against the same exact runtime-env checkout:

```bash
./runtime-env sync \
  --profile bettor-arena-tech-lead-local \
  --binding bettor-arena-local \
  --workload bettor-arena-proof \
  --policy claude-code-native-isolation \
  --policy codex-cli-native-isolation \
  --policy codex-openshell-chatgpt-placeholder \
  --target-root /absolute/path/to/bettor-arena \
  --check
```

Binding generation and scheduler execution are intentionally separate. After the binding is committed and Bettor's admission gate reports `READY_FOR_LOCAL_CANARY`, execute the fixed `repository-control-plane-scheduler` / `multi-worker-canary.py` routes from runtime-env. Do not pass a model-generated shell command.

Evidence ceilings remain separate: a fresh binding proves composition/freshness only; it does not prove live Workers, Git Town, Forgejo, GrepAI, SCIP/LSP, Tree-sitter, Serena, SQLite, convergence, merge, or promotion.
