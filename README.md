# ArenaIQ — Smart Stadium Navigator

> **GenAI-powered operations platform for FIFA World Cup 2026**

[![CI — ArenaIQ](https://github.com/Manoj-kumarv/ArenaAI-Smart-Stadium-Navigator/actions/workflows/ci.yml/badge.svg)](https://github.com/Manoj-kumarv/ArenaAI-Smart-Stadium-Navigator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://img.shields.io/badge/Coverage-93%25-brightgreen.svg)](#running-tests)
[![Accessibility Compliant](https://img.shields.io/badge/A11y-WCAG%20AA-blue.svg)](#accessibility-standards)

ArenaIQ gives FIFA World Cup 2026 stadium operations teams real-time situational awareness through a live Digital Twin, AI-driven incident resolution, and atomic multilingual PA broadcasts — while giving fans a trilingual (EN/ES/AR) assistant for directions, food, and accessibility info. Every decision is logged to an immutable audit trail and traceable to a specific AI agent response.

## 📚 Project Documentation

Comprehensive technical documentation is located in the **[docs/](docs/index.md)** directory:
* **[System Architecture](docs/architecture/overview.md)** — C4 container models and layering.
* **[Architecture Decision Records (ADRs)](docs/adr/README.md)** — Core engineering design trade-offs.
* **[Security Model & Threat Mitigation](docs/security/threat-model.md)** — PII filters, sanitization, and secure headers.
* **[Operational Runbook](docs/operations/runbook.md)** — Deployments, backups, and monitoring.

---

## 🤖 Generative AI Integration

In accordance with tournament guidelines, GenAI integration is central to ArenaIQ:
1. **Intent-based AI Orchestrator**: Uses Gemini 1.5 Flash to route operations requests to specialized domain cognitive agents.
2. **AI Crowd Management Agent**: Explains zone congestion and generates proactive, context-aware queue mitigation strategies.
3. **Multilingual PA Announcement Generator**: Generates PA broadcasts in English, Spanish, and Arabic dynamically. Enforces transactional atomicity.
4. **Interactive Fan Assistant**: Provides trilingual Q&A directions, catering options, and accessibility help.

---

## Setup & Running

### Prerequisites
- Python 3.11+, Node 18+, npm

### Backend

```bash
cd apps/backend

# Copy env template and fill in values
cp .env.example .env

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# Seed the database (creates arenaiq.db with 25 zones, 2 users, 5 incidents)
python -m scripts.seed

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Running Tests

### Backend (pytest with coverage)

```bash
cd apps/backend
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend (Vitest)

```bash
cd apps/frontend
npm test
```

---

## Deployment (Render)

The `render.yaml` in the repo root configures two services:
1. **arenaiq-backend** — Python web service, `uvicorn app.main:app`
2. **arenaiq-frontend** — Static site, `npm ci && npm run build` → `dist/`
