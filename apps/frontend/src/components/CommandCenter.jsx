import React, { useState, useEffect, useCallback, useRef } from 'react';
import StadiumMap from './StadiumMap';
import KPIBar from './KPIBar';
import IncidentQueue from './IncidentQueue';
import BroadcastPanel from './BroadcastPanel';
import AIPanel from './AIPanel';
import DensityChart from './DensityChart';
import { api, WS_URL } from '../api';
import { useAuth } from '../hooks/useAuth';
import { STALE_THRESHOLD } from '../constants';

/**
 * CommandCenter dashboard component for ops_staff.
 * Displays live digital twin, real-time KPI metrics, incident queues, and PA broadcasts.
 *
 * @returns {React.ReactElement} The CommandCenter dashboard.
 */
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
  const [selectedBroadcastIncidentId, setSelectedBroadcastIncidentId] = useState('');
  const wsRef = useRef(null);
  const lastTsRef = useRef(Date.now());
  const kpiRef = useRef(null);
  const isOps = role === 'ops_staff';

  /**
   * Refreshes dashboard data.
   */
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

  useEffect(() => {
    refresh();
  }, [refresh]);

  // WebSocket telemetry connection handling
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      ws.onopen  = () => {
        setWsStatus('connected');
        setStale(false);
      };
      ws.onclose = () => {
        setWsStatus('disconnected');
        setTimeout(connect, 3000);
      };
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

    // Telemetry stale state detection
    const staleTimer = setInterval(() => {
      if (Date.now() - lastTsRef.current > STALE_THRESHOLD) setStale(true);
    }, 1000);

    return () => {
      wsRef.current?.close();
      clearInterval(staleTimer);
    };
  }, []);

  /**
   * Selection handler for triggering a PA broadcast from incident list.
   *
   * @param {Object} inc - Incident object.
   */
  const handleBroadcastFor = (inc) => {
    setSelectedBroadcastIncidentId(String(inc.id));
    const selectEl = document.getElementById('broadcast-incident-select');
    if (selectEl) {
      selectEl.scrollIntoView({ behavior: 'smooth' });
      selectEl.focus();
    }
  };

  return (
    <div>
      <KPIBar kpi={kpi} liveRegionRef={kpiRef} />

      {stale && (
        <div className="stale-banner" role="alert" aria-live="assertive">
          ⚠ STALE DATA — Live telemetry feed interrupted. Last update &gt;{STALE_THRESHOLD / 1000}s ago.
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
              <div className="ws-indicator" aria-label={`WebSocket: ${wsStatus}`}>
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
                <BroadcastPanel
                  incidents={incidents}
                  broadcasts={broadcasts}
                  onRefresh={refresh}
                  selectedIncidentId={selectedBroadcastIncidentId}
                  onSelectIncident={setSelectedBroadcastIncidentId}
                />
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
