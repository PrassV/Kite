// Zustand Store Types

import type { User, StockQuote, ComprehensiveAnalysis } from './api';

// Auth Store
export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (tokens: { access_token: string; refresh_token: string; user: User }) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// Trading Store
export interface TradingState {
  selectedSymbol: string | null;
  watchlist: string[];
  quotes: Record<string, StockQuote>;
  analysis: Record<string, ComprehensiveAnalysis>;
  analysisLoading: Record<string, boolean>;
  
  // UI State
  activeTab: 'overview' | 'fibonacci' | 'patterns' | 'volume' | 'recommendations';
  
  // Actions
  setSelectedSymbol: (symbol: string | null) => void;
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;
  setQuote: (symbol: string, quote: StockQuote) => void;
  setAnalysis: (symbol: string, analysis: ComprehensiveAnalysis) => void;
  setAnalysisLoading: (symbol: string, loading: boolean) => void;
  setActiveTab: (tab: 'overview' | 'fibonacci' | 'patterns' | 'volume' | 'recommendations') => void;
  clearAnalysis: (symbol: string) => void;
}

// UI Store
export interface UIState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  notifications: Notification[];
  
  // Actions
  toggleTheme: () => void;
  toggleSidebar: () => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  timestamp: Date;
}