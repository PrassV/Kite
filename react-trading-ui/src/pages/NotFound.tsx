// 404 Not Found Page

import React from 'react';
import { Link } from 'react-router-dom';
import { ExclamationTriangleIcon, HomeIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../stores/authStore';

const NotFound: React.FC = () => {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full text-center">
        <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
        
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          404
        </h1>
        
        <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Page Not Found
        </h2>
        
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Sorry, we couldn't find the page you're looking for. 
          It might have been moved, deleted, or you entered the wrong URL.
        </p>
        
        <div className="space-y-4">
          <Link
            to={isAuthenticated ? '/dashboard' : '/'}
            className="inline-flex items-center justify-center w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {isAuthenticated ? (
              <>
                <ChartBarIcon className="h-5 w-5 mr-2" />
                Go to Dashboard
              </>
            ) : (
              <>
                <HomeIcon className="h-5 w-5 mr-2" />
                Go Home
              </>
            )}
          </Link>
          
          {isAuthenticated && (
            <Link
              to="/"
              className="inline-flex items-center justify-center w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors"
            >
              <HomeIcon className="h-5 w-5 mr-2" />
              Back to Home
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotFound;