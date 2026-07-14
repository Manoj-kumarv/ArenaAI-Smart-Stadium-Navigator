import React, { useState, useEffect } from 'react';
import './index.css';
import { AuthProvider, useAuth } from './AuthContext';
import AuthPage from './AuthPage';
import CommandCenter from './components/CommandCenter';
import FanPortal from './components/FanPortal';
import { api } from './api';

function Shell() {
  const { token, role, logout, user } = useAuth();
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
      {/* Top navigation bar */}
      <header className="topbar" role="banner">
        <div className="topbar-brand">
          <div className="logo-icon" aria-hidden="true">🏟</div>
          <span>ArenaIQ</span>
          <span style={{ fontSize: '.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>FIFA World Cup 2026</span>
        </div>

        <nav className="topbar-nav" role="navigation" aria-label="Main navigation">
          <button
            id="nav-map"
            className={`nav-btn${view === 'map' ? ' active' : ''}`}
            onClick={() => setView('map')}
            aria-current={view === 'map' ? 'page' : undefined}
          >
            🗺 Operations
          </button>
          <button
            id="nav-fan"
            className={`nav-btn${view === 'fan' ? ' active' : ''}`}
            onClick={() => setView('fan')}
            aria-current={view === 'fan' ? 'page' : undefined}
          >
            ⭐ Fan Portal
          </button>
        </nav>

        <div className="topbar-right">
          <span className={`badge ${isOps ? 'badge-open' : 'badge-green'}`}>
            {isOps ? '🔐 Ops Staff' : '🎟 Fan'}
          </span>
          <button
            id="logout-btn"
            className="btn btn-secondary btn-sm"
            onClick={logout}
            aria-label="Sign out"
          >Sign out</button>
        </div>
      </header>

      {/* Main content */}
      <main className="content" id="main-content" role="main">
        <div aria-live="polite" className="sr-only" aria-label="Page navigation">
          {view === 'map' ? 'Operations view' : 'Fan portal view'}
        </div>
        {view === 'map' ? <CommandCenter /> : <FanPortal zones={zones} />}
      </main>

      {/* Skip link for keyboard users */}
      <a
        href="#main-content"
        className="sr-only"
        style={{
          position: 'absolute', top: '-999px',
          ':focus': { top: '0' }
        }}
      >
        Skip to main content
      </a>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
