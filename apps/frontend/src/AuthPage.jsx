import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';

/**
 * AuthPage component representing the main landing and login page.
 * Provides split-screen layout with product presentation hero and glassmorphism auth card.
 *
 * @returns {React.ReactElement} The rendered AuthPage.
 */
export default function AuthPage() {
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'fan' });
  const [loading, setLoading] = useState(false);
  const { login, signup, error, setError } = useAuth();

  /**
   * Input change handler factory.
   *
   * @param {string} k - Key inside form state dictionary.
   */
  const set = (k) => (e) => {
    setForm(f => ({ ...f, [k]: e.target.value }));
    setError('');
  };

  /**
   * Form submission handler. Calls AuthContext authentication actions.
   *
   * @param {React.FormEvent} e
   */
  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    if (tab === 'login') {
      await login(form.username, form.password);
    } else {
      await signup(form.username, form.email, form.password, form.role);
    }
    setLoading(false);
  };

  return (
    <div className="auth-grid" role="main">
      {/* Left panel — Product Hero Content */}
      <div className="auth-hero-panel">
        <h2 className="auth-hero-title">
          Next-Gen Stadium Navigation for FIFA World Cup 2026
        </h2>
        <p className="auth-hero-subtitle">
          ArenaIQ delivers real-time crowd intelligence, automated incident resolution playbooks, and multilingual fan assistance for modern tournament operations.
        </p>

        <div className="auth-features-list">
          <div className="auth-feature-item">
            <div className="auth-feature-icon" aria-hidden="true">🗺️</div>
            <div className="auth-feature-text">
              <span className="auth-feature-title">Digital Twin Map</span>
              <span className="auth-feature-desc">Monitor live zone occupancy, density drifts, and visitor flows in real-time.</span>
            </div>
          </div>
          
          <div className="auth-feature-item">
            <div className="auth-feature-icon" aria-hidden="true">🤖</div>
            <div className="auth-feature-text">
              <span className="auth-feature-title">AI Incident Solver</span>
              <span className="auth-feature-desc">Generate root-cause analysis and automated playbooks using Gemini 1.5 Flash.</span>
            </div>
          </div>

          <div className="auth-feature-item">
            <div className="auth-feature-icon" aria-hidden="true">📢</div>
            <div className="auth-feature-text">
              <span className="auth-feature-title">Trilingual PA Announcements</span>
              <span className="auth-feature-desc">Publish atomic broadcasts instantly in English, Spanish, and Arabic.</span>
            </div>
          </div>
        </div>

        <div className="auth-stats-grid">
          <div className="auth-stat-card">
            <span className="auth-stat-val">25+</span>
            <span className="auth-stat-lbl">Live Zones</span>
          </div>
          <div className="auth-stat-card">
            <span className="auth-stat-val">99.9%</span>
            <span className="auth-stat-lbl">Uptime</span>
          </div>
          <div className="auth-stat-card">
            <span className="auth-stat-val">3</span>
            <span className="auth-stat-lbl">Languages</span>
          </div>
        </div>
      </div>

      {/* Right panel — Auth Card */}
      <div className="auth-form-panel">
        <div className="auth-card fade-in">
          <div className="auth-logo">
            <div className="logo-icon" aria-hidden="true">🏟</div>
            <span>ArenaIQ</span>
          </div>

          <div className="auth-tabs" role="tablist" aria-label="Login or sign up">
            <button
              role="tab"
              aria-selected={tab === 'login'}
              className={`auth-tab${tab === 'login' ? ' active' : ''}`}
              onClick={() => { setTab('login'); setError(''); }}
              id="tab-login"
            >
              Sign In
            </button>
            <button
              role="tab"
              aria-selected={tab === 'signup'}
              className={`auth-tab${tab === 'signup' ? ' active' : ''}`}
              onClick={() => { setTab('signup'); setError(''); }}
              id="tab-signup"
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={submit} aria-labelledby={`tab-${tab}`}>
            <div className="form-group">
              <label className="form-label" htmlFor="username">Username</label>
              <input
                id="username"
                className="form-input"
                type="text"
                value={form.username}
                onChange={set('username')}
                required
                autoComplete="username"
                placeholder="ops_admin"
              />
            </div>

            {tab === 'signup' && (
              <div className="form-group">
                <label className="form-label" htmlFor="email">Email</label>
                <input
                  id="email"
                  className="form-input"
                  type="email"
                  value={form.email}
                  onChange={set('email')}
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </div>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="password">Password</label>
              <input
                id="password"
                className="form-input"
                type="password"
                value={form.password}
                onChange={set('password')}
                required
                autoComplete="current-password"
                placeholder="••••••••"
              />
            </div>

            {tab === 'signup' && (
              <div className="form-group">
                <label className="form-label" htmlFor="role">Role</label>
                <select id="role" className="form-input form-select" value={form.role} onChange={set('role')}>
                  <option value="fan">Fan (read-only)</option>
                  <option value="ops_staff">Operations Staff (full access)</option>
                </select>
              </div>
            )}

            {error && <p className="form-error" role="alert" aria-live="polite">⚠ {error}</p>}

            <button id="submit-auth" className="btn btn-primary w-full" type="submit" disabled={loading}>
              {loading ? <span className="spinner" aria-label="Loading" /> : tab === 'login' ? 'Sign In' : 'Create Account'}
            </button>

            <p className="text-xs text-muted" style={{ marginTop: '1rem', textAlign: 'center' }}>
              Demo: <strong>ops_admin / OpsPass123!</strong> &nbsp;|&nbsp; <strong>fan_user / FanPass123!</strong>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
