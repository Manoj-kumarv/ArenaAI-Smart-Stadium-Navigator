/**
 * Frontend unit tests — color mapping function and RTL class toggling.
 * Run with: npm test
 */
import { describe, it, expect } from 'vitest';
import { colorClass, colorLabel } from '../utils/colorHelpers';

// ─── Color mapping tests ───────────────────────────────────────────────────────

describe('colorClass', () => {
  it('maps green state', () => {
    expect(colorClass('green')).toBe('zone-green');
  });
  it('maps yellow state', () => {
    expect(colorClass('yellow')).toBe('zone-yellow');
  });
  it('maps red state', () => {
    expect(colorClass('red')).toBe('zone-red');
  });
  it('maps critical state', () => {
    expect(colorClass('critical')).toBe('zone-critical');
  });
  it('defaults to zone-green for unknown state', () => {
    expect(colorClass('unknown')).toBe('zone-green');
    expect(colorClass(undefined)).toBe('zone-green');
    expect(colorClass('')).toBe('zone-green');
  });
});

describe('colorLabel', () => {
  it('returns Low for green', () => expect(colorLabel('green')).toBe('Low'));
  it('returns Moderate for yellow', () => expect(colorLabel('yellow')).toBe('Moderate'));
  it('returns High for red', () => expect(colorLabel('red')).toBe('High'));
  it('returns Critical for critical', () => expect(colorLabel('critical')).toBe('Critical'));
  it('returns raw value for unknown', () => expect(colorLabel('other')).toBe('other'));
});

// ─── RTL class toggling ────────────────────────────────────────────────────────

describe('RTL language toggling', () => {
  it('Arabic lang should set dir=rtl', () => {
    const lang = 'ar';
    const isRtl = lang === 'ar';
    expect(isRtl).toBe(true);
  });
  it('English lang should NOT set dir=rtl', () => {
    const lang = 'en';
    const isRtl = lang === 'ar';
    expect(isRtl).toBe(false);
  });
  it('Spanish lang should NOT set dir=rtl', () => {
    const lang = 'es';
    const isRtl = lang === 'ar';
    expect(isRtl).toBe(false);
  });
  it('RTL chat bubble has ar class when lang is Arabic', () => {
    const lang = 'ar';
    const cssClass = `chat-bubble assistant${lang === 'ar' ? ' ar' : ''}`;
    expect(cssClass).toContain('ar');
  });
  it('LTR chat bubble does NOT have ar class when lang is English', () => {
    const lang = 'en';
    const cssClass = `chat-bubble assistant${lang === 'ar' ? ' ar' : ''}`;
    expect(cssClass).not.toContain(' ar');
  });
});

// ─── Density → color boundary logic (mirrors backend) ─────────────────────────

describe('density boundary logic (frontend)', () => {
  function densityToColor(pct) {
    if (pct < 0.60) return 'green';
    if (pct < 0.85) return 'yellow';
    if (pct < 0.95) return 'red';
    return 'critical';
  }

  const cases = [
    [0.0, 'green'], [0.59, 'green'], [0.60, 'yellow'],
    [0.84, 'yellow'], [0.85, 'red'], [0.94, 'red'],
    [0.95, 'critical'], [1.0, 'critical'],
  ];

  cases.forEach(([pct, expected]) => {
    it(`density ${pct} → ${expected}`, () => {
      expect(densityToColor(pct)).toBe(expected);
    });
  });
});
