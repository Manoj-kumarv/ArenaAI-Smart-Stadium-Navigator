import React, { useState, useEffect } from 'react';
import { api } from '../api';

/**
 * @typedef {Object} Zone
 * @property {string} id
 * @property {string} name
 * @property {number} capacity
 * @property {number} density_pct
 * @property {string} color_state
 */

/**
 * AIPanel component showing AI-driven crowd density analysis and quick actions.
 *
 * @param {Object} props
 * @param {Zone} props.zone - Selected zone object.
 * @param {function(): void} props.onClose - Close panel callback.
 * @param {string} props.token - JWT access token.
 * @returns {React.ReactElement} The rendered AIPanel.
 */
export default function AIPanel({ zone, onClose, token }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr('');
    setAnalysis(null);
    api.analyseZone(zone.id, token)
      .then(r => {
        if (!cancelled) {
          setAnalysis(r);
          setLoading(false);
        }
      })
      .catch(e => {
        if (!cancelled) {
          setErr(e.message);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [zone.id, token]);

  /**
   * Execute an operational action (broadcast, deploy volunteers, update signage) for the zone.
   *
   * @param {string} action
   */
  const doAction = async (action) => {
    setActionMsg('');
    try {
      await api.zoneAction(
        {
          zone_id: zone.id,
          action,
          detail: `Manual ${action} for ${zone.name}`,
        },
        token
      );
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
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
            <span className="spinner" aria-label="Analysing…" />
          </div>
        )}
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
              {actionMsg && (
                <p className="text-xs" style={{ color: actionMsg.startsWith('✓') ? 'var(--green)' : 'var(--red)' }}>
                  {actionMsg}
                </p>
              )}
              <button
                id={`action-broadcast-${zone.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => doAction('broadcast')}
              >
                📢 Broadcast
              </button>
              <button
                id={`action-volunteers-${zone.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => doAction('deploy_volunteers')}
              >
                🦺 Deploy Volunteers
              </button>
              <button
                id={`action-signage-${zone.id}`}
                className="btn btn-secondary btn-sm"
                onClick={() => doAction('update_signage')}
              >
                🪧 Update Signage
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
