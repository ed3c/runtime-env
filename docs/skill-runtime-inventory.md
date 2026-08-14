# Skill physical runtime inventory

The inventory is generated from the target checkout rather than copied into a
second hand-maintained list:

```bash
cd ~/runtime-env
./runtime-env inventory skills --repo-root ~/ix-agy \
  > /tmp/ix-agy-skill-inventory.json
```

The JSON records every top-level `SKILL.md` or `skill.md`, its resolved physical
source root, runtime code modules, test/assertion modules, repo-external modules
referenced through `kb-ingest/` or `indexing/`, and environment-name references.
It follows the shared-skill symlinks while excluding virtual environments,
dependency trees, caches, fixtures, and per-run data.

The 2026-08-10 inventory at ix-agy commit
`964d5a9758f3860e6fca894662ebae049d769dc0` contains:

| Item | Count |
|---|---:|
| Skills | 31 |
| Runtime code modules | 73 |
| Test/assertion modules | 64 |
| Referenced `kb-ingest/` or `indexing/` modules | 22 |

The same scanner reports 27 skills / 42 runtime modules / 32 assertion modules
for `~/bettor-arena`, and 25 / 42 / 32 for
`~/skill-bettor`. In both repositories the named
`gemini-conversation-research` and `dr-research-loop` entries resolve through
their symlinks to `~/.agents/skills-shared/skills/`; the consumer path
is a discovery surface, not a second implementation.

Two lowercase manifests are deliberately included:
`.agents/skills/problem-graph-indexer/skill.md` and
`.agents/skills/subproject-ixsecurity-e2e/skill.md`. A case-sensitive scan for
only `SKILL.md` is incomplete.

## Load-bearing local paths

| Capability | Physical path(s) |
|---|---|
| repo-wiki orchestration | `~/ix-agy/.agents/skills/repo-wiki-converge/` |
| repo-wiki author/verify/setup prompts | `~/ix-agy/kb-ingest/` |
| repo-wiki KG ingest | `~/ix-agy/indexing/ingest_repodoc_cli.py` plus the `indexing/` package |
| TestFlight boundary and ship | `~/ix-agy/.agents/skills/ios-testflight-ship/scripts/` |
| TestFlight negative/positive controls | `~/ix-agy/.agents/skills/ios-testflight-ship/tests/` |
| bettor proof receipts/controls | `~/bettor-arena/proof_workflow/` and `~/bettor-arena/loopctl/` |
| Gemini conversation research | `~/bettor-arena/.agents/skills/gemini-conversation-research/` plus bettor-arena repo-root browser adapters |
| DR proposal loop | `~/skill-bettor/.agents/skills/dr-research-loop/`, `~/skill-bettor/loop_wiki/engine.sh`, and `_template_dr/` |
| Agy 3.6 Flash High replay | `~/skill-bettor/loop_wiki/evolve-unknown-discovery-plan-truth/scripts/execute_agy_replay_requests.py` |
| stealth-browser MCP | `~/stealth-browser/src/index.ts`; persistent auth state under `~/stealth-browser/profiles/` |

The inventory proves that a path exists; it does not prove authentication,
network reachability, a real model turn, browser content isolation, or a device
operation. Each workload keeps those canaries and controls separate.
