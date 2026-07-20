# Universal Security & Threat Mitigation Standards

## Objective
Establish defense-in-depth controls across the system, ensuring data privacy, protection against common web vulnerabilities, secure authentication workflows, and safe generative AI integrations.

---

## 1. Secrets & Credentials Management
- **Rule 1.1**: Never commit secrets, credentials, API keys, private certificates, or database connection strings to source control.
- **Rule 1.2**: Retrieve all sensitive configurations from the environment. Use settings validators (e.g., Pydantic Settings in Python) to fail-fast during startup if any required environment variable is missing or invalid.
- **Rule 1.3**: Add `.env` and all deployment keys to `.gitignore` files at initialization.

---

## 2. API Hardening & Web Security

### 2.1. CORS Explicit Whitelisting
Never use wildcard origins (`*`) for Cross-Origin Resource Sharing (CORS) on authenticated endpoints.
- Maintain a strict whitelist of allowed domains (e.g., specific production domains and localhost during development).

### 2.2. Secure HTTP Headers Middleware
Ensure every HTTP response includes robust security headers:
- **Content Security Policy (CSP)**: Restrict scripts, styles, and resource fetches to trusted sources.
- **HTTP Strict Transport Security (HSTS)**: Force all connections over HTTPS.
- **X-Frame-Options**: Enforce `DENY` or `SAMEORIGIN` to prevent clickjacking.
- **X-Content-Type-Options**: Set to `nosniff` to prevent mime-type sniffing.
- **Referrer-Policy**: Restrict exposure of referrers.

### 2.3. Request Size Limiting
Enforce limits on the maximum payload size allowed in POST/PUT request bodies (e.g., max 1MB–10MB depending on endpoints) to mitigate Denial of Service (DoS) attempts.

### 2.4. Rate Limiting
Enforce rate limiting on all endpoints:
- Apply low limits on expensive operations (e.g., AI queries, login attempts, PA broadcast generation).
- Utilize standard middleware (like SlowAPI or Redis token bucket) to throttle requests by client IP or authenticated user ID.

---

## 3. Authentication & RBAC

### 3.1. Password Hashing
Never store plain-text passwords. Use secure, standard hashing algorithms (such as bcrypt or Argon2) with a strong salt.

### 3.2. Stateless JWT Authorization
- **Token Signature**: Cryptographically sign JWT tokens using strong algorithms (such as HS256/RS256) with high-entropy keys.
- **Time Limits**: Keep token expiration windows short (e.g., 15–30 minutes) and use refresh tokens for continuous session management.
- **Role-Based Access Control (RBAC)**: Ensure role membership is validated server-side on every request. Never rely on the client frontend for permission validation.

---

## 4. Input Sanitization & AI Guardrails

### 4.1. SQL Injection Prevention
Always use parameterized queries or object-relational mapping (ORM) frameworks. Never format or concatenate strings directly into SQL statement strings.

### 4.2. PII Filtration
Prior to passing any user-provided content to external LLMs or third-party APIs, apply regex-based and token-based scrubbing to remove Personally Identifiable Information (PII) such as emails, phone numbers, and credentials.

### 4.3. LLM Prompt Injection & Refusal Logic
- Enforce strict system prompt boundaries to prevent prompt escape or manipulation.
- Implement classification guardrails to identify and refuse out-of-domain prompts (e.g., refusing queries about coding, math, or other non-stadium topics if building a stadium assistant).
- If the AI model response is corrupted or does not conform to the expected output schema, trigger a deterministic fallback response rather than returning errors.
