# Universal Testing & Verification Standards

## Objective
Establish a comprehensive, multi-layered testing workflow to validate core functionality, secure code modifications, detect regressions, and guarantee robust behavior under extreme input scenarios.

---

## 1. Test Architecture & Lifecycle

### 1.1. Deterministic & Isolated Environments
- **State Isolation**: Every test must run in a clean environment. Use separate databases (e.g., in-memory SQLite `sqlite://` or isolated Docker database containers) that reset or rollback after each test execution.
- **No Global Leakage**: Do not allow tests to modify global application state (like environment variables or module constants) without using explicit mock patches or context managers.
- **Parallel Execution**: Design test suites to be thread-safe and isolated so they can be run in parallel (e.g., via `pytest-xdist` or `vitest`) to reduce build queue times.

---

## 2. Multi-Tiered Testing Strategy

### 2.1. Unit Testing
- Mock all external dependencies, network interfaces, database transactions, and AI API endpoints.
- Ensure that unit tests run fast and focus on single classes or pure functions.
- Write tests to validate boundary margins (upper, lower, and exact limits). For example, test occupancy thresholds of exactly `0.59`, `0.60`, and `0.61`.

### 2.2. Integration & End-to-End Testing
- Write scenario-driven tests that execute complete user workflows.
- *Examples*:
  1. User authenticates via API → User creates an incident request → Server orchestrates AI agent → Audit log is verified.
  2. WebSocket telemetry registers a client → Telemetry loop pushes congestion update → Client receives data payload.

### 2.3. Property-Based Testing (Hypothesis)
Use property-based testing libraries (e.g., `Hypothesis` in Python) to validate system invariants across hundreds of auto-generated input ranges.
- Validate that functions handling calculations (like density scales or crowd margins) always produce expected, bounded values under all inputs.
```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=0.0, max_value=1.0))
def test_occupancy_color_always_valid(occupancy: float):
    color = get_occupancy_color(occupancy)
    assert color in ["green", "yellow", "red", "critical"]
```

### 2.4. Contract & Schema Validation Testing
Verify that all API response JSON payloads strictly match the OpenAPI schemas.
- If a route returns data, execute tests that decode and validate the payload structure using validation libraries (e.g., Pydantic `model_validate`).

### 2.5. Security Verification Tests
Verify security controls:
- Try accessing protected endpoints with expired, invalid, or missing tokens, verifying that HTTP `401 Unauthorized` or `403 Forbidden` statuses are returned.
- Feed malicious inputs (like prompt injection, PII text, and large payloads) and verify that the security filters block them.

---

## 3. Metrics & Coverage Goals
- **Code Coverage targets**: Maintain **95%+ statement coverage** on all business-critical modules (services, security filters, database controllers). Maintain a minimum **85%+ overall coverage** for the entire backend application.
- **Test Quality**: Write test assertions that verify data properties, not just execution. Avoid writing dummy tests that call code without checking results.
