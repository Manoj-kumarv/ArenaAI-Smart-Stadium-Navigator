# Operational Runbook

## Deployment

ArenaIQ is configured for zero-downtime deployment on Render via `render.yaml`.

### Build Verification
Verify builds locally before deploying:
```bash
# Backend build and lint check
cd apps/backend
pip install -r requirements.txt
ruff check app/

# Frontend build check
cd apps/frontend
npm run build
```

## Monitoring & Health Checks

- **Liveness Probe**: `/health` endpoint validates that the FastAPI ASGI loop is serving requests.
- **Readiness Probe**: `/ready` endpoint validates database accessibility and status configuration.

## Backup and Recovery

1. **Database Preservation**:
   - The SQLite database file `arenaiq.db` resides inside the app's root.
   - For PostgreSQL production environments, execute daily db dumps:
     ```bash
     pg_dump -U username dbname > backup.sql
     ```
2. **Failure Mitigation**:
   - If the database file is corrupted or lost, run `python -m scripts.seed` to restore initial stadium settings, including default user roles and zones.
