import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';

import { api } from '../api';
import { authStorage, authUrls } from '../api/client';

const AuthContext = createContext(null);

const safeJsonParse = (text) => {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (error) {
    return { ok: false, value: null, error };
  }
};

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(authStorage.getAccessToken());
  const [refreshToken, setRefreshToken] = useState(authStorage.getRefreshToken());
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('idle');
  const [authError, setAuthError] = useState('');

  const loadUser = useCallback(async () => {
    if (!accessToken) {
      setUser(null);
      return;
    }
    setStatus('loading');
    setAuthError('');
    try {
      const profile = await api.me();
      setUser(profile);
      setStatus('ready');
    } catch (error) {
      setUser(null);
      setStatus('error');
      setAuthError(error.message);
    }
  }, [accessToken]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const loginWithTokens = useCallback(
    async ({ access, refresh, user: userPayload }) => {
      if (!access || !refresh) {
        throw new Error('Both access and refresh tokens are required');
      }
      authStorage.setTokens({ access, refresh });
      setAccessToken(access);
      setRefreshToken(refresh);
      setAuthError('');
      if (userPayload) {
        setUser(userPayload);
        setStatus('ready');
      } else {
        try {
          setStatus('loading');
          const profile = await api.me();
          setUser(profile);
          setStatus('ready');
        } catch (error) {
          setUser(null);
          setStatus('error');
          setAuthError(error.message);
        }
      }
    },
    []
  );

  const loginWithCallbackPayload = useCallback(
    async (rawPayload) => {
      const parsed = safeJsonParse(rawPayload);
      if (!parsed.ok) {
        throw new Error('Invalid JSON payload');
      }
      await loginWithTokens(parsed.value);
    },
    [loginWithTokens]
  );

  const logout = useCallback(() => {
    authStorage.clearTokens();
    setAccessToken('');
    setRefreshToken('');
    setUser(null);
    setStatus('idle');
    setAuthError('');
  }, []);

  const value = useMemo(
    () => ({
      accessToken,
      refreshToken,
      user,
      status,
      authError,
      loginUrl: authUrls.login,
      callbackUrl: authUrls.callback,
      loginWithTokens,
      loginWithCallbackPayload,
      logout,
    }),
    [
      accessToken,
      refreshToken,
      user,
      status,
      authError,
      loginWithTokens,
      loginWithCallbackPayload,
      logout,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

AuthProvider.propTypes = {
  children: PropTypes.node,
};

export const useAuth = () => useContext(AuthContext);
