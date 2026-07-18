import React from 'react';
import { colorClass, colorLabel } from '../utils/colorHelpers';

const FIELD_W = 800;
const FIELD_H = 540;

/**
 * @typedef {Object} Zone
 * @property {string} id - Unique identifier.
 * @property {string} name - Human readable name.
 * @property {number} density_pct - Density value between 0.0 and 1.0.
 * @property {string} color_state - 'green', 'yellow', 'red', 'critical'.
 * @property {boolean} is_step_free - Flag for step-free access.
 * @property {boolean} is_low_noise - Flag for low noise levels.
 * @property {number} x - X coordinate.
 * @property {number} y - Y coordinate.
 * @property {number} w - Width.
 * @property {number} h - Height.
 */

/**
 * SVG interactive group element for a single zone.
 *
 * @param {Object} props
 * @param {Zone} props.zone - Zone data.
 * @param {function(Zone): void} props.onClick - Click event handler.
 * @param {boolean} props.a11yMode - Whether accessibility highlighting is active.
 * @returns {React.ReactElement} The zone SVG representation.
 */
function ZoneRect({ zone, onClick, a11yMode }) {
  const cls = colorClass(zone.color_state);
  const isAccessible = zone.is_step_free || zone.is_low_noise;
  const a11yCls = a11yMode ? (isAccessible ? 'zone-accessible' : 'zone-inaccessible') : '';
  const pct = Math.round((zone.density_pct || 0) * 100);

  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={`${zone.name}, density ${pct}%, status ${colorLabel(zone.color_state)}${zone.is_step_free ? ', step-free access' : ''}${zone.is_low_noise ? ', low noise' : ''}`}
      onClick={() => onClick(zone)}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onClick(zone)}
      style={{ cursor: 'pointer' }}
    >
      <rect
        x={zone.x} y={zone.y} width={zone.w} height={zone.h}
        className={`zone-rect ${cls} ${a11yCls}`}
        rx="4" ry="4"
      />
      {/* Accessibility icons */}
      {zone.is_step_free && (
        <text x={zone.x + 2} y={zone.y + 8} fontSize="7" fill="#60a5fa" aria-hidden="true">♿</text>
      )}
      {zone.is_low_noise && (
        <text x={zone.x + (zone.is_step_free ? 10 : 2)} y={zone.y + 8} fontSize="7" fill="#a78bfa" aria-hidden="true">🔇</text>
      )}
      <text x={zone.x + zone.w / 2} y={zone.y + zone.h / 2 - 3}
        className="zone-label" textAnchor="middle" aria-hidden="true">
        {zone.name.length > 14 ? zone.name.slice(0, 13) + '…' : zone.name}
      </text>
      <text x={zone.x + zone.w / 2} y={zone.y + zone.h / 2 + 7}
        className="zone-density" textAnchor="middle" aria-hidden="true">
        {pct}%
      </text>
    </g>
  );
}

/**
 * StadiumMap rendering the SVG Digital Twin interface.
 *
 * @param {Object} props
 * @param {Zone[]} props.zones - List of zones.
 * @param {function(Zone): void} props.onZoneClick - Zone click callback.
 * @param {boolean} props.a11yMode - Accessibility highlighting mode flag.
 * @returns {React.ReactElement} The SVG container.
 */
export default function StadiumMap({ zones, onZoneClick, a11yMode }) {
  return (
    <svg
      viewBox={`0 0 ${FIELD_W} ${FIELD_H}`}
      className={`map-svg${a11yMode ? ' a11y-mode' : ''}`}
      role="img"
      aria-label="Stadium digital twin map showing zone occupancy levels"
    >
      {/* Pitch */}
      <rect x={175} y={145} width={450} height={250} fill="rgba(34,197,94,0.06)"
        stroke="rgba(34,197,94,0.18)" strokeWidth="1" rx="8" />
      <line x1={400} y1={145} x2={400} y2={395} stroke="rgba(34,197,94,0.12)" strokeWidth="1" />
      <circle cx={400} cy={270} r={40} fill="none" stroke="rgba(34,197,94,0.12)" strokeWidth="1" />
      <text x={400} y={274} textAnchor="middle" fontSize="11" fill="rgba(34,197,94,0.3)"
        fontFamily="Inter,sans-serif" fontWeight="600">PITCH</text>

      {/* Stadium ring background */}
      <rect x={60} y={60} width={680} height={420} fill="rgba(255,255,255,.02)"
        stroke="rgba(255,255,255,.05)" strokeWidth="1" rx="12" />

      {/* Zones */}
      {zones.map(zone => (
        <ZoneRect key={zone.id} zone={zone} onClick={onZoneClick} a11yMode={a11yMode} />
      ))}

      {/* Live regions for screen readers */}
      <title>Stadium Digital Twin — Live Zone Occupancy</title>
    </svg>
  );
}
