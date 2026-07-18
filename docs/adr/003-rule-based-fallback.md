# ADR 003: Deterministic Rule-Based Fallback logic

## Status
Accepted

## Context
Generative AI calls are prone to timeouts, query limits, schema structural shifts, and input injections. A system that crashes when an LLM fails is not production-ready.

## Decision
We implemented deterministic, rule-based fallback handlers for all 3 agents (Crowd, Fan, Incident) and the broadcast generator. If Gemini calls fail, timeout, or return malformed structures, the orchestrator automatically invokes matching fallback templates to construct valid responses.

## Consequences
- **Positive**: High resilience, 100% uptime, zero latency spikes, and predictable behavior during Gemini API outages.
- **Negative**: Reduced response flexibility and detail during fallback mode.
