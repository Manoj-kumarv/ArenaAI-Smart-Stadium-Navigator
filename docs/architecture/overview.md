# System Architecture

## C4 Container Overview

ArenaIQ consists of a single web repository containerized using a multi-stage Docker build:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  React Components │ WebSocket Client │ State Management     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       API Gateway Layer                      │
│    FastAPI Routers │ Request Validation │ Error Handling    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│   Business Logic │ Orchestration │ Domain Operations        │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AI Agent Layer  │  │ Repository Layer│  │ External APIs   │
│ Orchestrator    │  │ Data Access     │  │ Gemini API      │
│ Crowd/Fan/Inc.  │  │ Abstractions    │  │ Cache/Queue     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│   Database │ Message Bus │ Monitoring │ Configuration       │
└─────────────────────────────────────────────────────────────┐
```

### Components Description

1. **FastAPI Backend (Python)**:
   - Manages state, processes requests, implements security header parameters and correlation ID propagation.
   - Enforces rate limiting per endpoint.
2. **React Frontend (JavaScript)**:
   - Displays operations view (Digital Twin) and fan portal. Uses WebSocket channel to capture live telemetry updates.
   - Integrates accessibility layers and contrast themes.
3. **AI Orchestrator**:
   - Routes requests to specialized agents or deterministic fallbacks.
   - Manages trilingual translation consistency.
4. **Data Store**:
   - SQLite DB for persistence, structured via SQLAlchemy ORM.
