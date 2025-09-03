// Comprehensive Analysis Page

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  ArrowLeftIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  ExclamationTriangleIcon
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

  const goBack = () => {
    navigate('/dashboard');
  };

  const retryAnalysis = () => {
    refetch();
  };

  if (!symbol) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Invalid Stock Symbol</h2>
          <button onClick={goBack} className="mt-4 text-blue-600 hover:text-blue-700">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center py-16">
            <LoadingSpinner size="lg" />
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mt-6 mb-2">
              Analyzing {symbol}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Generating comprehensive technical analysis with Fibonacci, volume, and pattern detection...
            </p>
            <div className="mt-6 flex justify-center space-x-8 text-sm text-gray-500 dark:text-gray-400">
              <span className="animate-pulse">📈 Fibonacci Analysis</span>
              <span className="animate-pulse" style={{animationDelay: '0.5s'}}>📊 Volume Patterns</span>
              <span className="animate-pulse" style={{animationDelay: '1s'}}>🔍 Chart Patterns</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-2xl mx-auto text-center px-4">
          <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">Analysis Failed</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Unable to analyze {symbol}. This could be due to network issues or invalid stock symbol.
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

  if (!analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">No Analysis Data</h2>
          <button onClick={retryAnalysis} className="mt-4 text-blue-600 hover:text-blue-700">
            Try Again
          </button>
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

  const getTrendColor = (direction: string, bias?: string) => {
    const combined = `${direction} ${bias}`.toLowerCase();
    if (combined.includes('bullish') || combined.includes('up')) {
      return 'text-green-600 dark:text-green-400';
    } else if (combined.includes('bearish') || combined.includes('down')) {
      return 'text-red-600 dark:text-red-400';
    }
    return 'text-gray-600 dark:text-gray-400';
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'fibonacci', name: 'Fibonacci', icon: ArrowTrendingUpIcon },
    { id: 'patterns', name: 'Patterns', icon: ChartBarIcon },
    { id: 'volume', name: 'Volume', icon: ChartBarIcon },
    { id: 'recommendations', name: 'Recommendations', icon: ArrowTrendingUpIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Stock Header */}
      <section className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={goBack}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {symbol}
                </h1>
                <div className="text-gray-600 dark:text-gray-400">
                  {analysis.analysis_summary?.analysis_focus} • {analysis.analysis_summary?.analysis_date}
                </div>
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatCurrency(analysis.analysis_summary?.current_price)}
              </div>
              {analysis.current_market_structure?.momentum?.['1_day'] && (
                <div className={`text-sm flex items-center justify-end ${
                  analysis.current_market_structure.momentum['1_day'].direction === 'Positive' 
                    ? 'text-green-600' 
                    : 'text-red-600'
                }`}>
                  {getTrendIcon(analysis.current_market_structure.momentum['1_day'].direction)}
                  <span className="ml-1">
                    ₹{analysis.current_market_structure.momentum['1_day'].change} 
                    ({analysis.current_market_structure.momentum['1_day'].change_pct}%)
                  </span>
                </div>
              )}
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Last updated: {analysis.analysis_summary?.analysis_date}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trend Banner */}
      {analysis.current_market_structure?.current_trend && (
        <section className="py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className={`rounded-lg p-4 text-center text-white font-semibold ${
              analysis.current_market_structure.current_trend.bias === 'Bullish' 
                ? 'bg-green-500' 
                : analysis.current_market_structure.current_trend.bias === 'Bearish'
                ? 'bg-red-500'
                : 'bg-gray-500'
            }`}>
              <div className="flex items-center justify-center space-x-4">
                <span>
                  {analysis.current_market_structure.current_trend.bias} Trend 
                  ({analysis.current_market_structure.current_trend.strength})
                </span>
                <span>•</span>
                <span>Current: {formatCurrency(analysis.current_market_structure.current_trend.current_price)}</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Analysis Tabs */}
      <section className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-semibold text-sm whitespace-nowrap flex items-center ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <tab.icon className="h-4 w-4 mr-1" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </section>

      {/* Tab Content */}
      <div className="py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid lg:grid-cols-3 gap-8 mb-8">
              {/* Current Trend */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="font-semibold text-lg mb-4 text-blue-600 dark:text-blue-400 flex items-center">
                  <ArrowTrendingUpIcon className="h-5 w-5 mr-2" />
                  Current Trend
                </h3>
                {analysis.current_market_structure?.current_trend && (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Direction:</span>
                      <span className={`font-semibold ${getTrendColor(analysis.current_market_structure.current_trend.direction, analysis.current_market_structure.current_trend.bias)}`}>
                        {analysis.current_market_structure.current_trend.direction}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Strength:</span>
                      <span className="font-semibold">{analysis.current_market_structure.current_trend.strength}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">SMA 10:</span>
                      <span className="font-medium">{formatCurrency(analysis.current_market_structure.current_trend.sma_10)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">SMA 20:</span>
                      <span className="font-medium">{formatCurrency(analysis.current_market_structure.current_trend.sma_20)}</span>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Key Levels */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="font-semibold text-lg mb-4 text-green-600 dark:text-green-400 flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Key Levels
                </h3>
                {analysis.fibonacci_analysis?.closest_levels && (
                  <div className="space-y-3">
                    {analysis.fibonacci_analysis.closest_levels.slice(0, 4).map((level, index) => (
                      <div key={index} className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">{level.level}:</span>
                        <div className="text-right">
                          <div className="font-semibold">{formatCurrency(level.price)}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">{level.distance_percent}% away</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Volume Status */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="font-semibold text-lg mb-4 text-orange-600 dark:text-orange-400 flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Volume Status
                </h3>
                {analysis.volume_analysis?.volume_profile && (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Current Volume:</span>
                      <span className="font-semibold">
                        {analysis.volume_analysis.volume_profile.current_volume.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Assessment:</span>
                      <span className={`font-semibold ${
                        analysis.volume_analysis.volume_profile.volume_assessment === 'High' 
                          ? 'text-orange-600 dark:text-orange-400' 
                          : 'text-gray-600 dark:text-gray-400'
                      }`}>
                        {analysis.volume_analysis.volume_profile.volume_assessment}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">vs Average:</span>
                      <span className="font-medium">{analysis.volume_analysis.volume_profile.volume_ratio_to_average}x</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      {analysis.volume_analysis.volume_profile.volume_significance}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Other tabs would show placeholder content */}
          {activeTab !== 'overview' && (
            <div className="text-center py-16">
              <ChartBarIcon className="mx-auto h-16 w-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {tabs.find(t => t.id === activeTab)?.name} Analysis
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Detailed {activeTab} analysis will be displayed here.
              </p>
              <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                Coming in the next update with interactive charts and detailed insights.
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;