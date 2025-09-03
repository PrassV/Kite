// API Service for Trading Analysis Platform

import axios, { AxiosError } from 'axios';
import type { AxiosResponse } from 'axios';
import type { 
  AuthResponse, 
  StockSearchResult, 
  StockQuote, 
  ComprehensiveAnalysis,
  ApiError,
  HealthCheck
} from '../types/api';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://kite-tau.vercel.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  // Initiate login flow
  initiateLogin: async (): Promise<{ login_url: string }> => {
    const response = await api.post('/auth/login', {
      redirect_url: `${window.location.origin}/auth/callback`
    });
    return response.data;
  },

  // Handle OAuth callback
  handleCallback: async (requestToken: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/callback', {
      request_token: requestToken
    });
    return response.data;
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  // Refresh token
  refreshToken: async (refreshToken: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  },

  // Logout
  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  }
};

// Stocks API
export const stocksAPI = {
  // Search stocks
  searchStocks: async (query: string): Promise<StockSearchResult[]> => {
    const response = await api.get<StockSearchResult[]>(`/stocks/search`, {
      params: { query, limit: 10 }
    });
    return response.data;
  },

  // Get stock quote
  getQuote: async (symbol: string): Promise<StockQuote> => {
    const response = await api.get<StockQuote>(`/stocks/quote/${symbol}`);
    return response.data;
  },

  // Get multiple quotes
  getQuotes: async (symbols: string[]): Promise<StockQuote[]> => {
    const response = await api.get<StockQuote[]>('/stocks/quotes', {
      params: { symbols: symbols.join(',') }
    });
    return response.data;
  },

  // Get market status
  getMarketStatus: async () => {
    const response = await api.get('/stocks/market-status');
    return response.data;
  },

  // Get user watchlist
  getWatchlist: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/stocks/watchlist');
    return response.data;
  },

  // Add to watchlist
  addToWatchlist: async (symbol: string) => {
    const response = await api.post('/stocks/watchlist', { symbol });
    return response.data;
  },

  // Remove from watchlist
  removeFromWatchlist: async (symbol: string) => {
    const response = await api.delete(`/stocks/watchlist/${symbol}`);
    return response.data;
  }
};

// Analysis API
export const analysisAPI = {
  // Get comprehensive analysis
  getComprehensiveAnalysis: async (symbol: string): Promise<ComprehensiveAnalysis> => {
    const response = await api.post<ComprehensiveAnalysis>(`/analysis/${symbol}`, {
      analysis_type: 'comprehensive',
      timeframe: '1D'
    });
    return response.data;
  },

  // Get quick analysis
  getQuickAnalysis: async (symbol: string) => {
    const response = await api.get(`/analysis/${symbol}/quick`);
    return response.data;
  },

  // Get analysis history
  getAnalysisHistory: async (page: number = 1, size: number = 20) => {
    const response = await api.get('/analysis/history', {
      params: { page, size }
    });
    return response.data;
  },

  // Clear analysis cache
  clearAnalysisCache: async (symbol: string) => {
    const response = await api.delete(`/analysis/${symbol}/cache`);
    return response.data;
  }
};

// System API
export const systemAPI = {
  // Health check
  healthCheck: async (): Promise<HealthCheck> => {
    const response = await api.get<HealthCheck>('/health');
    return response.data;
  },

  // Public stats
  getPublicStats: async () => {
    const response = await api.get('/monitoring/public/stats');
    return response.data;
  }
};

// Export configured axios instance for custom requests
export default api;

// Error handling utility
export const handleApiError = (error: AxiosError<ApiError>): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.code === 'ECONNABORTED') {
    return 'Request timeout. Please try again.';
  }
  
  if (error.code === 'ERR_NETWORK') {
    return 'Network error. Please check your connection.';
  }
  
  return error.message || 'An unexpected error occurred';
};

// Token management utilities
export const tokenUtils = {
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  },

  getAccessToken: (): string | null => {
    return localStorage.getItem('accessToken');
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem('refreshToken');
  },

  clearTokens: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },

  isTokenExpired: (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }
};