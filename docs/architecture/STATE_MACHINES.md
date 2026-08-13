# Runtime contract state machines

## Variable catalog

```text
UNDECLARED
→ METADATA_VALIDATED
→ VARIABLE_DECLARED
→ REFERENCED_BY_MODULE
```

Failures: duplicate name, unknown field, committed secret default/value, invalid scope.

## Module/profile resolution

```text
MODULE_REQUESTED
→ VARIABLE_REFERENCES_RESOLVED
→ MODULE_VALID
→ PROFILE_COMPOSITION_REQUESTED
→ DEFAULTS_CONFLICT_CHECKED
→ PROFILE_RESOLVED
```

A module/profile declaration is not provider execution.

## Workload execution

```text
WORKLOAD_DECLARED
→ ENTRYPOINT_SELECTED
→ PROFILE_RESOLVED
→ REQUIRED_NAMES_PRESENT
→ EXACT_ENVIRONMENT_BUILT
→ FIXED_ENTRYPOINT_EXECUTED
→ PRIVATE_METADATA_RECEIPT
```

Terminals include invalid contract (`2`), required configuration absent/not run (`3`), fixed entrypoint failure, timeout, mutation/control failure, and PASS for the exact subject.

## Consumer projection

```text
REQUIREMENTS_RECEIVED
→ CLEAN_SOURCE_IDENTIFIED
→ CLOSURE_RESOLVED
→ DRY_RUN_PLAN
→ APPLY_EXPLICIT
→ PROJECTION_WRITTEN
→ STAGED_OFFLINE_VERIFY
→ CONSUMER_CANARY
→ HUMAN PROMOTION / ROLLBACK
```

Pre-commit cannot perform sync or read the source checkout.

## Secret broker

```text
SECRET_NAME_DECLARED
→ EXECUTION_PLANE_SELECTED
→ HOST/PROVIDER BROKER
→ FIXED ENTRYPOINT GETS MINIMAL ENV OR OPAQUE HANDLE
→ VALUE EXCLUDED FROM PORTABLE OUTPUT
```

Human/host authority owns authentication, Keychain, OAuth, provider session, and secret rotation.

## Delivery evidence

```text
ARTIFACT_PRESENT
→ DELIVERY_RECEIPT_VALID
→ PUBLICATION_ATTESTED
→ CURRENT SUBJECT VERIFIED
```

Delivery receipt does not prove the runtime/provider canary itself.
