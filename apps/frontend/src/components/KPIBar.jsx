import React from 'react';

/**
 * @typedef {Object} KPIData
 * @property {number} attendance - Total number of occupants in the stadium.
 * @property {number} active_incidents - Count of open or in-progress incidents.
 * @property {number} avg_wait_minutes - Estimated average wait time in minutes.
 * @property {number} ai_actions_taken - Total count of logged AI actions/decisions.
 * @property {number} critical_zones - Count of zones with critical density.
 */

/**
 * KPIBar component rendering dynamic live status counters.
 * Marked with aria-live and role="status" for accessibility compliance.
 *
 * @param {Object} props
 * @param {KPIData} props.kpi - The KPI data metrics.
 * @param {React.RefObject} props.liveRegionRef - Ref object for dynamic screen reader announcements.
 * @returns {React.ReactElement|null} The rendered KPI bar container.
 */
export default function KPIBar({ kpi, liveRegionRef }) {
  if (!kpi) return null;
  return (
    <div
      className="kpi-bar"
      ref={liveRegionRef}
      aria-live="polite"
      aria-label="Live KPI summary"
    >
      <div className="kpi-card accent" role="status" aria-atomic="true">
        <div className="kpi-label">Attendance</div>
        <div className="kpi-value" id="kpi-attendance">{kpi.attendance?.toLocaleString() ?? '—'}</div>
        <div className="kpi-sub">fans in stadium</div>
      </div>
      <div className={`kpi-card${kpi.active_incidents > 3 ? ' danger' : kpi.active_incidents > 0 ? ' warning' : ' success'}`} role="status" aria-atomic="true">
        <div className="kpi-label">Active Incidents</div>
        <div className="kpi-value" id="kpi-incidents">{kpi.active_incidents ?? '—'}</div>
        <div className="kpi-sub">open + in progress</div>
      </div>
      <div className={`kpi-card${kpi.avg_wait_minutes > 10 ? ' danger' : kpi.avg_wait_minutes > 5 ? ' warning' : ' success'}`} role="status" aria-atomic="true">
        <div className="kpi-label">Avg Wait Time</div>
        <div className="kpi-value" id="kpi-wait">{kpi.avg_wait_minutes ?? '—'}<span style={{ fontSize: '.9rem', fontWeight: 400 }}>m</span></div>
        <div className="kpi-sub">estimated queue</div>
      </div>
      <div className="kpi-card accent" role="status" aria-atomic="true">
        <div className="kpi-label">AI Actions</div>
        <div className="kpi-value" id="kpi-ai-actions">{kpi.ai_actions_taken ?? '—'}</div>
        <div className="kpi-sub">decisions logged</div>
      </div>
      <div className={`kpi-card${kpi.critical_zones > 0 ? ' danger' : ' success'}`} role="status" aria-atomic="true">
        <div className="kpi-label">Critical Zones</div>
        <div className="kpi-value" id="kpi-critical">{kpi.critical_zones ?? '—'}</div>
        <div className="kpi-sub">≥95% capacity</div>
      </div>
    </div>
  );
}
