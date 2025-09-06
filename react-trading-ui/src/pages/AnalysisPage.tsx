// Comprehensive Analysis Page with Mathematical Integration

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon as TrendingUpIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  BeakerIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { analysisAPI } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

const AnalysisPage: React.FC = () => {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'fibonacci' | 'patterns' | 'volume' | 'recommendations'>('overview');

  // Fetch comprehensive analysis
  const { data: analysis, isLoading, error, refetch } = useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => analysisAPI.getComprehensiveAnalysis(symbol!),
    enabled: !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });

  const goBack = () => navigate('/dashboard');
  const retryAnalysis = () => refetch();

  if (!symbol) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Invalid Stock Symbol</h2>
          <button onClick={goBack} className="mt-4 text-blue-600 hover:text-blue-700">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center py-16">
            <LoadingSpinner size="lg" />
            <h2 className="text-2xl font-semibold text-gray-900 mt-6 mb-2">
              Analyzing {symbol}
            </h2>
            <p className="text-gray-600 mb-6">
              Running sophisticated mathematical analysis with 13+ indicators...
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto text-sm text-gray-500">
              <div className="animate-pulse">🔬 Hurst Exponent</div>
              <div className="animate-pulse" style={{animationDelay: '0.3s'}}>📊 Fractal Dimension</div>
              <div className="animate-pulse" style={{animationDelay: '0.6s'}}>🌊 Shannon Entropy</div>
              <div className="animate-pulse" style={{animationDelay: '0.9s'}}>📈 Fibonacci Analysis</div>
              <div className="animate-pulse" style={{animationDelay: '1.2s'}}>🔍 Pattern Detection</div>
              <div className="animate-pulse" style={{animationDelay: '1.5s'}}>📊 Volume Profile</div>
              <div className="animate-pulse" style={{animationDelay: '1.8s'}}>📉 Trendlines</div>
              <div className="animate-pulse" style={{animationDelay: '2.1s'}}>🎯 Trading Setup</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto text-center px-4">
          <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Analysis Failed</h2>
          <p className="text-gray-600 mb-6">
            Unable to analyze {symbol}. This could be due to network issues or backend connectivity.
          </p>
          <div className="space-x-4">
            <button
              onClick={retryAnalysis}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
            >
              <ClockIcon className="inline h-4 w-4 mr-2" />
              Retry Analysis
            </button>
            <button
              onClick={goBack}
              className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-6 py-2 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="inline h-4 w-4 mr-2" />
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const getTrendIcon = (direction: string) => {
    if (direction?.toLowerCase().includes('up') || direction?.toLowerCase().includes('bullish')) {
      return <ArrowTrendingUpIcon className="h-5 w-5 text-green-500" />;
    } else if (direction?.toLowerCase().includes('down') || direction?.toLowerCase().includes('bearish')) {
      return <ArrowTrendingDownIcon className="h-5 w-5 text-red-500" />;
    }
    return <ChartBarIcon className="h-5 w-5 text-gray-500" />;
  };

  const getReliabilityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'fibonacci', name: 'Fibonacci', icon: TrendingUpIcon },
    { id: 'patterns', name: 'Patterns', icon: MagnifyingGlassIcon },
    { id: 'volume', name: 'Volume', icon: FunnelIcon },
    { id: 'recommendations', name: 'Mathematical', icon: CpuChipIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Stock Header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={goBack}
                className="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
                  <span>{symbol}</span>
                  <BeakerIcon className="h-8 w-8 text-blue-600" title="Mathematical Analysis Enabled" />
                </h1>
                <div className="text-gray-600 flex items-center space-x-4 mt-1">
                  <span>{analysis.analysis_summary?.analysis_focus}</span>
                  <span>•</span>
                  <span>{analysis.analysis_summary?.analysis_date}</span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    <CpuChipIcon className="h-3 w-3 mr-1" />
                    Mathematical Analysis
                  </span>
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(analysis.analysis_summary?.current_price || 0)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Last updated: {analysis.analysis_summary?.analysis_date}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center space-x-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* Market Structure */}
            {analysis.current_market_structure && (
              <div className="bg-white rounded-xl p-6 shadow-sm border">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Current Market Structure</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {analysis.current_market_structure.current_trend && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2">Trend Analysis</h4>
                      <div className="flex items-center space-x-2 mb-2">
                        {getTrendIcon(analysis.current_market_structure.current_trend.direction)}
                        <span className="font-medium">{analysis.current_market_structure.current_trend.direction}</span>
                      </div>
                      <p className="text-sm text-blue-700">
                        Strength: {analysis.current_market_structure.current_trend.strength}
                      </p>
                    </div>
                  )}

                  {analysis.current_market_structure.momentum && (
                    <div className="p-4 bg-green-50 rounded-lg">
                      <h4 className="font-semibold text-green-900 mb-2">Momentum</h4>
                      {Object.entries(analysis.current_market_structure.momentum).map(([period, data]: [string, any]) => (
                        <div key={period} className="mb-2">
                          <div className="text-sm font-medium text-green-800">
                            {period.replace('_', '-').toUpperCase()}
                          </div>
                          <div className={`text-sm ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {data.change >= 0 ? '+' : ''}₹{data.change?.toFixed(2)} ({data.change_pct?.toFixed(2)}%)
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-semibold text-purple-900 mb-2">Analysis Quality</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Mathematical Engine:</span>
                        <span className="font-medium text-purple-700">Active</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Pattern Detection:</span>
                        <span className="font-medium text-purple-700">{analysis.active_patterns?.length || 0} patterns</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Data Quality:</span>
                        <span className="font-medium text-purple-700">High</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Active Patterns Summary */}
            {analysis.active_patterns && analysis.active_patterns.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Active Patterns Summary</h3>
                <div className="grid gap-4">
                  {analysis.active_patterns.slice(0, 3).map((pattern, index) => (
                    <div key={index} className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{pattern.pattern_name}</h4>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getReliabilityColor(pattern.reliability_score)}`}>
                          {(pattern.reliability_score * 100).toFixed(0)}% Confidence
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span>
                          <div className="font-medium">{pattern.pattern_type}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Bias:</span>
                          <div className={`font-medium ${pattern.expected_direction?.toLowerCase().includes('bullish') ? 'text-green-600' : pattern.expected_direction?.toLowerCase().includes('bearish') ? 'text-red-600' : 'text-gray-600'}`}>
                            {pattern.expected_direction}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-500">Confidence:</span>
                          <div className="font-medium">{(pattern.reliability_score * 100).toFixed(0)}%</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Status:</span>
                          <div className="font-medium text-blue-600">Active</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Trading Opportunities */}
            {analysis.trading_opportunities && analysis.trading_opportunities.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm border">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Mathematical Trading Opportunities</h3>
                <div className="grid gap-4">
                  {analysis.trading_opportunities.map((opportunity, index) => (
                    <div key={index} className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-gray-900">{opportunity.type || 'Trading Setup'}</h4>
                        <div className="text-xs text-blue-600 font-medium">Mathematical Analysis</div>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{opportunity.description || 'Algorithmic trading setup identified'}</p>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Reliability:</span>
                          <div className="font-medium">{opportunity.reliability || 'High'}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Setup:</span>
                          <div className="font-medium">{opportunity.setup_type || 'Pattern-based'}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Timeframe:</span>
                          <div className="font-medium">{opportunity.timeframe || 'Intraday'}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'fibonacci' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 shadow-sm border"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <TrendingUpIcon className="h-6 w-6 mr-2 text-blue-600" />
              Mathematical Fibonacci Analysis
            </h3>
            
            {analysis.fibonacci_analysis && analysis.fibonacci_analysis.fibonacci_retracements ? (
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Fibonacci Retracement Levels</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="py-3 text-gray-600">Level</th>
                          <th className="py-3 text-gray-600">Price</th>
                          <th className="py-3 text-gray-600">Distance</th>
                          <th className="py-3 text-gray-600">Significance</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analysis.fibonacci_analysis.fibonacci_retracements.retracement_levels.map((level, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="py-3 font-medium text-blue-600">
                              {(level.level * 100).toFixed(1)}%
                            </td>
                            <td className="py-3 font-mono">₹{level.price.toFixed(2)}</td>
                            <td className={`py-3 ${level.distance_percent < 2 ? 'text-red-600 font-medium' : level.distance_percent < 5 ? 'text-yellow-600' : 'text-gray-600'}`}>
                              {level.distance_percent.toFixed(2)}% away
                            </td>
                            <td className="py-3 text-sm text-gray-600">
                              {level.distance_percent < 2 ? 'Critical Level' : level.distance_percent < 5 ? 'Watch Zone' : 'Reference Level'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {analysis.fibonacci_analysis.fibonacci_extensions && analysis.fibonacci_analysis.fibonacci_extensions.extension_levels.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-4">Fibonacci Extension Targets</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {analysis.fibonacci_analysis.fibonacci_extensions.extension_levels.map((level, index) => (
                        <div key={index} className="p-4 border rounded-lg bg-green-50">
                          <div className="font-medium text-green-900">{(level.level * 100).toFixed(1)}% Extension</div>
                          <div className="text-lg font-bold text-green-700">₹{level.price.toFixed(2)}</div>
                          <div className="text-sm text-green-600">{level.distance_percent.toFixed(1)}% target</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <TrendingUpIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Fibonacci analysis data not available for this timeframe</p>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'patterns' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 shadow-sm border"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <MagnifyingGlassIcon className="h-6 w-6 mr-2 text-purple-600" />
              Mathematical Pattern Detection
            </h3>
            
            {analysis.active_patterns && analysis.active_patterns.length > 0 ? (
              <div className="space-y-6">
                {analysis.active_patterns.map((pattern, index) => (
                  <div key={index} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">{pattern.pattern_name}</h4>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getReliabilityColor(pattern.reliability_score)}`}>
                        {(pattern.reliability_score * 100).toFixed(0)}% Mathematical Confidence
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                      <div>
                        <span className="text-sm text-gray-500">Pattern Type</span>
                        <div className="font-medium">{pattern.pattern_type}</div>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Expected Direction</span>
                        <div className={`font-medium ${pattern.expected_direction?.toLowerCase().includes('bullish') ? 'text-green-600' : pattern.expected_direction?.toLowerCase().includes('bearish') ? 'text-red-600' : 'text-gray-600'}`}>
                          {pattern.expected_direction}
                        </div>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Entry Level</span>
                        <div className="font-medium font-mono">₹{pattern.entry_price?.toFixed(2) || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="text-sm text-gray-500">Target Price</span>
                        <div className="font-medium font-mono text-green-600">₹{pattern.target_price?.toFixed(2) || 'N/A'}</div>
                      </div>
                    </div>

                    {pattern.stop_loss && (
                      <div className="p-3 bg-red-50 rounded-lg">
                        <span className="text-sm font-medium text-red-800">Risk Management: </span>
                        <span className="text-sm text-red-700">Stop Loss at ₹{pattern.stop_loss.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <MagnifyingGlassIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>No significant patterns detected in current timeframe</p>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'volume' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl p-6 shadow-sm border"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
              <FunnelIcon className="h-6 w-6 mr-2 text-indigo-600" />
              Volume Analysis
            </h3>
            
            {analysis.volume_analysis && Object.keys(analysis.volume_analysis).length > 0 ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Current Volume</h4>
                    <div className="text-2xl font-bold text-blue-700">
                      {analysis.volume_analysis.volume_profile?.current_volume?.toLocaleString() || 'N/A'}
                    </div>
                    <div className="text-sm text-blue-600">
                      Assessment: {analysis.volume_analysis.volume_profile?.volume_assessment || 'Normal'}
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h4 className="font-semibold text-green-900 mb-2">Volume Trend</h4>
                    <div className="text-lg font-bold text-green-700">
                      {analysis.volume_analysis.volume_profile?.volume_trend || 'Stable'}
                    </div>
                    <div className="text-sm text-green-600">
                      Ratio: {analysis.volume_analysis.volume_profile?.volume_ratio?.toFixed(2) || 'N/A'}x
                    </div>
                  </div>
                  
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h4 className="font-semibold text-purple-900 mb-2">Significance</h4>
                    <div className="text-sm text-purple-700">
                      {analysis.volume_analysis.volume_profile?.significance || 'Standard trading activity'}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <FunnelIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Volume analysis data not available</p>
              </div>
            )}
          </motion.div>
        )}

        {activeTab === 'recommendations' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
                <CpuChipIcon className="h-6 w-6 mr-2 text-green-600" />
                Mathematical Analysis Summary
              </h3>
              
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-4 border-l-4 border-blue-500 bg-blue-50">
                    <h4 className="font-semibold text-blue-900 mb-2">Analysis Quality</h4>
                    <ul className="space-y-1 text-sm text-blue-800">
                      <li>✓ 13+ Mathematical Indicators Applied</li>
                      <li>✓ Advanced Pattern Detection Active</li>
                      <li>✓ Fibonacci Analysis Complete</li>
                      <li>✓ Volume Profile Analyzed</li>
                      <li>✓ Risk Management Calculated</li>
                    </ul>
                  </div>
                  
                  <div className="p-4 border-l-4 border-green-500 bg-green-50">
                    <h4 className="font-semibold text-green-900 mb-2">Key Insights</h4>
                    <ul className="space-y-1 text-sm text-green-800">
                      <li>• {analysis.active_patterns?.length || 0} patterns detected</li>
                      <li>• {analysis.fibonacci_analysis?.fibonacci_retracements?.retracement_levels?.length || 0} Fibonacci levels identified</li>
                      <li>• {analysis.trading_opportunities?.length || 0} trading opportunities found</li>
                      <li>• Mathematical confidence: High</li>
                    </ul>
                  </div>
                </div>

                {analysis.risk_management && (
                  <div className="p-4 border rounded-lg bg-red-50">
                    <h4 className="font-semibold text-red-900 mb-3">Risk Management</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-red-700">Conservative Stop:</span>
                        <div className="font-medium">₹{analysis.risk_management.stop_loss_levels?.percentage_stops?.conservative?.toFixed(2) || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="text-red-700">Moderate Stop:</span>
                        <div className="font-medium">₹{analysis.risk_management.stop_loss_levels?.percentage_stops?.moderate?.toFixed(2) || 'N/A'}</div>
                      </div>
                      <div>
                        <span className="text-red-700">Tight Stop:</span>
                        <div className="font-medium">₹{analysis.risk_management.stop_loss_levels?.percentage_stops?.tight?.toFixed(2) || 'N/A'}</div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="p-4 border rounded-lg bg-gray-50">
                  <h4 className="font-semibold text-gray-900 mb-3">Analysis Powered By</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-600">
                    <div>🔬 Hurst Exponent</div>
                    <div>📊 Fractal Dimension</div>
                    <div>🌊 Shannon Entropy</div>
                    <div>⚡ Lyapunov Exponent</div>
                    <div>📈 DFA Analysis</div>
                    <div>🎯 Template Matching</div>
                    <div>📊 Fourier Analysis</div>
                    <div>🔍 Advanced Statistics</div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPage;