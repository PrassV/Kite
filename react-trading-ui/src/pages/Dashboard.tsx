// Dashboard Page - Stock Selection Interface

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon,
  ClockIcon,
  BriefcaseIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { stocksAPI } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

const Dashboard: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();

  // Popular stocks for quick access
  const popularStocks = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 
    'ITC', 'SBIN', 'BAJFINANCE', 'BHARTIARTL', 'KOTAKBANK',
    'MARUTI', 'ASIANPAINT', 'LT', 'AXISBANK', 'TITAN'
  ];

  // Search stocks with debouncing
  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const results = await stocksAPI.searchStocks(query);
      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
      console.error('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300);
    
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const analyzeStock = (symbol: string) => {
    navigate(`/analysis/${symbol}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                <BriefcaseIcon className="inline h-8 w-8 mr-3 text-blue-600" />
                Trading Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Select stocks for comprehensive technical analysis
              </p>
            </div>
            
            <div className="text-right">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Market Status
              </div>
              <div className="text-lg font-semibold text-green-600">
                <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                Open
              </div>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search stocks (e.g., RELIANCE, TCS, HDFCBANK...)"
                className="w-full px-4 py-3 pl-12 rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-blue-500 focus:outline-none text-lg"
              />
              <div className="absolute left-4 top-1/2 transform -translate-y-1/2">
                {isSearching ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <MagnifyingGlassIcon className="h-6 w-6 text-gray-400" />
                )}
              </div>
            </div>
            
            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {searchResults.map((stock) => (
                  <button
                    key={stock.symbol}
                    onClick={() => {
                      setSearchQuery(stock.symbol);
                      setSearchResults([]);
                      analyzeStock(stock.symbol);
                    }}
                    className="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-200 dark:border-gray-700 last:border-b-0 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {stock.symbol}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {stock.name}
                        </div>
                      </div>
                      <div className="text-xs bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded">
                        {stock.exchange}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Portfolio Analysis */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Portfolio Analysis</h3>
                <p className="text-blue-100 text-sm">Analyze your current holdings</p>
              </div>
              <BriefcaseIcon className="h-8 w-8 text-blue-200" />
            </div>
            <button className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition-colors">
              Coming Soon
            </button>
          </div>
          
          {/* Market Scanner */}
          <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Market Scanner</h3>
                <p className="text-green-100 text-sm">Find trading opportunities</p>
              </div>
              <SparklesIcon className="h-8 w-8 text-green-200" />
            </div>
            <button className="bg-white text-green-600 px-4 py-2 rounded-lg font-semibold hover:bg-green-50 transition-colors">
              Coming Soon
            </button>
          </div>
          
          {/* Analysis History */}
          <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">Recent Analysis</h3>
                <p className="text-purple-100 text-sm">View past analysis results</p>
              </div>
              <ClockIcon className="h-8 w-8 text-purple-200" />
            </div>
            <button className="bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-purple-50 transition-colors">
              Coming Soon
            </button>
          </div>
        </div>

        {/* Popular Stocks */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <ChartBarIcon className="h-6 w-6 mr-2 text-blue-600" />
            Popular Stocks for Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Click on any stock to get comprehensive technical analysis with trading recommendations.
          </p>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {popularStocks.map((symbol) => (
            <div
              key={symbol}
              onClick={() => analyzeStock(symbol)}
              className="bg-white dark:bg-gray-800 rounded-lg border-2 border-gray-200 dark:border-gray-700 p-4 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="text-center">
                <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center group-hover:bg-blue-200 dark:group-hover:bg-blue-800 transition-colors">
                  <ChartBarIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  {symbol}
                </h3>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  NSE Equity
                </div>
                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm font-medium transition-colors">
                  Analyze Now
                </button>
              </div>
            </div>
          ))}
        </div>
        
        {/* Getting Started Tips */}
        <div className="mt-12 grid md:grid-cols-2 gap-8">
          {/* Tips */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-lg mb-4 text-blue-600 dark:text-blue-400 flex items-center">
              <SparklesIcon className="h-6 w-6 mr-2" />
              Pro Tips
            </h3>
            <ul className="space-y-3 text-gray-600 dark:text-gray-400">
              <li className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                Use the search function to quickly find any NSE/BSE equity
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                Analysis includes entry points, targets, and stop-losses
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                Volume analysis helps confirm pattern reliability
              </li>
              <li className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                Fibonacci levels provide key support and resistance zones
              </li>
            </ul>
          </div>
          
          {/* Analysis Features */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-lg mb-4 text-green-600 dark:text-green-400 flex items-center">
              <ChartBarIcon className="h-6 w-6 mr-2" />
              Analysis Features
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Fibonacci Retracements</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Volume Analysis</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Chart Patterns</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Trendline Detection</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Trading Recommendations</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;