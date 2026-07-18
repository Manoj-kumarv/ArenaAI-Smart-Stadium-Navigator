# Security Policy

## Supported Versions

We actively monitor and patch the following versions of ArenaIQ:

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |
| < 1.0.0 | No        |

## Reporting a Vulnerability

If you discover a potential security vulnerability within ArenaIQ, please **do not open a public GitHub issue**. Instead, follow these steps:

1. Draft a detailed explanation of the vulnerability, including step-by-step instructions to reproduce the issue (and a proof-of-concept if possible).
2. Email your report privately to `security@arenaiq.local` (or the repository maintainer).
3. We will acknowledge receipt of your report within 48 hours and coordinate a timeline for remediation and public disclosure.

## Security Practices Enforced

- **Input Sanitization**: All incoming text fields are filtered for prompt injection patterns and Personally Identifiable Information (PII) before passing to GenAI models.
- **OWASP Secure Headers**: All API endpoints return security headers including CSP, HSTS, X-Content-Type-Options, and X-Frame-Options to prevent browser-based attacks.
- **CORS Lock**: Cross-Origin Resource Sharing is locked down to verified domains to block unauthorized third-party site requests.
- **Rate Limiting**: Hard limits are applied on endpoints based on IP address client tracking to mitigate brute-force and Denial of Service (DoS) attempts.
