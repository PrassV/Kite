// OAuth Callback Handler Page

import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { authOperations } from '../stores/authStore';
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { isLoading, error } = useAuthStore();
  
  useEffect(() => {
    const handleCallback = async () => {
      const requestToken = searchParams.get('request_token');
      const errorParam = searchParams.get('error');
      
      if (errorParam) {
        toast.error(`Authentication failed: ${errorParam}`);
        navigate('/', { replace: true });
        return;
      }
      
      if (!requestToken) {
        toast.error('No request token received from Kite');
        navigate('/', { replace: true });
        return;
      }
      
      try {
        await authOperations.handleCallback(requestToken);
        toast.success('Successfully authenticated!');
        navigate('/dashboard', { replace: true });
      } catch (error) {
        console.error('Callback error:', error);
        toast.error('Authentication failed. Please try again.');
        navigate('/', { replace: true });
      }
    };
    
    handleCallback();
  }, [searchParams, navigate]);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="max-w-md w-full mx-auto p-6">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
            {isLoading ? 'Processing Authentication...' : 'Authentication Complete'}
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {isLoading 
              ? 'Please wait while we verify your Kite credentials and set up your account.'
              : 'Redirecting to your dashboard...'
            }
          </p>
          
          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;