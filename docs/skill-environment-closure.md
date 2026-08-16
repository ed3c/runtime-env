# Skill environment closure

`runtime-env skills` is the host/runtime half of the canonical Skill integration contract. It does not select Skills or copy Skill bodies. It consumes exact identities emitted by `skills-shared` and maps abstract capability requirements only through an explicit repository binding.

```text
skills-shared resolution receipt
+ per-Skill runtime requirements
+ repo-skill-runtime-binding
+ exact consumer HEAD
+ exact runtime-env HEAD/tree
        |
        v
SKILL_RECEIPT_BOUND
-> REQUIREMENTS_BOUND
-> CONSUMER_MAPPING_BOUND
-> PROFILE_CLOSURE_RESOLVED
-> ENVIRONMENT_PLAN_RENDERED
-> PRESENCE_CHECKED
-> FIXED_SETUP_EXECUTED       (local/actions only)
-> CAPABILITY_PROBES_EXECUTED (local/actions only)
-> ENVIRONMENT_READY
```

Portable `resolve`, `plan`, and `check` never claim execution. Their runtime claims remain `NOT_EXERCISED`. `connector` and `public-consumer` modes refuse `prepare`; connector access is authorization/data access, not host compute.

`prepare` has no trailing shell surface. It may invoke only the workload and entrypoint IDs already present in the checked-in runtime-env catalog and resolved into the exact plan. Child workload receipts remain host-owned and the consolidated environment receipt contains only metadata/digests and variable **names/presence**, never values.

## Ownership boundary

- `skills-shared`: Skill identity, selection, procedural law, abstract runtime requirements.
- `runtime-env`: capability mapping, module/profile/workload/policy closure, fixed setup/probes, host receipts.
- consumer repo: thin immutable binding and exact repository subject.
- provider adapters: live GitHub/Forgejo/API mechanics outside this core contract.

A rendered plan is not runtime readiness. A passed setup is not readiness without every owning probe. Git Town and Forgejo live lanes remain independent `NOT_EXERCISED` claims until their exact runtime receipts exist.
