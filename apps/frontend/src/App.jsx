import React, { useState, useEffect } from 'react';
import './index.css';
import { AuthProvider } from './AuthContext';
import { useAuth } from './hooks/useAuth';
import AuthPage from './AuthPage';
import CommandCenter from './components/CommandCenter';
import FanPortal from './components/FanPortal';
import { ErrorBoundary } from './components/ErrorBoundary';
import { api } from './api';

/**
 * Main application shell containing navigation and view routing.
 * Accessible to authenticated users only.
 * 
 * @returns {React.ReactElement} The rendered Shell component.
 */
function Shell() {
  const { token, role, logout } = useAuth();
  const [view, setView] = useState('map');
  const [zones, setZones] = useState([]);

  useEffect(() => {
    if (token) {
      api.getZones(token).then(setZones).catch(() => {});
    }
  }, [token]);

  if (!token) return <AuthPage />;

  const isOps = role === 'ops_staff';

  return (
    <div className="app-shell">
      {/* Skip link for keyboard users (must be first focusable element) */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Top navigation bar */}
      <header className="topbar" role="banner">
        <div className="topbar-brand">
          <div className="logo-icon" aria-hidden="true">🏟</div>
          <h1 style={{ margin: 0, fontSize: '1rem', display: 'inline-flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span style={{ fontWeight: 700 }}>ArenaIQ</span>
            <span className="brand-subtitle" style={{ fontSize: '.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>FIFA World Cup 2026</span>
          </h1>
        </div>

        <nav className="topbar-nav" role="navigation" aria-label="Main navigation">
          <button
            id="nav-map"
            className={`nav-btn${view === 'map' ? ' active' : ''}`}
            onClick={() => setView('map')}
            aria-current={view === 'map' ? 'page' : undefined}
          >
            <span aria-hidden="true">🗺</span> <span className="nav-btn-text">Operations</span>
          </button>
          <button
            id="nav-fan"
            className={`nav-btn${view === 'fan' ? ' active' : ''}`}
            onClick={() => setView('fan')}
            aria-current={view === 'fan' ? 'page' : undefined}
          >
            <span aria-hidden="true">⭐</span> <span className="nav-btn-text">Fan Portal</span>
          </button>
        </nav>

        <div className="topbar-right">
          <span className={`badge ${isOps ? 'badge-open' : 'badge-green'} role-badge`}>
            {isOps ? '🔐 Ops Staff' : '🎟 Fan'}
          </span>
          <button
            id="logout-btn"
            className="btn btn-secondary btn-sm"
            onClick={logout}
            aria-label="Sign out"
          >
            <span className="logout-text">Sign out</span>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="content" id="main-content" role="main">
        <div aria-live="polite" className="sr-only" aria-label="Page navigation">
          {view === 'map' ? 'Operations view' : 'Fan portal view'}
        </div>
        <ErrorBoundary>
          {view === 'map' ? <CommandCenter /> : <FanPortal zones={zones} />}
        </ErrorBoundary>
      </main>
    </div>
  );
}

/**
 * Root component of the application. Wraps the shell in AuthProvider.
 * 
 * @returns {React.ReactElement} The root app element.
 */
export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
