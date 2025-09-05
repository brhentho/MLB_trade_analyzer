/**
 * Error Boundary Components
 * Provides graceful error handling and recovery options
 */

'use client';

import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

// Error fallback component
interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
  title?: string;
  showDetails?: boolean;
  showHomeLink?: boolean;
}

export function ErrorFallback({
  error,
  resetErrorBoundary,
  title = 'Something went wrong',
  showDetails = false,
  showHomeLink = true,
}: ErrorFallbackProps) {
  const isDevelopment = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg border border-red-200 p-6">
          {/* Error icon and title */}
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              <p className="text-sm text-gray-600">
                An unexpected error occurred while loading this section.
              </p>
            </div>
          </div>

          {/* Error message */}
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-700 font-medium">
                {error.message || 'An unknown error occurred'}
              </p>
            </div>
          </div>

          {/* Error details (development only or when requested) */}
          {(isDevelopment || showDetails) && (
            <details className="mb-6">
              <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                <Bug className="inline h-4 w-4 mr-1" />
                Error Details
              </summary>
              <div className="mt-2 p-3 bg-gray-100 rounded-md">
                <pre className="text-xs text-gray-600 whitespace-pre-wrap overflow-auto max-h-40">
                  {error.stack || error.toString()}
                </pre>
              </div>
            </details>
          )}

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={resetErrorBoundary}
              className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Try Again</span>
            </button>
            
            {showHomeLink && (
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                <Home className="h-4 w-4" />
                <span>Go Home</span>
              </button>
            )}
          </div>

          {/* Contact support link */}
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">
              If this problem persists, please contact support with error ID:
              <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                {Date.now().toString(36)}
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Compact error fallback for smaller components
export function CompactErrorFallback({
  error,
  resetErrorBoundary,
  title = 'Error',
}: Partial<ErrorFallbackProps>) {
  return (
    <div className="flex items-center justify-center p-4">
      <div className="text-center max-w-sm">
        <AlertTriangle className="h-6 w-6 text-red-500 mx-auto mb-2" />
        <h4 className="text-sm font-medium text-gray-900 mb-1">{title}</h4>
        <p className="text-xs text-gray-600 mb-3">
          {error?.message || 'Something went wrong'}
        </p>
        <button
          onClick={resetErrorBoundary}
          className="inline-flex items-center space-x-1 px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
          <span>Retry</span>
        </button>
      </div>
    </div>
  );
}

// Error logging function
function logError(error: Error, errorInfo: { componentStack: string }) {
  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Error Boundary caught an error:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  // In production, you would send this to an error reporting service
  // Example: Sentry, LogRocket, Bugsnag, etc.
  /*
  if (process.env.NODE_ENV === 'production') {
    // Send to error reporting service
    errorReportingService.captureException(error, {
      tags: { component: 'ErrorBoundary' },
      extra: errorInfo,
    });
  }
  */
}

// Main Error Boundary wrapper
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  title?: string;
  showDetails?: boolean;
  showHomeLink?: boolean;
  onError?: (error: Error, errorInfo: { componentStack: string }) => void;
}

export function ErrorBoundary({
  children,
  fallback: Fallback = ErrorFallback,
  title,
  showDetails,
  showHomeLink,
  onError,
}: ErrorBoundaryProps) {
  return (
    <ReactErrorBoundary
      FallbackComponent={(props) => (
        <Fallback
          {...props}
          title={title}
          showDetails={showDetails}
          showHomeLink={showHomeLink}
        />
      )}
      onError={(error, errorInfo) => {
        logError(error, errorInfo);
        onError?.(error, errorInfo);
      }}
      onReset={() => {
        // Clear any cached data that might be causing issues
        if (typeof window !== 'undefined') {
          window.location.reload();
        }
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
}

// Specific error boundaries for different sections
export function APIErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={CompactErrorFallback}
      title="API Error"
      showDetails={false}
      showHomeLink={false}
    >
      {children}
    </ErrorBoundary>
  );
}

export function ComponentErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      fallback={CompactErrorFallback}
      title="Component Error"
      showDetails={process.env.NODE_ENV === 'development'}
      showHomeLink={false}
    >
      {children}
    </ErrorBoundary>
  );
}

export function PageErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      title="Page Error"
      showDetails={process.env.NODE_ENV === 'development'}
      showHomeLink={true}
    >
      {children}
    </ErrorBoundary>
  );
}

// Hook for programmatic error handling
export function useErrorHandler() {
  return useCallback((error: Error) => {
    // Log the error
    console.error('Handled error:', error);
    
    // In production, report to error service
    if (process.env.NODE_ENV === 'production') {
      // errorReportingService.captureException(error);
    }
    
    // Could also show a toast notification
    // toast.error(error.message);
  }, []);
}