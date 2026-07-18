# ADR 004: Event-driven WebSocket push for telemetry

## Status
Accepted

## Context
Stadium crowd tracking changes dynamically by the second. Having clients pull status updates via REST polling introduces substantial network load, latency delays, and database traffic spikes.

## Decision
We implemented a WebSocket endpoint `/ws/telemetry` for live status broadcasts. The backend telemetry simulator runs as an asynchronous loop, updating zone densities and broadcasting delta states to all connected clients in real-time.

## Consequences
- **Positive**: Low network overhead, real-time client UI state changes, and instant stale detection on connection drops.
- **Negative**: Connection state must be tracked in server memory; requires support for persistent TCP connections on staging.
