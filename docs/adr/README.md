# Architecture Decision Records (ADRs)

This directory contains records of the major architectural and design decisions made during the design and development of ArenaIQ.

## Records List

- **[ADR 001: Monolith App Architecture](001-single-app-architecture.md)**
  - Decides on a consolidated monolith repository structure (FastAPI + React) instead of microservices to comply with repository size requirements.
- **[ADR 002: JWT + SQLite authentication strategy](002-jwt-sqlite-over-cognito.md)**
  - Documents storing credentials locally using JWT session verification and SQLite instead of Cognito to run free of external services.
- **[ADR 003: Deterministic Rule-Based Fallback logic](003-rule-based-fallback.md)**
  - Establishes fallback playbook models when Gemini AI requests fail or timeout, guaranteeing continuous service availability.
- **[ADR 004: Event-driven WebSocket push for telemetry](004-websocket-telemetry.md)**
  - Leverages persistent connection sockets for real-time digital twin maps status changes rather than polling.
