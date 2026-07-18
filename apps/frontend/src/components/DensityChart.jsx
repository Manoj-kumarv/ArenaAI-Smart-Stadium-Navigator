import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';

/**
 * @typedef {Object} TelemetryHistoryEntry
 * @property {string} zone_id
 * @property {number} density_pct
 * @property {string} color_state
 * @property {string} ts
 */

/**
 * DensityChart component to render real-time zone occupancy trends over time.
 *
 * @param {Object} props
 * @param {TelemetryHistoryEntry[]} props.history - List of telemetry history data.
 * @returns {React.ReactElement|null} The rendered LineChart.
 */
export default function DensityChart({ history }) {
  if (!history || history.length === 0) return null;
  const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#ef4444', '#a855f7'];
  const zoneIds = [...new Set(history.map(h => h.zone_id))].slice(0, 5);

  const byTime = {};
  history.forEach(h => {
    const t = new Date(h.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (!byTime[t]) byTime[t] = { t };
    byTime[t][h.zone_id] = Math.round(h.density_pct * 100);
  });
  const data = Object.values(byTime).slice(-30);

  return (
    <div className="chart-wrap" aria-label="Zone density trend chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
          <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
          <XAxis dataKey="t" tick={{ fill: '#4a5a78', fontSize: 9 }} interval="preserveStartEnd" />
          <YAxis domain={[0, 100]} tick={{ fill: '#4a5a78', fontSize: 9 }} unit="%" />
          <Tooltip
            contentStyle={{ background: '#131928', border: '1px solid #1e2d47', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: '#8a9bb8' }}
          />
          <Legend wrapperStyle={{ fontSize: 10, color: '#8a9bb8' }} />
          {zoneIds.map((id, i) => (
            <Line
              key={id}
              type="monotone"
              dataKey={id}
              stroke={COLORS[i % COLORS.length]}
              dot={false}
              strokeWidth={1.5}
              name={id.replace(/_/g, ' ')}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
