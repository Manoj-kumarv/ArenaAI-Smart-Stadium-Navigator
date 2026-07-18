# ArenaIQ Documentation Index

Welcome to the comprehensive technical documentation for ArenaIQ Smart Stadium Navigator, a production-grade operations platform for the FIFA World Cup 2026.

## Documentation Sections

1. **[System Architecture](architecture/overview.md)**
   - C4 context and container diagrams, data flow overview, and service relationships.
2. **[Architecture Decision Records (ADR)](adr/)**
   - Traceable records of foundational engineering trade-offs:
     - [ADR 001: Monolith App Architecture](adr/001-single-app-architecture.md)
     - [ADR 002: JWT + SQLite authentication strategy](adr/002-jwt-sqlite-over-cognito.md)
     - [ADR 003: Deterministic Rule-Based Fallback logic](adr/003-rule-based-fallback.md)
     - [ADR 004: Event-driven WebSocket push for telemetry](adr/004-websocket-telemetry.md)
3. **[Security Model & Threat Mitigation](security/threat-model.md)**
   - PII protection logic, prompt injection filters, and secure headers policy.
4. **[Operational Runbook](operations/runbook.md)**
   - Deployment configuration on Render, telemetry scaling guidelines, database backups, and health monitoring.
