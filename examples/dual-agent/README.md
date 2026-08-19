# Dual-Agent examples

These are deterministic **contract fixtures**, not runtime receipts.

- `P1`: public read-only cloud job.
- `P2`: `LOCAL_ONLY` local job with zero network egress.
- `P3`: reversible write with Human approval, effect identity and compensation.
- `P4`: duplicate delivery keeps one idempotency/effect identity across attempts.
- `P5`: unknown external effect remains a distinct terminal state.
- `P6`: `../../contracts/dual-agent/contract-set-manifest.json` binds the exact
  portable-method subject and schema digests.

No fixture can claim live provider execution, user outcome, merge or release.
