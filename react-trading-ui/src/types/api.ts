// API Types for Trading Analysis Platform

export interface User {
  id: string;
  email: string;
  kite_user_id: string;
  created_at: string;
  last_login: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginRequest {
  redirect_url?: string;
}

export interface CallbackRequest {
  request_token: string;
}

// Stock Types
export interface Stock {
  symbol: string;
  name: string;
  exchange?: string;
  instrument_type?: string;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  exchange: string;
  instrument_type: string;
}

export interface StockQuote {
  symbol: string;
  name: string;
  last_price: number;
  change: number;
  change_percent: number;
  volume: number;
  open: number;
  high: number;
  low: number;
  close: number;
  timestamp: string;
}

// Analysis Types
export interface FibonacciLevel {
  level: number;
  price: number;
  ratio?: number;
  distance_percent: number;
  significance?: string;
}

export interface ChartPattern {
  pattern_id: string;
  pattern_name: string;
  pattern_type: string;
  status?: string;
  bias?: string;
  reliability_score: number;
  expected_direction: string;
  entry_price?: number;
  target_price?: number;
  stop_loss?: number;
  trading_setup?: {
    entry_trigger?: number;
    target_price?: number;
    stop_loss?: number;
    entry_strategy?: {
      trigger_price: number;
      target_price: number;
      stop_loss: number;
      confirmation_needed: string;
    };
  };
  volume_confirmation?: {
    pattern_volume_support: string;
  };
  timeline?: string;
  next_action?: string;
}

export interface VolumeProfile {
  total_volume?: number;
  average_daily_volume?: number;
  volume_weighted_average_price?: number;
  significant_volume_levels?: any[];
  current_volume?: number;
  average_volume_30d?: number;
  volume_assessment?: string;
  volume_significance?: string;
  volume_trend?: string;
  volume_ratio?: number;
  volume_ratio_to_average?: number;
  significance?: string;
}

export interface VolumeAnomaly {
  date: string;
  volume: number;
  z_score: number;
  anomaly_type: string;
  significance: string;
  price: number;
  volume_ratio: number;
}

export interface TrendAnalysis {
  direction: string;
  strength: string;
  bias?: string;
  duration_days?: number;
  key_levels?: any[];
  current_price?: number;
  sma_10?: number;
  sma_20?: number;
}

export interface TradingRecommendation {
  trading_bias: string;
  immediate_actions: Array<{
    action_type: string;
    priority: string;
    specific_action: string;
    trigger_price?: number;
    timeline: string;
    pattern_type?: string;
  }>;
  position_recommendations: {
    current_stance: string;
    position_sizing: string;
    hold_period: string;
  };
  fibonacci_key_levels: Array<{
    level_name: string;
    price: number;
    significance: string;
    distance_percent: number;
  }>;
}

export interface TradingOpportunity {
  type?: string;
  description?: string;
  entry_price?: number;
  target_price?: number;
  stop_loss?: number;
  risk_reward_ratio?: number;
  confidence_level?: number;
  reliability?: number;
  setup_type?: string;
  setup_description?: string;
  timeframe?: string;
}

export interface MathematicalAnalysisData {
  hurst_exponent?: number;
  fractal_dimension?: number;
  shannon_entropy?: number;
  lyapunov_exponent?: number;
  detrended_fluctuation_analysis?: number;
  mathematical_patterns?: any[];
  chaos_indicators?: any[];
  complexity_metrics?: any[];
}

export interface ComprehensiveAnalysis {
  analysis_summary: {
    stock_symbol: string;
    analysis_date: string;
    analysis_focus: string;
    current_price: number;
    analysis_window?: string;
    market_session?: string;
  };
  current_market_structure: {
    current_trend: TrendAnalysis;
    momentum: {
      "1_day": { direction: string; change: number; change_pct: number };
      "5_day": { direction: string; change: number; change_pct: number };
      "20_day": { direction: string; change: number; change_pct: number };
    };
    volatility: {
      current_volatility?: number;
      volatility_percentile?: number;
      volatility_assessment: string;
      current_volatility_annualized?: number;
    };
  };
  fibonacci_analysis: {
    current_fibonacci_analysis: {
      current_price: number;
      trend_direction: string;
      most_recent_swing_high: {
        price: number;
        date: string;
      };
      most_recent_swing_low: {
        price: number;
        date: string;
      };
    };
    fibonacci_retracements: {
      retracement_levels: FibonacciLevel[];
    };
    fibonacci_extensions: {
      extension_levels: FibonacciLevel[];
    };
    closest_levels: FibonacciLevel[];
    current_level_context: string;
  };
  active_patterns: ChartPattern[];
  volume_analysis: {
    volume_profile: VolumeProfile;
    volume_price_confirmation: {
      recent_confirmations: Array<{
        date: string;
        price_change_pct: number;
        volume_ratio: number;
        confirmation_status: string;
        significance: string;
      }>;
      confirmation_rate: string;
      overall_assessment: string;
    };
    recent_volume_anomalies: {
      spikes?: any[];
      analysis_summary?: string;
      volume_anomalies?: VolumeAnomaly[];
    };
  };
  immediate_trading_plan?: TradingRecommendation;
  risk_management?: {
    portfolio_risk?: number;
    position_sizing?: string;
    max_drawdown?: number;
    stop_loss_strategy?: string;
    stop_loss_levels?: {
      percentage_stops?: {
        conservative?: number;
        moderate?: number;
        tight?: number;
      };
    };
    risk_per_trade?: number;
    correlation_analysis?: any[];
  };
  forward_looking_forecast?: {
    forecast_summary?: {
      analysis_date: string;
      current_price: number;
      primary_bias: string;
      momentum_alignment: string;
      active_patterns_count: number;
      forecast_horizon: string;
    };
    scenarios?: Array<{
      scenario_name: string;
      probability: string;
      target_price: number;
      timeline: string;
      trigger_conditions: string;
      invalidation_level: number;
      description: string;
    }>;
  };
  trading_opportunities?: TradingOpportunity[];
  mathematical_analysis?: MathematicalAnalysisData;
  mathematical_indicators?: {
    hurst_exponent?: number;
    fractal_dimension?: number;
    shannon_entropy?: number;
    lyapunov_exponent?: number;
    detrended_fluctuation_analysis?: number;
    approximate_entropy?: number;
    correlation_dimension?: number;
    recurrence_quantification?: number;
    multifractal_spectrum?: any[];
    wavelet_analysis?: any[];
    fourier_analysis?: any[];
    chaos_game_representation?: any[];
    phase_space_reconstruction?: any[];
  };
}

// API Request/Response interfaces
export interface AnalysisRequest {
  symbol: string;
  analysis_type?: 'comprehensive' | 'quick';
  timeframe?: '1D' | '1W' | '1M';
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
  error_code?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Health Check
export interface HealthCheck {
  status: string;
  timestamp: string;
  version: string;
  database: boolean;
  redis: boolean;
  kite_api: boolean;
}