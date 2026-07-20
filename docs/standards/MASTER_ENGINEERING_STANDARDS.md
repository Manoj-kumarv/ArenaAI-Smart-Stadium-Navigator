# Master Engineering Standards & AI Evaluation Blueprint (v1.0)

## Executive Summary
This document serves as the master overview and deployment guide for the **Universal Engineering Standards** designed to guarantee a perfect **100/100** score in static analyzers and AI evaluation systems. 

By applying these standardized pillars to any future codebase at initialization, your generated projects will immediately compile with production-grade modularity, bulletproof security, high efficiency, exhaustive tests, accessible UI, and perfect logic.

---

## 🏛️ The Six Pillars of AI Evaluation

### 1. Code Quality & Modularity
- **Architecture**: Enforce a strict Clean Architecture pattern. Routers $\rightarrow$ Services $\rightarrow$ Repositories $\rightarrow$ DB. Never permit routes to directly access DB/ORM sessions.
- **Constraints**: Keep files $\le 200$ lines, functions $\le 30$ lines, classes $\le 250$ lines, and cyclomatic complexity $\le 10$.
- **Typing & Linting**: Enforce 100% strict type hints on all parameters/returns. Run Ruff (Python) or ESLint/Oxlint (JS/TS) to maintain 0 warnings.
- *Detailed Spec*: [standards_code_quality.md](standards_code_quality.md)

### 2. Efficiency & Performance
- **Database**: Eliminate N+1 query patterns using eager-loading joins. Apply single and composite indexes on columns used in filters and joins.
- **Payloads**: Use pagination on all listing endpoints. Apply Gzip compression middleware to responses exceeding 1KB.
- **Async Safety**: Never run blocking calls (`time.sleep` or synchronous request clients) inside the async event loop.
- *Detailed Spec*: [standards_efficiency.md](standards_efficiency.md)

### 3. Security & Vulnerability Hardening
- **Secrets Management**: Absolutely zero hardcoded credentials, ports, or API keys in code. Load all settings via validated schemas (e.g., Pydantic Settings).
- **Web Protections**: Restrict CORS to explicitly whitelisted domains. Enforce security headers (CSP, HSTS, X-Frame-Options) and apply IP/user rate-limiters.
- **AI Safety & PII Filters**: Sanitise all user inputs for PII (email, phone, cards) before sending to external LLM endpoints.
- *Detailed Spec*: [standards_security.md](standards_security.md)

### 4. Testing & QA Rigor
- **Isolated Tests**: Use an in-memory SQLite DB (`sqlite://`) or clean Docker db containers to isolate testing environments.
- **Multi-layered Coverage**: Combine Unit tests (mocking external connections), Integration tests (verifying E2E workflows), and Property-Based tests (e.g., Python's `Hypothesis`) to check invariant limits.
- **Coverage Target**: Aim for **95%+ coverage** on all business services and security filters.
- *Detailed Spec*: [standards_testing.md](standards_testing.md)

### 5. Accessibility & i18n
- **Semantic Structure**: Maintain correct heading hierarchies (`<h1>` down to `<h6>` chronologically). Ensure keyboard navigability (visible focus indicators, focus traps inside modals, skip links).
- **Aria & Color**: Implement `aria-label`, `aria-live` regions for dynamic elements, and visual contrast ratios exceeding **4.5:1** (WCAG AA).
- **Internationalization**: Support dynamic language switching and adapt wrappers to support text growth and RTL language layouts (e.g., Arabic).
- *Detailed Spec*: [standards_accessibility.md](standards_accessibility.md)

### 6. Problem Statement Alignment & Orchestration
- **Intent Routing**: Classify user input intent dynamically to direct queries to specialized cognitive agents.
- **Fail-safety**: Always implement deterministic fallback logic when LLM APIs are offline.
- **ADR & Documentation**: Document every design decision inside Architecture Decision Records (`docs/adr/`) and maintain a structured README detailing vertical approaches, workflows, and logic.
- *Detailed Spec*: [standards_problem_alignment.md](standards_problem_alignment.md)

---

## 🛠️ Step-by-Step Implementation Guide for Future Projects

Follow this checklist to initialize your next project using these engineering standard guidelines:

### Step 1: Feed the Standards into your AI coding tool
Before writing code, copy the contents of the 6 detailed standards files into your coding assistant's context (e.g., as a `.cursorrules` file or system prompt directives). Instruct the agent to strictly reject generating any code that violates these limits.

### Step 2: Establish the Directory Layout
Initialize your backend/frontend directories following the standardized architectural tree:
```bash
# Example shell script to initialize directories
mkdir -p app/{api/routers,services,repositories,models,schemas,database,config,utils,constants,exceptions,logging,ai,prompts}
```

### Step 3: Implement Pre-Commit Automation
Create a `.pre-commit-config.yaml` file in the root directory to automate formatting and linting checks:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```
Install the hooks:
```bash
pip install pre-commit
pre-commit install
```

### Step 4: Configure the CI/CD Pipeline
Create a GitHub Actions workflow `.github/workflows/ci.yml` that automatically runs on every push:
```yaml
name: CI Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt ruff mypy pytest pytest-cov
      - name: Lint check
        run: ruff check app/
      - name: Type check
        run: mypy app/
      - name: Run tests with coverage
        run: pytest --cov=app --cov-fail-under=85
```
