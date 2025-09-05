/**
 * Global Error Component for App Router
 * Handles errors gracefully with recovery options and detailed logging
 */

'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Wifi } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Application Error:', error);
    }
    
    // In production, this would send to error tracking service
    if (process.env.NODE_ENV === 'production' && typeof window !== 'undefined') {
      // Example: Sentry, LogRocket, etc.
      console.error('Production error:', {
        message: error.message,
        digest: error.digest,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      });
    }
  }, [error]);

  // Determine error type for better user messaging
  const getErrorInfo = () => {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return {
        title: 'Connection Error',
        description: 'Unable to connect to Baseball Trade AI services. Please check your internet connection.',
        icon: Wifi,
        color: 'text-orange-600',
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200',
        actionText: 'Retry Connection',
      };
    }
    
    if (message.includes('timeout')) {
      return {
        title: 'Request Timeout',
        description: 'The analysis is taking longer than expected. This might be due to heavy server load.',
        icon: AlertTriangle,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        actionText: 'Try Again',
      };
    }
    
    if (message.includes('not found') || message.includes('404')) {
      return {
        title: 'Resource Not Found',
        description: 'The requested data could not be found. It may have been moved or deleted.',
        icon: AlertTriangle,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
        actionText: 'Go Home',
      };
    }
    
    // Generic error
    return {
      title: 'Something Went Wrong',
      description: 'An unexpected error occurred while processing your request.',
      icon: Bug,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      actionText: 'Try Again',
    };
  };

  const errorInfo = getErrorInfo();
  const ErrorIcon = errorInfo.icon;

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-lg w-full">
        {/* Error Card */}
        <div className={`bg-white rounded-lg shadow-lg border-2 ${errorInfo.borderColor} p-8 text-center`}>
          {/* Icon */}
          <div className={`${errorInfo.bgColor} rounded-full p-4 w-20 h-20 mx-auto mb-6 flex items-center justify-center`}>
            <ErrorIcon className={`h-10 w-10 ${errorInfo.color}`} />
          </div>
          
          {/* Error Message */}
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {errorInfo.title}
          </h1>
          
          <p className="text-gray-600 mb-6 leading-relaxed">
            {errorInfo.description}
          </p>
          
          {/* Error Details (Development only) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="mb-6 text-left">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                Technical Details
              </summary>
              <div className="mt-3 p-4 bg-gray-100 rounded-lg text-xs font-mono text-gray-800 overflow-auto">
                <div className="space-y-2">
                  <div><strong>Error:</strong> {error.message}</div>
                  {error.digest && <div><strong>Digest:</strong> {error.digest}</div>}
                  {error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-words text-xs">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            </details>
          )}
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={reset}
              className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {errorInfo.actionText}
            </button>
            
            <button
              onClick={() => window.location.href = '/'}
              className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </button>
          </div>
          
          {/* Additional Help */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              If this problem persists, please check our{' '}
              <a 
                href="/status" 
                className="text-blue-600 hover:text-blue-500 font-medium"
                aria-label="System status page"
              >
                system status
              </a>{' '}
              or contact support.
            </p>
          </div>
        </div>

        {/* Additional Context for Baseball-specific errors */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-400">
            Baseball Trade AI v{process.env.VERSION || '1.0.0'} • 
            Built with Next.js {process.env.NEXT_RUNTIME ? ` (${process.env.NEXT_RUNTIME})` : ''}
          </p>
        </div>
      </div>
    </div>
  );
}