/**
 * Global Error Boundary for App Router
 * Catches and handles errors that occur outside of page boundaries
 */

'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // Critical error logging
    console.error('Critical Application Error:', error);
    
    // In production, send to error monitoring service
    if (process.env.NODE_ENV === 'production' && typeof window !== 'undefined') {
      // This would integrate with your error tracking service
      const errorReport = {
        type: 'global_error',
        message: error.message,
        digest: error.digest,
        stack: error.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        severity: 'critical',
      };
      
      console.error('Critical error report:', errorReport);
      
      // Example: Send to monitoring service
      // errorTrackingService.captureException(error, { extra: errorReport });
    }
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
          <div className="max-w-md w-full text-center">
            {/* Critical Error Visual */}
            <div className="mb-8">
              <div className="w-24 h-24 mx-auto bg-red-100 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="h-12 w-12 text-red-600" />
              </div>
              <div className="text-4xl font-bold text-gray-900 mb-2">Oops!</div>
            </div>

            <h1 className="text-2xl font-semibold text-gray-900 mb-4">
              Critical Application Error
            </h1>
            
            <p className="text-gray-600 mb-8 leading-relaxed">
              Baseball Trade AI encountered a critical error and needs to restart. 
              Don't worry - your data is safe and this helps us improve the platform.
            </p>

            {/* Development Error Details */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mb-8 text-left bg-gray-100 rounded-lg p-4">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 mb-2">
                  Error Details (Development)
                </summary>
                <div className="text-xs font-mono text-gray-800 space-y-2">
                  <div><strong>Message:</strong> {error.message}</div>
                  {error.digest && <div><strong>Digest:</strong> {error.digest}</div>}
                  {error.stack && (
                    <div>
                      <strong>Stack:</strong>
                      <pre className="mt-1 whitespace-pre-wrap text-xs">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Recovery Actions */}
            <div className="space-y-3">
              <button
                onClick={reset}
                className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-base font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Restart Application
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                className="w-full inline-flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
              >
                <Home className="h-4 w-4 mr-2" />
                Return to Homepage
              </button>
            </div>

            {/* Support Information */}
            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-700">
                <strong>Need Help?</strong> If this error continues, please check our 
                system status or contact our support team with error ID: {error.digest || 'unknown'}
              </p>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}