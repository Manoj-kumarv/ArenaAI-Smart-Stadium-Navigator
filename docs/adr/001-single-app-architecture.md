# ADR 001: Monolith App Architecture (FastAPI + React)

## Status
Accepted

## Context
The initial requirements suggested building four separate microservices apps with complex distributed infrastructure. Under strict timeline constraints and repository limits (< 10MB), deploying multiple separate microservices presents high integration risks and operations overhead.

## Decision
We decided to merge the views into a single, cohesive FastAPI + React repository. The frontend supports multiple user roles (ops_staff vs. fan) in a single SPA web application shell, matching capabilities dynamically according to token values.

## Consequences
- **Positive**: Simplifies deployment pipelines, guarantees consistency of API contracts, and stays well under the 10MB size limit.
- **Negative**: Scalability limit; single runtime memory pool must scale as a unit.
