// Authentication Store using Zustand

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthState } from '../types/store';
import { authAPI, tokenUtils } from '../services/api';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: (tokens) => {
        const { access_token, refresh_token, user } = tokens;
        
        // Store tokens
        tokenUtils.setTokens(access_token, refresh_token);
        
        set({
          user,
          accessToken: access_token,
          refreshToken: refresh_token,
          isAuthenticated: true,
          error: null,
          isLoading: false,
        });
      },

      logout: async () => {
        const state = get();
        
        try {
          // Call logout API if authenticated
          if (state.isAuthenticated) {
            await authAPI.logout();
          }
        } catch (error) {
          console.error('Logout API call failed:', error);
        } finally {
          // Clear local state regardless of API call success
          tokenUtils.clearTokens();
          
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
            isLoading: false,
          });
        }
      },

      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      setError: (error) => {
        set({ error, isLoading: false });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper functions for auth operations
export const authOperations = {
  // Initialize auth state from localStorage
  initializeAuth: () => {
    const accessToken = tokenUtils.getAccessToken();
    const refreshToken = tokenUtils.getRefreshToken();
    
    if (accessToken && refreshToken && !tokenUtils.isTokenExpired(accessToken)) {
      // Token is valid, fetch user info
      authAPI.getCurrentUser()
        .then((user) => {
          useAuthStore.getState().login({
            access_token: accessToken,
            refresh_token: refreshToken,
            user
          });
        })
        .catch(() => {
          // Invalid token, clear auth
          useAuthStore.getState().logout();
        });
    } else if (accessToken && refreshToken && tokenUtils.isTokenExpired(accessToken)) {
      // Try to refresh token
      authAPI.refreshToken(refreshToken)
        .then((response) => {
          useAuthStore.getState().login(response);
        })
        .catch(() => {
          // Refresh failed, clear auth
          useAuthStore.getState().logout();
        });
    }
  },

  // Handle OAuth callback
  handleCallback: async (requestToken: string) => {
    const authStore = useAuthStore.getState();
    
    try {
      authStore.setLoading(true);
      authStore.clearError();
      
      const response = await authAPI.handleCallback(requestToken);
      authStore.login(response);
      
      return response;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Authentication failed';
      authStore.setError(errorMessage);
      throw error;
    } finally {
      authStore.setLoading(false);
    }
  },

  // Initiate login
  initiateLogin: async () => {
    const authStore = useAuthStore.getState();
    
    try {
      authStore.setLoading(true);
      authStore.clearError();
      
      const { login_url } = await authAPI.initiateLogin();
      
      // Redirect to Kite login
      window.location.href = login_url;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login initialization failed';
      authStore.setError(errorMessage);
      authStore.setLoading(false);
    }
  },
};