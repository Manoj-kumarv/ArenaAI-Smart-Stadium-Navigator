# Universal Efficiency & Performance Standards

## Objective
Ensure low-latency, high-throughput backend performance and highly responsive frontend user interfaces, maximizing the efficiency of compute, network, and database resources.

---

## 1. Database Operations & Query Optimization

### 1.1. Eliminate the N+1 Query Problem
Never execute queries inside loops. Use eager loading (`joinedload` / `selectinload` in SQLAlchemy, or `INCLUDE` joins in SQL) to pull related items in a single round trip.
```python
# AVOID (triggers query per incident)
for incident in db.query(Incident).all():
    print(incident.zone.name)

# PREFER (single query with join)
incidents = db.query(Incident).options(joinedload(Incident.zone)).all()
```

### 1.2. Database Indexing
Define explicit, single-column or composite indexes on fields that are frequently used in filtering (`WHERE`), joining (`JOIN`), or sorting (`ORDER BY`).
- *Primary candidates*: ID references, foreign keys, timestamps, and state columns.

### 1.3. Connection Pooling
Always use connection pools (e.g., `QueuePool` for standard relational databases, or custom pools for WebSockets) with configured thresholds to avoid connection overhead.
- **Rules**: Limit database pool sizes to avoid exhaustion under high concurrent load (e.g., set connection pools to max 20–50 connections with short timeouts).

---

## 2. API Design & Payload Optimization

### 2.1. Caching Strategy
Cache static or slow-changing configurations, analytical aggregations, and lists using an in-memory cache or Redis with a deterministic Time-to-Live (TTL).
```python
# Example: Cache zone lookup results for 30 seconds
@cache(ttl_seconds=30)
async def get_kpi_summary(): ...
```

### 2.2. Pagination
All list endpoints returning collections of dynamic length must enforce pagination.
- Always include `limit` and `offset` (or cursor-based tokens) parameters to prevent returning massive lists that choke network interfaces.

### 2.3. Response Compression (Gzip)
Compress any API response exceeding **1KB** in size using Gzip middleware. This reduces raw bytes sent over the wire and optimizes mobile/low-bandwidth client load speeds.

---

## 3. Asynchronous execution & Event Loops

### 3.1. Never Block the Event Loop
Ensure that no synchronous CPU-heavy code or blocking I/O (like Python's `time.sleep`, standard `requests`, or block-based file read/writes) executes in an asynchronous context.
- Use `asyncio.sleep()`, asynchronous clients (like `httpx.AsyncClient`), and async DB drivers.
- Delegate blocking operations to worker threads via executor pools (`run_in_executor`).

### 3.2. WebSocket Connection Management
Maintain a centralized, memory-efficient registry for tracking active WebSocket clients. Push updates only when state changes occur (event-driven) rather than utilizing aggressive polling loops.

---

## 4. Frontend Resource Efficiency

### 4.1. Code Splitting & Lazy Loading
Implement route-based and component-based code splitting to minimize the initial JS bundle size.
- Load heavyweight charts, modal structures, and complex sub-panels dynamically only when the user navigates to them.

### 4.2. Minimize Re-renders
Memoize complex UI elements (using `React.memo`, `useMemo`, and `useCallback` in React) to prevent redundant DOM updates. Avoid state allocations at the top-level app node.

### 4.3. Asset Optimization
Completely optimize static media assets:
- Compress all SVG images, use next-gen image formats (WebP/AVIF), and implement responsive image sets (`srcset`) to serve correct resolutions based on screen sizes.
