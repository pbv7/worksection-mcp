# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.3.x (latest) | ✅ |
| < 0.3 | ❌ |

Only the latest release receives security fixes.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report vulnerabilities privately via [GitHub Security Advisories](https://github.com/pbv7/worksection-mcp/security/advisories/new).

Include as much of the following as possible:

- Description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- Affected versions
- Any suggested mitigations

You will receive an acknowledgment within **48 hours** and a status update within **7 days**.
If the vulnerability is confirmed, a fix will be prioritized based on severity.
You are welcome to request credit in the release notes.

## Scope

**In scope:**

- Authentication and token handling (`auth/`)
- Sensitive data exposure in logs or error messages
- Dependency vulnerabilities with a known exploit
- Docker image security issues

**Out of scope:**

- Vulnerabilities requiring physical access to the host machine
- Issues in the Worksection API itself
- Self-signed certificate warnings (expected behavior for local OAuth callback)
- Rate limiting bypass (Worksection API enforces its own limits)

## Security Design Notes

- OAuth2 tokens are encrypted at rest using Fernet symmetric encryption
- Encryption keys and tokens are stored in `./data/` which should have `chmod 700`
- The MCP server binds to `127.0.0.1` by default (localhost only)
- All API operations are read-only — no write or delete tools are exposed
- Authorization codes and token values are redacted from debug logs

## Current Deployment Assumptions

This project is designed for **single-user, self-hosted use** — one person connecting
their own Worksection account to their own AI assistant on a trusted machine. Several
security decisions follow from this assumption:

- **No MCP endpoint authentication** — the server trusts the local network. This is
  appropriate when bound to `127.0.0.1`, but not for a publicly exposed deployment.
- **Symmetric encryption key on disk** — the Fernet key lives next to the tokens it
  protects. Acceptable for a single-user local setup; a multi-user system should use
  a secrets manager or OS keyring instead.
- **Single OAuth2 app credential** — one `client_id`/`client_secret` pair per instance.
  There is no per-user credential isolation.
- **No audit logging** — authentication events and API calls are not logged to a
  persistent audit trail.
- **No secret rotation mechanism** — token and key rotation must be done manually.

If this application were to become multi-user or publicly accessible, the above areas
would need to be hardened before deployment. Security reports assuming a multi-user
threat model are welcome but will be evaluated against the intended single-user scope.
