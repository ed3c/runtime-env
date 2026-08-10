# Agent runtime execution topology

Environment-variable names do not create execution capability. Treat repository
context, compute, network reachability, credentials, and authorization as five
independent contracts.

## What each plane can actually do

| Plane | Compute | Can reach this Mac's localhost or devices? | Correct use |
|---|---|---|---|
| ChatGPT GitHub app | No repository shell | No | Search, read, and reason over selected GitHub repository content |
| Codex cloud | OpenAI-managed container | No; `localhost` is the cloud container | Portable builds, tests, lint, and code changes |
| GitHub-hosted Actions | Ephemeral GitHub-hosted VM | No | Public-repository CI on untrusted contributions |
| Dedicated self-hosted runner | The registered host | Yes, if deliberately installed on that host | Trusted, gated jobs needing private-network or physical-hardware access |
| Local Codex/App/CLI host | The user's machine under its sandbox and approval policy | Yes, subject to local permissions | Interactive localhost, simulator, and real-device work |
| Remote typed MCP through Secure MCP Tunnel | Tool implementation runs on the connected private host | Yes, but only through declared tools | Narrow local capabilities invoked from supported OpenAI products |

The GitHub app is a repository context plane, not a compute plane. Committing an
MCP configuration to GitHub also does nothing by itself: an MCP server must be
running on a reachable compute host, and the caller must be authorized to use
its declared tools.

Codex cloud creates a container, checks out the selected repository revision,
runs setup, and then lets the agent execute terminal commands. Setup has network
access; agent-phase network access is off by default and can be constrained by
domain and HTTP method. Environment variables remain available for the chat,
while configured secrets are removed after setup. Consequently, a secret needed
by tests during the agent phase must not be misclassified as a setup-only
secret.

## Recommended composition

1. Use `codex-cloud-portable` for builds and tests whose dependencies can exist
   entirely inside the managed container.
2. Keep physical-device, local Forgejo, Keychain, and other loopback work on a
   local host. A cloud runner cannot make its own `localhost` mean this Mac.
3. When ChatGPT must invoke a local-only capability, run a narrow MCP server on
   the local host and connect it with Secure MCP Tunnel. Expose typed operations
   such as `verify_runtime`, `run_ios_flow`, or `forgejo_status`; never expose a generic shell tool,
   arbitrary filesystem access, or raw credential reads.
4. Use tool allowlists, schema validation, bounded timeouts, redacted receipts,
   and approval requirements for sensitive mutations. MCP is an authorization
   surface, not a sandbox replacement.
5. Use GitHub-hosted Actions for public pull requests. GitHub warns that
   self-hosted runners should almost never execute public pull-request code,
   because untrusted contributors can persistently compromise the host. Reserve
   a dedicated or ephemeral self-hosted runner for trusted branches or explicitly
   admitted workflows, with no automatic execution of fork code.

This arrangement removes accidental reachability limits without flattening the
security boundary: portable work goes to a disposable container; physical work
stays local; ChatGPT reaches only typed local actions; CI does not hand public PR
authors the keys to a developer machine.

## Accounts and host configuration still required

| Capability | Human or admin setup | Runtime contract |
|---|---|---|
| Codex cloud | Create/select an environment in Codex settings; configure setup, environment variables, and any setup-only secrets | `profiles/codex-cloud-portable.json` |
| ChatGPT write-capable custom MCP app | Eligible ChatGPT workspace plan and developer-mode/admin configuration | `profiles/secure-mcp-tunnel.json` plus a deployed typed MCP server |
| Secure MCP Tunnel | OpenAI Platform credentials and the tunnel client running on the private host | `OPENAI_API_KEY`, optional project/org identifiers, and the assigned endpoint |
| GitHub self-hosted runner | Register a dedicated runner at repository, organization, or enterprise scope; constrain runner groups | Registration token is operational input, not a committed project variable |
| E2B | E2B account and API key | `E2B_API_KEY` |
| Gemini | Google AI Studio account and API key | `GEMINI_API_KEY` |
| Local Forgejo | Existing localhost account/session, Git credential helper, or explicitly selected fallback | See `docs/runtimes/forgejo-localhost.md` |

## Official anchors

- [OpenAI: connecting GitHub to ChatGPT](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)
  describes repository search/read context; it does not promise a repository
  shell.
- [OpenAI: Codex cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environment)
  defines the container, setup, environment-variable, secret, and cache model.
- [OpenAI: Codex agent internet access](https://learn.chatgpt.com/docs/cloud/internet-access)
  defines the default-off agent network and domain/method restrictions.
- [OpenAI: MCP and connectors](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
  distinguishes maintained connectors from remote MCP tools and documents
  approvals and tool allowlists.
- [OpenAI: Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
  is the supported bridge for private, on-premises, or developer-machine MCP
  servers without publishing them directly to the internet.
- [GitHub: self-hosted runners](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)
  defines host requirements, outbound connectivity, and ephemeral runners.
- [GitHub: secure use of Actions](https://docs.github.com/en/actions/reference/security/secure-use)
  documents the persistent-compromise risk of untrusted code on self-hosted
  runners.
