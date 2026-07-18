import React, { useState, useCallback } from 'react';
import { api } from './api';
import { AuthCtx } from './AuthCtx';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('arenaiq_token'));
  const [role, setRole]   = useState(() => localStorage.getItem('arenaiq_role'));
  const [user, setUser]   = useState(null);
  const [error, setError] = useState('');

  const login = useCallback(async (username, password) => {
    setError('');
    try {
      const data = await api.login(username, password);
      localStorage.setItem('arenaiq_token', data.access_token);
      localStorage.setItem('arenaiq_role', data.role);
      setToken(data.access_token);
      setRole(data.role);
      setUser({ username, role: data.role });
      return true;
    } catch (e) {
      setError(e.message || 'Login failed');
      return false;
    }
  }, []);

  const signup = useCallback(async (username, email, password, selectedRole) => {
    setError('');
    try {
      const data = await api.signup(username, email, password, selectedRole);
      localStorage.setItem('arenaiq_token', data.access_token);
      localStorage.setItem('arenaiq_role', data.role);
      setToken(data.access_token);
      setRole(data.role);
      setUser({ username, role: data.role });
      return true;
    } catch (e) {
      setError(e.message || 'Signup failed');
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('arenaiq_token');
    localStorage.removeItem('arenaiq_role');
    setToken(null);
    setRole(null);
    setUser(null);
  }, []);

  return (
    <AuthCtx.Provider value={{ token, role, user, error, login, signup, logout, setError }}>
      {children}
    </AuthCtx.Provider>
  );
}
