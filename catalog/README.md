# `catalog/`

Owner: variable vocabulary and security metadata. Machine authority: [`variables.json`](variables.json).

```text
name proposed → metadata validated → declared once → referenced by modules
```

Inputs: variable name, secret flag, runtime scope, safe default/account link metadata. Output: canonical declaration. Forbidden: credential values, duplicate names, secret defaults, provider execution claims.
