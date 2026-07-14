import React, { useState } from 'react';
import { useAuth } from './AuthContext';

export default function AuthPage() {
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', role: 'fan' });
  const [loading, setLoading] = useState(false);
  const { login, signup, error, setError } = useAuth();

  const set = (k) => (e) => { setForm(f => ({ ...f, [k]: e.target.value })); setError(''); };

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
    <div className="auth-shell" role="main">
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
          >Sign In</button>
          <button
            role="tab"
            aria-selected={tab === 'signup'}
            className={`auth-tab${tab === 'signup' ? ' active' : ''}`}
            onClick={() => { setTab('signup'); setError(''); }}
            id="tab-signup"
          >Sign Up</button>
        </div>

        <form onSubmit={submit} aria-labelledby={`tab-${tab}`}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input id="username" className="form-input" type="text" value={form.username}
              onChange={set('username')} required autoComplete="username" placeholder="ops_admin" />
          </div>

          {tab === 'signup' && (
            <div className="form-group">
              <label className="form-label" htmlFor="email">Email</label>
              <input id="email" className="form-input" type="email" value={form.email}
                onChange={set('email')} required autoComplete="email" placeholder="you@example.com" />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input id="password" className="form-input" type="password" value={form.password}
              onChange={set('password')} required autoComplete="current-password" placeholder="••••••••" />
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
  );
}
