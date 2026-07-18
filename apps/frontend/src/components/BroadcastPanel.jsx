import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { useAuth } from '../hooks/useAuth';

/**
 * @typedef {Object} Incident
 * @property {number} id
 * @property {string} title
 * @property {string} description
 * @property {string} status
 */

/**
 * @typedef {Object} Broadcast
 * @property {number} id
 * @property {number} [incident_id]
 * @property {string} message_en
 * @property {string} message_es
 * @property {string} message_ar
 * @property {boolean} used_ai
 */

/**
 * BroadcastPanel component for generating atomic trilingual PA announcements.
 *
 * @param {Object} props
 * @param {Incident[]} props.incidents - List of active incidents.
 * @param {Broadcast[]} props.broadcasts - List of recent broadcasts.
 * @param {function(): void} props.onRefresh - Callback to refresh lists.
 * @param {string} props.selectedIncidentId - Currently selected incident ID.
 * @param {function(string): void} props.onSelectIncident - Selection callback.
 * @returns {React.ReactElement} The rendered BroadcastPanel.
 */
export default function BroadcastPanel({
  incidents,
  broadcasts,
  onRefresh,
  selectedIncidentId,
  onSelectIncident,
}) {
  const { token } = useAuth();
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [latest, setLatest] = useState(null);

  useEffect(() => {
    if (selectedIncidentId) {
      setSelected(selectedIncidentId);
    }
  }, [selectedIncidentId]);

  /**
   * Selection drop-down change handler.
   *
   * @param {React.ChangeEvent<HTMLSelectElement>} e
   */
  const handleSelectChange = (e) => {
    const val = e.target.value;
    setSelected(val);
    onSelectIncident(val);
  };

  /**
   * Action to call backend for trilingual PA broadcast generation.
   */
  const send = async () => {
    if (!selected) return;
    setErr('');
    setLoading(true);
    setLatest(null);
    try {
      const res = await api.createBroadcast(parseInt(selected), token);
      setLatest(res);
      onRefresh();
    } catch (e) {
      setErr(e.message || 'Broadcast failed');
    } finally {
      setLoading(false);
    }
  };

  const display = latest || (broadcasts && broadcasts[0]);

  return (
    <div>
      <div className="card-header">
        <h3 className="card-title">📢 PA Broadcast Generator</h3>
      </div>

      <div className="flex gap-1" style={{ marginBottom: '1rem', alignItems: 'flex-end' }}>
        <div style={{ flex: 1 }}>
          <label className="form-label" htmlFor="broadcast-incident-select">Incident</label>
          <select
            id="broadcast-incident-select"
            className="form-input form-select"
            value={selected}
            onChange={handleSelectChange}
          >
            <option value="">Select an incident…</option>
            {(incidents || []).filter(i => i.status !== 'resolved').map(i => (
              <option key={i.id} value={i.id}>{i.title}</option>
            ))}
          </select>
        </div>
        <button
          id="broadcast-send-btn"
          className="btn btn-primary"
          onClick={send}
          disabled={!selected || loading}
          aria-label="Generate PA broadcast in 3 languages"
        >
          {loading ? <span className="spinner" /> : '📡 Generate'}
        </button>
      </div>

      {err && <p className="form-error" role="alert">⚠ {err}</p>}

      {display && (
        <div className="fade-in" aria-live="polite" aria-label="Generated broadcast messages">
          <div className="broadcast-card">
            <div className="broadcast-lang">🇬🇧 English</div>
            <p className="broadcast-text" id="broadcast-en">{display.message_en}</p>
          </div>
          <div className="broadcast-card">
            <div className="broadcast-lang">🇪🇸 Español</div>
            <p className="broadcast-text" id="broadcast-es">{display.message_es}</p>
          </div>
          <div className="broadcast-card">
            <div className="broadcast-lang">🇸🇦 العربية</div>
            <p className="broadcast-text ar" dir="rtl" lang="ar" id="broadcast-ar">{display.message_ar}</p>
          </div>
          <p className="text-xs text-muted" style={{ marginTop: '.5rem' }}>
            {display.used_ai ? '✨ Generated with Gemini AI' : '📋 Rule-based fallback'}
          </p>
        </div>
      )}

      {(!display) && (
        <p className="text-sm text-muted">Select an incident above to generate a PA announcement in English, Spanish, and Arabic.</p>
      )}
    </div>
  );
}
