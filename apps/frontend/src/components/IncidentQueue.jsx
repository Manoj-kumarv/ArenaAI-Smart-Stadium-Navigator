import React, { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../hooks/useAuth';

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

/**
 * Renders a CSS-styled status badge for a given incident severity level.
 *
 * @param {string} sev - Incident severity ('low', 'medium', 'high', 'critical').
 * @returns {React.ReactElement} The badge element.
 */
function severityBadge(sev) {
  return <span className={`badge badge-${sev}`}>{sev}</span>;
}

/**
 * Modal displaying AI-driven resolution results and actions taken.
 *
 * @param {Object} props
 * @param {Object} props.result - The resolution result API response.
 * @param {function(): void} props.onClose - Modal close handler.
 * @returns {React.ReactElement|null} The modal overlay.
 */
function ResolutionModal({ result, onClose }) {
  if (!result) return null;
  const r = result.ai_result || {};
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal fade-in">
        <div className="flex justify-between items-center" style={{ marginBottom: '1rem' }}>
          <h2 id="modal-title" className="modal-title">🤖 AI Resolution Result</h2>
          <button className="btn-icon" onClick={onClose} aria-label="Close modal">✕</button>
        </div>

        <div className="resolution-section">
          <div className="resolution-label">Severity</div>
          {severityBadge(r.severity || 'medium')}
        </div>
        <div className="resolution-section">
          <div className="resolution-label">Confidence</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '.75rem' }}>
            <div className="confidence-bar" style={{ flex: 1 }}>
              <div className="confidence-fill" style={{ width: `${Math.round((r.confidence || 0) * 100)}%` }} />
            </div>
            <span className="text-sm text-muted">{Math.round((r.confidence || 0) * 100)}%</span>
          </div>
        </div>
        <div className="resolution-section">
          <div className="resolution-label">Root Cause</div>
          <p className="resolution-text">{r.cause || '—'}</p>
        </div>
        <div className="resolution-section">
          <div className="resolution-label">Resolution Playbook</div>
          <p className="resolution-playbook">{r.recommendation || '—'}</p>
        </div>
        <div className="resolution-section">
          <div className="resolution-label">AI Used</div>
          <span className={`badge ${r.used_ai ? 'badge-open' : 'badge-medium'}`}>
            {r.used_ai ? 'Gemini AI' : 'Rule-based Fallback'}
          </span>
        </div>
        <div style={{ marginTop: '1.25rem' }}>
          <button id="modal-close-btn" className="btn btn-secondary w-full" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

/**
 * IncidentQueue component rendering active/resolved incidents.
 *
 * @param {Object} props
 * @param {Array.<Object>} props.incidents - List of incidents to display.
 * @param {function(): void} props.onRefresh - Callback to refresh lists.
 * @param {function(Object): void} props.onBroadcast - Callback to initiate broadcast.
 * @returns {React.ReactElement} The incident queue container.
 */
export default function IncidentQueue({ incidents, onRefresh, onBroadcast }) {
  const { token, role } = useAuth();
  const [resolving, setResolving] = useState({});
  const [modalResult, setModalResult] = useState(null);
  const [err, setErr] = useState('');

  const isOps = role === 'ops_staff';

  const sorted = [...(incidents || [])].sort((a, b) => {
    const sa = SEV_ORDER[a.severity] ?? 9;
    const sb = SEV_ORDER[b.severity] ?? 9;
    if (sa !== sb) return sa - sb;
    return (b.ai_severity_score || 0) - (a.ai_severity_score || 0);
  });

  const handleResolve = async (inc) => {
    setErr('');
    setResolving(r => ({ ...r, [inc.id]: true }));
    try {
      const res = await api.resolveIncident(inc.id, token);
      setModalResult(res);
      onRefresh();
    } catch (e) {
      setErr(e.message || 'Resolution failed');
    } finally {
      setResolving(r => ({ ...r, [inc.id]: false }));
    }
  };

  return (
    <div>
      {err && <p className="form-error" role="alert" style={{ marginBottom: '.5rem' }}>⚠ {err}</p>}
      <div className="incident-list" aria-label="Incident queue" aria-live="polite">
        {sorted.length === 0 && (
          <p className="text-sm text-muted" style={{ padding: '.5rem 0' }}>No active incidents.</p>
        )}
        {sorted.map(inc => (
          <article
            key={inc.id}
            className={`incident-item ${inc.severity}`}
            aria-label={`Incident: ${inc.title}, severity ${inc.severity}, status ${inc.status}`}
          >
            <div className="incident-info">
              <div className="incident-title">{inc.title}</div>
              <div className="incident-meta">
                {severityBadge(inc.severity)}
                <span className={`badge badge-${inc.status}`}>{inc.status}</span>
                {inc.zone_id && <span>📍 {inc.zone_id.replace(/_/g, ' ')}</span>}
                {inc.ai_severity_score != null &&
                  <span>AI: {Math.round(inc.ai_severity_score * 100)}%</span>}
              </div>
            </div>
            {isOps && (
              <div className="incident-actions">
                {inc.status !== 'resolved' && (
                  <button
                    id={`resolve-btn-${inc.id}`}
                    className="btn btn-primary btn-sm"
                    onClick={() => handleResolve(inc)}
                    disabled={resolving[inc.id] || inc.status === 'in_progress'}
                    aria-label={`Resolve incident ${inc.title} with GenAI`}
                  >
                    {resolving[inc.id] ? <span className="spinner" /> : '🤖 Solve'}
                  </button>
                )}
                <button
                  id={`broadcast-btn-${inc.id}`}
                  className="btn btn-secondary btn-sm"
                  onClick={() => onBroadcast(inc)}
                  aria-label={`Broadcast PA announcement for incident ${inc.title}`}
                >📢</button>
              </div>
            )}
          </article>
        ))}
      </div>
      {modalResult && <ResolutionModal result={modalResult} onClose={() => setModalResult(null)} />}
    </div>
  );
}
