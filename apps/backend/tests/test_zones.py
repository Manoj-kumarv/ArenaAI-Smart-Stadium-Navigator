"""
Property tests for zone color thresholds and density cap.

Property 1 — color thresholds (parametrized boundary values)
Property 2 — density_pct > 1.0 is capped to 1.0
"""
from __future__ import annotations

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.models import ColorState, cap_density, density_to_color


# ─── Property 1: exact boundary checks ───────────────────────────────────────

@pytest.mark.parametrize("density,expected", [
    (0.0,   ColorState.green),
    (0.59,  ColorState.green),
    (0.599, ColorState.green),
    (0.60,  ColorState.yellow),   # boundary: 0.60 → yellow
    (0.60001, ColorState.yellow),
    (0.84,  ColorState.yellow),
    (0.849, ColorState.yellow),
    (0.85,  ColorState.red),      # boundary: 0.85 → red
    (0.851, ColorState.red),
    (0.94,  ColorState.red),
    (0.949, ColorState.red),
    (0.95,  ColorState.critical), # boundary: 0.95 → critical
    (0.951, ColorState.critical),
    (1.0,   ColorState.critical),
])
def test_zone_color_thresholds(density: float, expected: ColorState):
    assert density_to_color(density) == expected


# ─── Property 2: density cap ─────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected_val,expected_flag", [
    (0.5,  0.5,  False),
    (1.0,  1.0,  False),
    (1.001, 1.0, True),
    (1.5,  1.0,  True),
    (2.0,  1.0,  True),
    (0.0,  0.0,  False),
])
def test_density_cap(raw: float, expected_val: float, expected_flag: bool):
    val, flag = cap_density(raw)
    assert val == expected_val
    assert flag == expected_flag


# ─── Hypothesis: color is always a valid ColorState ──────────────────────────

@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@h_settings(max_examples=500)
def test_color_always_valid(density: float):
    result = density_to_color(density)
    assert result in ColorState.__members__.values()


# ─── Hypothesis: cap always returns [0, 1] ───────────────────────────────────

@given(st.floats(min_value=0.0, max_value=10.0, allow_nan=False))
@h_settings(max_examples=300)
def test_cap_always_in_range(raw: float):
    val, _ = cap_density(raw)
    assert 0.0 <= val <= 1.0
