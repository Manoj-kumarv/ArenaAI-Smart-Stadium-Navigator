# ADR 002: JWT + SQLite authentication strategy

## Status
Accepted

## Context
Deploying enterprise authentication tools like AWS Cognito or DynamoDB requires paid AWS accounts and complex cloud configuration. To make the application run self-contained and free on cloud providers like Render, we need a local, lightweight data layer.

## Decision
We implemented JWT stateless session auth with bcrypt password hashing stored in a local SQLite database. SQLAlchemy is used as the ORM, allowing developers to switch to PostgreSQL or Postgres-compatible RDS simply by modifying the `DATABASE_URL` environment variable.

## Consequences
- **Positive**: Zero external cloud dependency. Fast setup and easy migration to Postgres database.
- **Negative**: No built-in Multi-Factor Authentication (MFA); security relies entirely on signature verification via the backend's local `SECRET_KEY`.
