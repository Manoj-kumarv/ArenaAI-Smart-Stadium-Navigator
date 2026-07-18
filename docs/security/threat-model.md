# Security Threat Model

## Threat Vectors & Mitigations

| Threat | Risk | Mitigation | Status |
| --- | --- | --- | --- |
| **Prompt Injection** | High | Input scanned against regex blacklist before routing to LLM. Evaluated pre-execution. | Mitigated |
| **PII Data Leak** | Medium | Validation filters reject phone, email, SSN, and CC patterns. Output scrubbed before returning. | Mitigated |
| **Brute Force / DoS** | High | Rate limits configured per IP client. Maximum payload size limited to 1MB. | Mitigated |
| **Cross-Site Scripting (XSS)** | High | Content Security Policy (CSP) headers block execution of unauthorized third-party scripts. | Mitigated |
| **Clickjacking** | Medium | `X-Frame-Options: DENY` header injected into all response payloads. | Mitigated |

## PII Sanitization Flowchart

```
Input Request
     │
     ▼
Email/Phone/SSN Scan ─────[Found]─────► HTTP 422 (Rejected)
     │
   [None]
     ▼
Prompt Injection Scan ────[Found]─────► HTTP 422 (Rejected)
     │
   [None]
     ▼
Generate Response ───► Scrub Output ───► Send Clean Response
```
