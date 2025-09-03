// Landing Page for Trading Analysis Platform

import React from 'react';
import { motion } from 'framer-motion';
import { 
  ChartBarIcon, 
  BoltIcon, 
  CursorArrowRaysIcon,
  ShieldCheckIcon,
  ChartPieIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { authOperations } from '../stores/authStore';

const LandingPage: React.FC = () => {
  const handleLogin = () => {
    authOperations.initiateLogin();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-purple-800">
      {/* Hero Section */}
      <section className="relative pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              Professional Trading Analysis
              <span className="block text-yellow-300 mt-2">In Real-Time</span>
            </h1>
            <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-4xl mx-auto leading-relaxed">
              Get comprehensive technical analysis with Fibonacci retracements, volume patterns, 
              and chart pattern detection. Make informed trading decisions with actionable insights.
            </p>
          </motion.div>
          
          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center mb-12"
          >
            <button
              onClick={handleLogin}
              className="inline-flex items-center bg-yellow-400 text-gray-900 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-yellow-300 transition transform hover:scale-105 shadow-lg"
            >
              <ChartBarIcon className="h-6 w-6 mr-2" />
              Analyze My Portfolio Now
            </button>
            <button
              onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
              className="inline-flex items-center border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white hover:text-gray-900 transition"
            >
              <BoltIcon className="h-6 w-6 mr-2" />
              See How It Works
            </button>
          </motion.div>
          
          {/* Trust Indicators */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="flex items-center justify-center space-x-8 text-sm text-blue-200"
          >
            <div className="flex items-center">
              <ShieldCheckIcon className="h-5 w-5 mr-2" />
              Kite Connect Integrated
            </div>
            <div className="flex items-center">
              <BoltIcon className="h-5 w-5 mr-2" />
              Real-time Analysis
            </div>
            <div className="flex items-center">
              <ChartPieIcon className="h-5 w-5 mr-2" />
              Professional Grade
            </div>
          </motion.div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Successful Traders Choose Our Platform
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Stop guessing. Start trading with confidence using institutional-grade analysis tools.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="text-center p-6 rounded-xl bg-gray-50 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                <ChartBarIcon className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Comprehensive Analysis</h3>
              <p className="text-gray-600">
                Fibonacci retracements, volume analysis, trendlines, and chart patterns - all in one view.
              </p>
            </motion.div>
            
            {/* Feature 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-center p-6 rounded-xl bg-gray-50 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                <BoltIcon className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Real-time Intelligence</h3>
              <p className="text-gray-600">
                Live data from your Kite account. Current patterns, not historical analysis.
              </p>
            </motion.div>
            
            {/* Feature 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
              className="text-center p-6 rounded-xl bg-gray-50 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                <CursorArrowRaysIcon className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Actionable Recommendations</h3>
              <p className="text-gray-600">
                Specific entry points, targets, and stop-losses. No ambiguity, just clear action.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="features" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Get professional analysis in 3 simple steps</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Step 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="w-12 h-12 mx-auto mb-4 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                1
              </div>
              <h3 className="text-xl font-semibold mb-3">Connect Your Kite Account</h3>
              <p className="text-gray-600">
                Secure one-click authentication with your existing Kite Connect credentials.
              </p>
            </motion.div>
            
            {/* Step 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="w-12 h-12 mx-auto mb-4 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                2
              </div>
              <h3 className="text-xl font-semibold mb-3">Select Your Stocks</h3>
              <p className="text-gray-600">
                Choose from your portfolio or search for any NSE/BSE equity for analysis.
              </p>
            </motion.div>
            
            {/* Step 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="w-12 h-12 mx-auto mb-4 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                3
              </div>
              <h3 className="text-xl font-semibold mb-3">Get Instant Analysis</h3>
              <p className="text-gray-600">
                Comprehensive technical analysis with specific trading recommendations.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Deep Dive */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Content */}
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Professional-Grade Technical Analysis
              </h2>
              <div className="space-y-6">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5 }}
                  viewport={{ once: true }}
                  className="flex items-start space-x-4"
                >
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Forward-Looking Fibonacci Analysis</h3>
                    <p className="text-gray-600">Trend-aware retracements using recent swing points for current trading decisions.</p>
                  </div>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  viewport={{ once: true }}
                  className="flex items-start space-x-4"
                >
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Volume-Confirmed Patterns</h3>
                    <p className="text-gray-600">Chart patterns validated by volume analysis for higher probability setups.</p>
                  </div>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  viewport={{ once: true }}
                  className="flex items-start space-x-4"
                >
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Dynamic Trendlines</h3>
                    <p className="text-gray-600">Forward-projecting trendlines relevant for current market structure.</p>
                  </div>
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.3 }}
                  viewport={{ once: true }}
                  className="flex items-start space-x-4"
                >
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">Actionable Trading Setups</h3>
                    <p className="text-gray-600">Specific entry triggers, targets, and stop-losses with risk-reward ratios.</p>
                  </div>
                </motion.div>
              </div>
            </div>
            
            {/* Visual */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="bg-gray-100 rounded-xl p-8 text-center"
            >
              <ArrowTrendingUpIcon className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Live Market Data</h3>
              <p className="text-gray-600 mb-6">
                Real-time analysis using your Kite Connect data feed for the most current market insights.
              </p>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <div className="text-sm text-gray-500 mb-2">Sample Analysis Output</div>
                <div className="text-left space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Current Trend:</span>
                    <span className="text-green-600 font-semibold">Strong Uptrend</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Fibonacci 38.2%:</span>
                    <span className="font-semibold">₹2,816.40</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Volume Status:</span>
                    <span className="text-orange-600 font-semibold">High Activity</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pattern:</span>
                    <span className="text-blue-600 font-semibold">Ascending Triangle</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Trade with Confidence?
            </h2>
            <p className="text-xl mb-8 opacity-90">
              Join successful traders who use professional analysis tools to make informed decisions.
            </p>
            
            <button
              onClick={handleLogin}
              className="inline-flex items-center bg-yellow-400 text-gray-900 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-yellow-300 transition transform hover:scale-105 shadow-lg"
            >
              <ChartBarIcon className="h-6 w-6 mr-2" />
              Start Free Analysis
            </button>
            
            <div className="mt-6 text-sm opacity-75">
              <ShieldCheckIcon className="h-4 w-4 inline mr-1" />
              Secure authentication through Kite Connect • No data stored
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;