# Universal Code Quality & Engineering Standards (v1.0)

## Objective
Generate production-quality, enterprise-grade code that maximizes maintainability, readability, modularity, testability, scalability, and security. The project should score perfectly on static analysis tools (e.g., SonarQube, CodeClimate, DeepSource, Codacy, CodeRabbit) and AI evaluation frameworks.

---

## 1. Architectural Patterns (Clean Architecture)
Enforce a strict layered flow of control and dependencies. Lower layers must never access higher layers directly.

```
Client / Frontend
     │
     ▼
API Layer (Routers / Controllers)
     │
     ▼
Service Layer (Business Logic & Workflows)
     │
     ▼
Repository Layer (Data Abstraction & CRUD)
     │
     ▼
Database / External Services (SQL, APIs, LLMs)
```

- **Rule 1.1**: API controllers/routers must never perform direct database queries (no SQL/ORM session execution in routers).
- **Rule 1.2**: API controllers must not contain business logic, loops, or complex data manipulation. They only validate inputs, call services, and return responses.
- **Rule 1.3**: Use Dependency Injection to provide services, repositories, and third-party clients (e.g., LLM wrapper, Redis, DB clients) to avoid hardcoded connections.

---

## 2. Standardized Folder Structure
Maintain a highly organized repository layout to prevent mixing unrelated responsibilities.

```
app/
├── api/                  # API Gateway Layer
│   ├── routers/          # HTTP Endpoint mappings
│   ├── dependencies/     # Dependency injection providers / Auth checks
│   └── middleware/       # CORS, security headers, rate limiters
├── services/             # Core business workflows (Service Layer)
├── repositories/         # Database access abstraction (Repository Layer)
├── models/               # Database entity schemas / ORM classes
├── schemas/              # Input/Output DTO schemas (Pydantic / TS types)
├── database/             # Connection configurations & migrations
├── config/               # Settings, env validation, profiles
├── utils/                # Pure utility functions & mathematical helpers
├── constants/            # Global constants & configuration bounds
├── exceptions/           # Custom exception definitions
├── logging/              # Structured logging configuration
├── ai/                   # AI clients, prompt orchestrators, and parsers
├── prompts/              # Plaintext prompt templates
├── tests/                # Unit & Integration test suites
└── main.py               # Fast API / Server entrypoint
```

---

## 3. Class, File, and Function Size Constraints
Strict limits to prevent "God Classes" and spaghetti code.

| Parameter | Preferred Metric | Hard Maximum Limit | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Function Length** | 10–20 lines | 30 lines | Extract helper methods or use strategy pattern. |
| **File Length** | 100–150 lines | 200 lines | Split domain logic into smaller files/sub-modules. |
| **Class Length** | <150 lines | 250 lines | Delegate responsibilities using composition. |
| **Cyclomatic Complexity** | 5 | 10 | Eliminate deep nesting (`if/if/if`) via guard clauses. |

---

## 4. Coding Conventions & Code Quality Rules

### 4.1. Single Responsibility Principle (SRP)
Every class, file, and function must have exactly one reason to change.
- *Bad*: `UserService` handling signups, PDF generation, email dispatching, and vector searches.
- *Good*: Split into `AuthenticationService`, `PDFService`, `EmailService`, and `VectorStoreService`.

### 4.2. Cyclomatic Complexity Reduction
Never exceed 3 levels of indentation. Use early returns and guard clauses to keep logic flat.
```python
# GOOD: Early returns prevent nesting
if user is None:
    return Response(error="Not Found")
if not user.is_active:
    return Response(error="Inactive")
return process_active_user(user)
```

### 4.3. Type Safety
All function arguments and return types must be fully typed. Never use untyped signatures or wildcard collections like `Any` or `dict` without schemas.
```python
# Python
def analyze_query(query: str) -> QueryAnalysisResponse: ...

# TypeScript / JavaScript
async function getZones(): Promise<Zone[]> { ... }
```

### 4.4. Explicit Documentation
All public classes, methods, and functions require docstrings outlining the intent, arguments, return type, and potential exceptions.
```python
"""
Analyze a zone's density telemetry and generate queue-mitigation advice.

Args:
    zone_id: Unique string identifier of the stadium zone.
    density: Current occupancy percentage (0.0 to 1.0).

Returns:
    An AnalysisResult object containing strategies.

Raises:
    NotFoundError: If the zone does not exist in the DB.
"""
```

---

## 5. Tooling & Static Analysis Setup
Validate and format on every code save. Target zero issues during analysis.

1. **Ruff / Pylint (Python Linting)**: Enforce strict rulesets (select `E`, `W`, `F`, `I`, `N`, `D`, `UP`, `B`, `S`, `T20`, `SIM`, `RUF`).
2. **Black (Python Formatting)**: Run `black --check .` to guarantee formatting consistency.
3. **Mypy (Type Checking)**: Run `mypy` in strict mode to capture missing annotations or invalid conversions.
4. **Prettier & ESLint / Oxlint (Frontend)**: Enforce absolute format consistency in JS/TS environments.
5. **SonarQube / DeepSource**: Maintain **A-grade** quality scores, **0** code smells, **0** critical/high maintainability issues, and **0%** duplicate code metrics.
