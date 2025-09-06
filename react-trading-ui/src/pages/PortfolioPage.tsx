import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon as TrendingUpIcon, 
  ArrowTrendingDownIcon as TrendingDownIcon,
  EyeIcon,
  CurrencyRupeeIcon,
  CalendarDaysIcon
} from '@heroicons/react/24/outline';
import { stocksAPI } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';

interface Holding {
  tradingsymbol: string;
  exchange: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
  product: string;
  close_price: number;
  t1_quantity: number;
}

interface Position {
  tradingsymbol: string;
  exchange: string;
  quantity: number;
  average_price: number;
  last_price: number;
  pnl: number;
  product: string;
  buy_quantity: number;
  sell_quantity: number;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoadingHoldings, setIsLoadingHoldings] = useState(true);
  const [isLoadingPositions, setIsLoadingPositions] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      setIsLoadingHoldings(true);
      setIsLoadingPositions(true);
      
      const [holdingsResponse, positionsResponse] = await Promise.allSettled([
        stocksAPI.getPortfolio(),
        stocksAPI.getPositions()
      ]);

      if (holdingsResponse.status === 'fulfilled') {
        setHoldings(holdingsResponse.value || []);
      } else {
        console.error('Failed to load holdings:', holdingsResponse.reason);
      }

      if (positionsResponse.status === 'fulfilled') {
        setPositions(positionsResponse.value || []);
      } else {
        console.error('Failed to load positions:', positionsResponse.reason);
      }

    } catch (err) {
      setError('Failed to load portfolio data');
      console.error('Portfolio loading error:', err);
    } finally {
      setIsLoadingHoldings(false);
      setIsLoadingPositions(false);
    }
  };

  const calculateTotalPnL = () => {
    const holdingsPnL = holdings.reduce((sum, holding) => sum + (holding.pnl || 0), 0);
    const positionsPnL = positions.reduce((sum, position) => sum + (position.pnl || 0), 0);
    return holdingsPnL + positionsPnL;
  };

  const calculateTotalValue = () => {
    return holdings.reduce((sum, holding) => {
      return sum + (holding.quantity * holding.last_price);
    }, 0);
  };

  const totalPnL = calculateTotalPnL();
  const totalValue = calculateTotalValue();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Portfolio Overview</h1>
          <p className="text-gray-600">Track your investments and trading positions</p>
        </motion.div>

        {/* Summary Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
        >
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Value</p>
                <p className="text-2xl font-bold text-gray-900">
                  ₹{totalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <CurrencyRupeeIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total P&L</p>
                <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {totalPnL >= 0 ? '+' : ''}₹{Math.abs(totalPnL).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div className={`p-3 rounded-full ${totalPnL >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                {totalPnL >= 0 ? (
                  <TrendingUpIcon className="h-6 w-6 text-green-600" />
                ) : (
                  <TrendingDownIcon className="h-6 w-6 text-red-600" />
                )}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Stocks</p>
                <p className="text-2xl font-bold text-gray-900">{holdings.length + positions.length}</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <ChartBarIcon className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>
        </motion.div>

        {/* Holdings Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl shadow-sm border mb-8"
        >
          <div className="p-6 border-b">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Holdings</h2>
            <p className="text-gray-600">Long-term investment positions</p>
          </div>

          <div className="p-6">
            {isLoadingHoldings ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : holdings.length === 0 ? (
              <div className="text-center py-8">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No holdings found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-sm text-gray-600">
                      <th className="text-left py-3">Symbol</th>
                      <th className="text-right py-3">Quantity</th>
                      <th className="text-right py-3">Avg Price</th>
                      <th className="text-right py-3">LTP</th>
                      <th className="text-right py-3">P&L</th>
                      <th className="text-right py-3">Value</th>
                      <th className="text-center py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {holdings.map((holding, index) => {
                      const currentValue = holding.quantity * holding.last_price;
                      const investedValue = holding.quantity * holding.average_price;
                      const pnlPercent = ((currentValue - investedValue) / investedValue) * 100;

                      return (
                        <tr key={index} className="border-b hover:bg-gray-50">
                          <td className="py-4">
                            <div>
                              <p className="font-semibold text-gray-900">{holding.tradingsymbol}</p>
                              <p className="text-sm text-gray-500">{holding.exchange}</p>
                            </div>
                          </td>
                          <td className="text-right py-4 text-gray-900">{holding.quantity}</td>
                          <td className="text-right py-4 text-gray-900">₹{holding.average_price.toFixed(2)}</td>
                          <td className="text-right py-4 text-gray-900">₹{holding.last_price.toFixed(2)}</td>
                          <td className={`text-right py-4 ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {holding.pnl >= 0 ? '+' : ''}₹{Math.abs(holding.pnl).toFixed(2)}
                            <br />
                            <span className="text-sm">
                              ({pnlPercent > 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
                            </span>
                          </td>
                          <td className="text-right py-4 text-gray-900">
                            ₹{currentValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                          </td>
                          <td className="text-center py-4">
                            <button
                              onClick={() => window.open(`/analysis/${holding.tradingsymbol}`, '_blank')}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                              title="View Analysis"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </motion.div>

        {/* Positions Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl shadow-sm border"
        >
          <div className="p-6 border-b">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Positions</h2>
            <p className="text-gray-600">Active trading positions</p>
          </div>

          <div className="p-6">
            {isLoadingPositions ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : positions.length === 0 ? (
              <div className="text-center py-8">
                <CalendarDaysIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No active positions</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-sm text-gray-600">
                      <th className="text-left py-3">Symbol</th>
                      <th className="text-right py-3">Quantity</th>
                      <th className="text-right py-3">Avg Price</th>
                      <th className="text-right py-3">LTP</th>
                      <th className="text-right py-3">P&L</th>
                      <th className="text-center py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="py-4">
                          <div>
                            <p className="font-semibold text-gray-900">{position.tradingsymbol}</p>
                            <p className="text-sm text-gray-500">{position.exchange} • {position.product}</p>
                          </div>
                        </td>
                        <td className="text-right py-4 text-gray-900">{position.quantity}</td>
                        <td className="text-right py-4 text-gray-900">₹{position.average_price.toFixed(2)}</td>
                        <td className="text-right py-4 text-gray-900">₹{position.last_price.toFixed(2)}</td>
                        <td className={`text-right py-4 ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {position.pnl >= 0 ? '+' : ''}₹{Math.abs(position.pnl).toFixed(2)}
                        </td>
                        <td className="text-center py-4">
                          <button
                            onClick={() => window.open(`/analysis/${position.tradingsymbol}`, '_blank')}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                            title="View Analysis"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </motion.div>

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadPortfolioData}
              className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            >
              Retry
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}