'use client';

import { useCallback, useEffect, useState } from 'react';
import { apiGet, apiPost } from '../lib/api';

/**
 * useAuth
 * - session-based auth (Django)
 * - uses centralized api client (credentials + CSRF handled automatically)
 * - endpoints:
 *   - GET  /api/auth/me/
 *   - POST /api/auth/login/
 *   - POST /api/auth/logout/
 */
export function useAuth() {
  const [user, setUser] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMe = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiGet('/api/auth/me/');
      setAuthenticated(!!data?.authenticated);
      setUser(data?.user || null);
      setError(null);
    } catch (err) {
      setAuthenticated(false);
      setUser(null);
      setError(err.message || 'Auth error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = async ({ username, password }) => {
    setError(null);
    try {
      await apiPost('/api/auth/login/', { username, password });
      await fetchMe();
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  const logout = async () => {
    setError(null);
    try {
      await apiPost('/api/auth/logout/');
      setAuthenticated(false);
      setUser(null);
    } catch (err) {
      setError(err.message || 'Logout failed');
      throw err;
    }
  };

  return {
    user,
    authenticated,
    loading,
    error,
    login,
    logout,
    refresh: fetchMe,
  };
}