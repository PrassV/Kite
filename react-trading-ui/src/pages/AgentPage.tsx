import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  PlayIcon,
  StopIcon,
  CpuChipIcon,
  ChartBarIcon,
  BeakerIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { LoadingSpinner } from '../components/LoadingSpinner';

interface AgentStatus {
  agent_available: boolean;
  status: string;
  started_at: string | null;
  last_analysis: string | null;
  analysis_count: number;
  error: string | null;
  mathematical_engine: string;
  features: string[];
}

interface AgentResults {
  status: string;
  results_count: number;
  analysis: Record<string, any>;
  last_updated: string;
  agent_status: string;
}

export default function AgentPage() {
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [agentResults, setAgentResults] = useState<AgentResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAgentStatus();
    // Poll status every 10 seconds
    const interval = setInterval(loadAgentStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadAgentStatus = async () => {
    try {
      const response = await fetch('/agent/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgentStatus(data);
        
        // If agent is running, also load results
        if (data.status === 'running' || data.status === 'completed') {
          loadAgentResults();
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to load agent status:', err);
      setError('Failed to connect to agent service');
    }
  };

  const loadAgentResults = async () => {
    if (isLoadingResults) return;
    
    setIsLoadingResults(true);
    try {
      const response = await fetch('/agent/results', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgentResults(data);
      }
    } catch (err) {
      console.error('Failed to load agent results:', err);
    } finally {
      setIsLoadingResults(false);
    }
  };

  const startAgent = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/agent/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        await response.json();
        setTimeout(() => {
          loadAgentStatus();
        }, 2000); // Give agent time to start
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start agent');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start agent');
    } finally {
      setIsLoading(false);
    }
  };

  const stopAgent = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/agent/stop', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setAgentResults(null);
        loadAgentStatus();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to stop agent');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop agent');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-50 border-green-200';
      case 'starting': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'stopping': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'completed': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <ArrowPathIcon className="h-5 w-5 animate-spin text-green-600" />;
      case 'completed': return <CheckCircleIcon className="h-5 w-5 text-purple-600" />;
      case 'error': return <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />;
      default: return <ClockIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  if (!agentStatus) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
            <CpuChipIcon className="h-8 w-8 mr-3 text-blue-600" />
            LivePositionalAgent
          </h1>
          <p className="text-gray-600">Advanced mathematical analysis of your portfolio holdings</p>
        </motion.div>

        {/* Agent Status Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-sm border mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900">Agent Status</h2>
            <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(agentStatus.status)}`}>
              <div className="flex items-center space-x-2">
                {getStatusIcon(agentStatus.status)}
                <span className="capitalize">{agentStatus.status}</span>
              </div>
            </div>
          </div>

          {!agentStatus.agent_available ? (
            <div className="text-center py-8">
              <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Agent Not Available</h3>
              <p className="text-gray-600 mb-4">Mathematical analysis components are not properly installed or configured.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{agentStatus.analysis_count}</div>
                  <div className="text-sm text-gray-600">Analyses Completed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {agentStatus.started_at ? '✓' : '○'}
                  </div>
                  <div className="text-sm text-gray-600">
                    {agentStatus.started_at ? 'Initialized' : 'Not Started'}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">13+</div>
                  <div className="text-sm text-gray-600">Math Indicators</div>
                </div>
              </div>

              <div className="flex justify-center space-x-4">
                {agentStatus.status === 'stopped' || agentStatus.status === 'completed' ? (
                  <button
                    onClick={startAgent}
                    disabled={isLoading}
                    className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
                  >
                    {isLoading ? (
                      <ArrowPathIcon className="h-5 w-5 animate-spin" />
                    ) : (
                      <PlayIcon className="h-5 w-5" />
                    )}
                    <span>Start Analysis</span>
                  </button>
                ) : agentStatus.status === 'running' ? (
                  <button
                    onClick={stopAgent}
                    disabled={isLoading}
                    className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
                  >
                    {isLoading ? (
                      <ArrowPathIcon className="h-5 w-5 animate-spin" />
                    ) : (
                      <StopIcon className="h-5 w-5" />
                    )}
                    <span>Stop Analysis</span>
                  </button>
                ) : null}

                <button
                  onClick={loadAgentResults}
                  disabled={isLoadingResults}
                  className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  {isLoadingResults ? (
                    <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  ) : (
                    <ChartBarIcon className="h-5 w-5" />
                  )}
                  <span>Refresh Results</span>
                </button>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600">{error}</p>
                </div>
              )}
            </>
          )}
        </motion.div>

        {/* Mathematical Engine Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl p-6 shadow-sm border mb-8"
        >
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <BeakerIcon className="h-6 w-6 mr-2 text-purple-600" />
            Mathematical Analysis Engine
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Advanced Indicators</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>Hurst Exponent - Trend persistence</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Fractal Dimension - Market complexity</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>Shannon Entropy - Information content</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span>Lyapunov Exponent - Chaos detection</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span>DFA - Long-range correlation</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Analysis Features</h3>
              <div className="space-y-2 text-sm text-gray-700">
                {agentStatus.features?.map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <CheckCircleIcon className="h-4 w-4 text-green-500" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Analysis Results */}
        {agentResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl p-6 shadow-sm border"
          >
            <h2 className="text-xl font-bold text-gray-900 mb-4">Analysis Results</h2>
            
            {agentResults.status === 'success' && agentResults.results_count > 0 ? (
              <div className="space-y-4">
                <div className="text-sm text-gray-600 mb-4">
                  Last updated: {new Date(agentResults.last_updated).toLocaleString()}
                </div>
                
                <div className="grid gap-4">
                  {Object.entries(agentResults.analysis).map(([symbol, data]: [string, any]) => (
                    <div key={symbol} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-gray-900">{symbol}</h3>
                        <div className="text-lg font-bold text-gray-900">
                          ₹{data.current_price?.toFixed(2) || 'N/A'}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Trend:</span>
                          <div className={`font-medium ${data.trend?.toLowerCase().includes('up') ? 'text-green-600' : data.trend?.toLowerCase().includes('down') ? 'text-red-600' : 'text-gray-600'}`}>
                            {data.trend || 'N/A'}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-500">Patterns:</span>
                          <div className="font-medium">{data.patterns_found || 0}</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Fibonacci:</span>
                          <div className="font-medium">{data.fibonacci_levels || 0} levels</div>
                        </div>
                        <div>
                          <span className="text-gray-500">Opportunities:</span>
                          <div className="font-medium">{data.trading_opportunities || 0}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>No analysis results available yet</p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </div>
  );
}