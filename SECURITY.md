# Security policy

## Never commit values

This repository stores parameter names and safe non-secret defaults only. Do not open an issue or pull request containing a credential. Revoke a credential immediately if it is exposed; deleting a Git commit does not remove it from forks or caches.

The following belong outside Git:

- `.env` and environment-specific variants;
- App Store Connect `.p8` files, certificates, and signing keys;
- cloud, model-provider, observability, browser, and sandbox tokens;
- test account passwords and TOTP seeds.

## Reporting

Report a suspected exposure privately through GitHub's security advisory interface for this repository. Include only the affected path and credential provider; do not paste the value.

## Trust boundaries

- Public pull requests must not run on persistent self-hosted runners.
- Prefer GitHub OIDC and short-lived credentials to static cloud keys.
- Secure MCP Tunnel tools must be typed and allowlisted; a generic shell endpoint is out of scope.
- A rendered template is not proof that an account, key, device, runner, or MCP server exists.
