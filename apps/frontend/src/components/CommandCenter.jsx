import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import StadiumMap, { colorClass } from './StadiumMap';
import KPIBar from './KPIBar';
import IncidentQueue from './IncidentQueue';
import BroadcastPanel from './BroadcastPanel';
import { api, WS_URL } from '../api';
import { useAuth } from '../AuthContext';

const STALE_THRESHOLD = 5000; // ms

// AI Panel shown when a zone is clicked
function AIPanel({ zone, onClose, token }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true); setErr(''); setAnalysis(null);
    api.analyseZone(zone.id, token)
      .then(r => { if (!cancelled) { setAnalysis(r); setLoading(false); } })
      .catch(e => { if (!cancelled) { setErr(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [zone.id, token]);

  const doAction = async (action) => {
    setActionMsg('');
    try {
      await api.zoneAction({ zone_id: zone.id, action, detail: `Manual ${action} for ${zone.name}` }, token);
      setActionMsg(`✓ '${action}' executed and logged`);
    } catch (e) {
      setActionMsg(`✗ ${e.message}`);
    }
  };

  return (
    <div className="ai-panel" role="complementary" aria-label={`AI analysis for ${zone.name}`}>
      <div className="ai-panel-header">
        <div>
          <div style={{ fontWeight: 700, fontSize: '.92rem' }}>{zone.name}</div>
          <span className={`badge badge-${zone.color_state}`} style={{ marginTop: '.25rem', display: 'inline-flex' }}>
            {Math.round((zone.density_pct || 0) * 100)}% · {zone.color_state}
          </span>
        </div>
        <button className="btn-icon" onClick={onClose} aria-label="Close AI panel">✕</button>
      </div>

      <div className="ai-panel-body">
        {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}><span className="spinner" aria-label="Analysing…" /></div>}
        {err && <p className="form-error">⚠ {err}</p>}

        {analysis && (
          <>
            <div>
              <div className="ai-label">Cause</div>
              <p className="ai-text">{analysis.cause}</p>
            </div>
            <div>
              <div className="ai-label">Recommendation</div>
              <p className="ai-text">{analysis.recommendation}</p>
            </div>
            <div>
              <div className="ai-label">Confidence</div>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${Math.round(analysis.confidence * 100)}%` }} />
              </div>
              <div className="text-xs text-muted" style={{ marginTop: '.25rem' }}>
                {Math.round(analysis.confidence * 100)}% · {analysis.used_ai ? '✨ Gemini AI' : '📋 Rule-based'}
              </div>
            </div>

            <div className="ai-actions">
              <div className="ai-label">Quick Actions</div>
              {actionMsg && <p className="text-xs" style={{ color: actionMsg.startsWith('✓') ? 'var(--green)' : 'var(--red)' }}>{actionMsg}</p>}
              <button id={`action-broadcast-${zone.id}`} className="btn btn-secondary btn-sm" onClick={() => doAction('broadcast')}>
                📢 Broadcast
              </button>
              <button id={`action-volunteers-${zone.id}`} className="btn btn-secondary btn-sm" onClick={() => doAction('deploy_volunteers')}>
                🦺 Deploy Volunteers
              </button>
              <button id={`action-signage-${zone.id}`} className="btn btn-secondary btn-sm" onClick={() => doAction('update_signage')}>
                🪧 Update Signage
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Mini density history chart
function DensityChart({ history }) {
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
            <Line key={id} type="monotone" dataKey={id} stroke={COLORS[i % COLORS.length]}
              dot={false} strokeWidth={1.5} name={id.replace(/_/g, ' ')} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function CommandCenter() {
  const { token, role } = useAuth();
  const [zones, setZones]           = useState([]);
  const [incidents, setIncidents]   = useState([]);
  const [broadcasts, setBroadcasts] = useState([]);
  const [kpi, setKpi]               = useState(null);
  const [a11yMode, setA11yMode]     = useState(false);
  const [selectedZone, setSelectedZone] = useState(null);
  const [wsStatus, setWsStatus]     = useState('disconnected');
  const [stale, setStale]           = useState(false);
  const [densityHistory, setDensityHistory] = useState([]);
  const wsRef = useRef(null);
  const lastTsRef = useRef(Date.now());
  const kpiRef = useRef(null);
  const isOps = role === 'ops_staff';

  // Fetch initial data
  const refresh = useCallback(async () => {
    try {
      const [z, kp] = await Promise.all([api.getZones(token), api.kpi()]);
      setZones(z);
      setKpi(kp);
    } catch {}
    if (isOps) {
      try {
        const inc = await api.getIncidents(token, { page_size: 50 });
        setIncidents(inc.items || []);
      } catch {}
      try {
        const bc = await api.getBroadcasts(token);
        setBroadcasts(bc || []);
      } catch {}
    }
  }, [token, isOps]);

  useEffect(() => { refresh(); }, [refresh]);

  // WebSocket telemetry
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen  = () => { setWsStatus('connected'); setStale(false); };
      ws.onclose = () => { setWsStatus('disconnected'); setTimeout(connect, 3000); };
      ws.onerror = () => ws.close();
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type !== 'telemetry') return;
        lastTsRef.current = Date.now();
        setStale(false);
        const updates = msg.data;
        setZones(prev => {
          const map = Object.fromEntries(prev.map(z => [z.id, z]));
          updates.forEach(u => {
            if (map[u.zone_id]) {
              map[u.zone_id] = { ...map[u.zone_id], density_pct: u.density_pct, color_state: u.color_state };
            }
          });
          return Object.values(map);
        });
        // Record history for chart
        const ts = new Date().toISOString();
        setDensityHistory(h => [...h.slice(-300), ...updates.map(u => ({ ...u, ts }))]);
        // Refresh KPI periodically
        api.kpi().then(setKpi).catch(() => {});
      };
    };
    connect();
    // Stale detection
    const staleTimer = setInterval(() => {
      if (Date.now() - lastTsRef.current > STALE_THRESHOLD) setStale(true);
    }, 1000);
    return () => { wsRef.current?.close(); clearInterval(staleTimer); };
  }, []);

  const handleBroadcastFor = (inc) => {
    // scroll to broadcast panel and pre-select
    document.getElementById('broadcast-incident-select')?.focus();
    const sel = document.getElementById('broadcast-incident-select');
    if (sel) { sel.value = String(inc.id); sel.dispatchEvent(new Event('change', { bubbles: true })); }
  };

  return (
    <div>
      <KPIBar kpi={kpi} liveRegionRef={kpiRef} />

      {stale && (
        <div className="stale-banner" role="alert" aria-live="assertive">
          ⚠ STALE DATA — Live telemetry feed interrupted. Last update &gt;5s ago.
        </div>
      )}

      <div className="cmd-layout">
        {/* Left — digital twin */}
        <div>
          <div className="map-container" style={{ marginBottom: '1rem' }}>
            <div className="map-controls">
              <span style={{ fontWeight: 600, fontSize: '.85rem' }}>🏟 Digital Twin</span>
              <div className="legend">
                <div className="legend-item"><span className="legend-dot green"/>Low</div>
                <div className="legend-item"><span className="legend-dot yellow"/>Moderate</div>
                <div className="legend-item"><span className="legend-dot red"/>High</div>
                <div className="legend-item"><span className="legend-dot critical"/>Critical</div>
              </div>
              <label className="toggle-wrap" htmlFor="a11y-toggle" style={{ marginLeft: 'auto' }}>
                <div
                  className={`toggle-track${a11yMode ? ' on' : ''}`}
                  role="switch"
                  aria-checked={a11yMode}
                  id="a11y-toggle"
                  tabIndex={0}
                  onClick={() => setA11yMode(v => !v)}
                  onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && setA11yMode(v => !v)}
                >
                  <div className="toggle-thumb" />
                </div>
                <span className="toggle-label">♿ Accessibility Layer</span>
              </label>
              <div className={`ws-indicator`} aria-label={`WebSocket: ${wsStatus}`}>
                <div className={`ws-dot ${wsStatus === 'connected' ? 'connected' : stale ? 'stale' : ''}`} />
                <span>{wsStatus === 'connected' ? 'Live' : 'Reconnecting…'}</span>
              </div>
            </div>
            <div style={{ position: 'relative' }}>
              <StadiumMap zones={zones} onZoneClick={setSelectedZone} a11yMode={a11yMode} />
              {selectedZone && (
                <AIPanel
                  zone={zones.find(z => z.id === selectedZone.id) || selectedZone}
                  onClose={() => setSelectedZone(null)}
                  token={token}
                />
              )}
            </div>
          </div>

          {/* Density chart */}
          <div className="card">
            <div className="card-header"><h3 className="card-title">📈 Zone Density Trend</h3></div>
            <DensityChart history={densityHistory} />
          </div>
        </div>

        {/* Right — incident queue + broadcast */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isOps && (
            <>
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">🚨 Incident Queue</h3>
                  <button className="btn btn-secondary btn-sm" onClick={refresh} aria-label="Refresh incidents">↻ Refresh</button>
                </div>
                <IncidentQueue incidents={incidents} onRefresh={refresh} onBroadcast={handleBroadcastFor} />
              </div>
              <div className="card">
                <BroadcastPanel incidents={incidents} broadcasts={broadcasts} onRefresh={refresh} />
              </div>
            </>
          )}
          {!isOps && (
            <div className="card">
              <p className="text-sm text-muted">Sign in as <strong>ops_staff</strong> to view and manage incidents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
