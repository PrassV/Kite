// Main App Component for Trading Analysis Platform

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Pages
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import AnalysisPage from './pages/AnalysisPage';
import PortfolioPage from './pages/PortfolioPage';
import AgentPage from './pages/AgentPage';
import AuthCallback from './pages/AuthCallback';
import NotFound from './pages/NotFound';

// Components
import { AuthGuard } from './components/AuthGuard';
import { Navbar } from './components/Navbar';
import { LoadingSpinner } from './components/LoadingSpinner';

// Stores
import { useAuthStore } from './stores/authStore';
import { authOperations } from './stores/authStore';

// Styles
import './App.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (previously cacheTime)
    },
    mutations: {
      retry: 1,
    },
  },
});

const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  // Initialize auth on app start
  useEffect(() => {
    authOperations.initializeAuth();
  }, []);

  // Show loading spinner during initial auth check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <LoadingSpinner size="lg" message="Initializing..." />
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          {/* Global Navigation */}
          <Navbar />
          
          {/* Main Content */}
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route 
                path="/" 
                element={
                  isAuthenticated ? <Navigate to="/dashboard" replace /> : <LandingPage />
                } 
              />
              
              {/* Auth Routes */}
              <Route path="/auth/callback" element={<AuthCallback />} />
              
              {/* Protected Routes */}
              <Route
                path="/dashboard"
                element={
                  <AuthGuard>
                    <Dashboard />
                  </AuthGuard>
                }
              />
              
              <Route
                path="/analysis/:symbol"
                element={
                  <AuthGuard>
                    <AnalysisPage />
                  </AuthGuard>
                }
              />
              
              <Route
                path="/portfolio"
                element={
                  <AuthGuard>
                    <PortfolioPage />
                  </AuthGuard>
                }
              />
              
              <Route
                path="/agent"
                element={
                  <AuthGuard>
                    <AgentPage />
                  </AuthGuard>
                }
              />
              
              {/* Fallback */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          
          {/* Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
                borderRadius: '8px',
                fontSize: '14px',
                maxWidth: '400px',
              },
              success: {
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
