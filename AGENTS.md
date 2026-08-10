# AGENTS.md — runtime-env

This repository is a secret-free contract catalog. These rules apply to the entire tree.

## Invariants

- A variable name and its security metadata are declared exactly once in `catalog/variables.json`.
- Modules reference variables; profiles compose modules. Do not copy variable metadata into profiles.
- Never commit credentials, tokens, private keys, encoded credential blobs, or realistic secret fixtures.
- Secret variables never have defaults. Non-secret defaults must be safe on every host selecting the module.
- Local-first and cloud opt-in paths remain separate profiles. Absence of an optional cloud credential is not a failed local capability.
- `check` may report names and presence states, never values.
- A connector or MCP declaration is not an execution plane. Documentation must name the host that provides compute.

## Change procedure

1. Add a failing public-seam test under `tests/test_*.sh`.
2. Make the smallest catalog or CLI change that passes it.
3. Run `bash tests/run-all.sh` and `git diff --check`.
4. Review the staged diff before committing; commit messages explain why.

Do not bypass hooks, disable tests, or hand-edit generated files under `examples/` without updating their generating contract.
