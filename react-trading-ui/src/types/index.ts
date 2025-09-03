// Base API Response
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

// Authentication Types
export interface User {
  user_id: string;
  email: string;
  broker: 'kite' | 'zerodha';
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  request_token: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Stock and Market Data Types
export interface Stock {
  symbol: string;
  name: string;
  exchange: string;
  instrument_token?: number;
  last_price?: number;
  change?: number;
  change_percent?: number;
}

export interface StockQuote {
  symbol: string;
  last_price: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
  change: number;
  change_percent: number;
}

export interface HistoricalData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Analysis Types
export interface FibonacciLevel {
  level: number;
  price: number;
  label: string;
}

export interface TechnicalPattern {
  pattern_type: string;
  confidence: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  description: string;
  formation_period: string;
}

export interface VolumeAnalysis {
  current_volume: number;
  average_volume: number;
  volume_ratio: number;
  volume_trend: 'increasing' | 'decreasing' | 'stable';
  significant_volume_events: Array<{
    date: string;
    volume: number;
    price_impact: number;
  }>;
}

export interface TradingRecommendation {
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  entry_price: number;
  stop_loss?: number;
  target_price?: number;
  risk_reward_ratio?: number;
  rationale: string;
}

export interface ComprehensiveAnalysis {
  symbol: string;
  current_price: number;
  analysis_timestamp: string;
  
  // Technical Analysis
  fibonacci_levels: FibonacciLevel[];
  patterns: TechnicalPattern[];
  volume_analysis: VolumeAnalysis;
  
  // Indicators
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  moving_averages: {
    sma_20: number;
    sma_50: number;
    ema_12: number;
    ema_26: number;
  };
  
  // Support and Resistance
  support_levels: number[];
  resistance_levels: number[];
  
  // Recommendations
  recommendation: TradingRecommendation;
  
  // Risk Assessment
  volatility: number;
  beta?: number;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  error: string | null;
  code?: string;
}

export interface UIState {
  loading: LoadingState;
  error: ErrorState;
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
}

// Chart Types
export interface ChartData {
  timestamp: string | number;
  value: number;
  volume?: number;
}

export interface ChartConfig {
  type: 'line' | 'candlestick' | 'area';
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
  indicators: string[];
}

// Portfolio Types
export interface Holding {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  price: number;
  side: 'buy' | 'sell';
  product: string;
  pnl: number;
}

export interface Portfolio {
  total_value: number;
  invested_value: number;
  current_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  holdings: Holding[];
  positions: Position[];
}

// Search and Filter Types
export interface SearchFilters {
  query: string;
  exchange?: string;
  sector?: string;
  price_range?: {
    min: number;
    max: number;
  };
}

export interface PaginationParams {
  page: number;
  limit: number;
  total?: number;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// API Request Types
export interface StockSearchRequest {
  query: string;
  limit?: number;
}

export interface AnalysisRequest {
  symbol: string;
  timeframe?: string;
  period?: number;
}

// Route Types
export type RouteParams = {
  symbol?: string;
  analysisId?: string;
};

// Form Types
export interface ContactForm {
  name: string;
  email: string;
  message: string;
}

// Environment Variables
export interface Config {
  apiUrl: string;
  kiteApiKey: string;
  environment: 'development' | 'production' | 'staging';
}