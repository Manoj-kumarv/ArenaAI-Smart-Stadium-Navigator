# Universal Problem Statement Alignment & Logical Decision-Making Standards

## Objective
Ensure projects fully align with challenge requirements, implement logical decision-making based on user context, demonstrate practical real-world usability, and provide complete transparency of design choices through documentation.

---

## 1. Context-Aware Decision Logic

### 1.1. Smart Multi-Agent Orchestration
When designing assistants, use an intent-based orchestrator to categorize user queries. Route each request dynamically to specialized cognitive domain agents (e.g., routing mapping queries to navigation agents, safety issues to incident agents, etc.) to keep agents highly focused.
```
User Request
     │
     ▼
AI Intent Classifier / Orchestrator
     ├── (Crowd query)    ──► Crowd Management Agent
     ├── (Safety query)   ──► Incident Resolution Agent
     └── (General query)  ──► Fan Q&A Agent
```

### 1.2. Deterministic AI Fallbacks
Always assume external generative AI APIs (such as Gemini or third-party integrations) can fail or timeout.
- Implement a deterministic, rule-based fallback system that catches timeouts or API connection errors and returns a high-quality, pre-defined response.
- Log AI call metrics (failures vs. successes) to monitor degradation.

### 1.3. Traceability (Immutable Audit Logs)
Every critical decision, especially those orchestrated by AI (like incident resolution or emergency broadcasts), must be logged to an immutable audit trail database.
- Track timestamps, user roles, input contexts, output actions, confidence scores, and whether the system used AI or a rule-based fallback.

---

## 2. Real-World Usability & Persona Design
- **Logical Rules**: Emulate real-world conditions. For example, if crowd density crosses specific thresholds (like 0.85), automatically trigger alerts.
- **Practical Workflows**: The frontend interface must act as a functional digital twin, displaying live, actionable data feeds (like charts and active maps) rather than static mockup assets.

---

## 3. Comprehensive Documentation & Transparency

### 3.1. Standardized README Guidelines
A complete, production-grade project must include a `README.md` at the root containing the following key sections:
1. **Vertical/Persona Selected**: Clear explanation of the chosen challenge context.
2. **Technical Approach & Logic**: How the system connects AI agents, telemetry, and security guardrails.
3. **System Architecture**: High-level and detailed diagrams (using C4 models or Merlin diagrams).
4. **How It Works**: Step-by-step user flow.
5. **Assumptions Made**: Technical boundaries, mock datasets, and hardware/API constraints.
6. **Local Setup & Installation**: Reproducible scripts and setup requirements.

### 3.2. Architecture Decision Records (ADRs)
Create traceable Architecture Decision Records (`docs/adr/`) for all critical engineering design trade-offs:
- *Template format*: Title, Date, Context, Options Considered, Decision made, and Consequences.
- *Examples*: Deciding on JWT + SQLite local auth instead of cognito, choosing rule-based fallbacks, using persistent WebSockets for live maps status.
- Maintain ADR indices mapping decision numbers to files.
