/**
 * Loading State Components
 * Provides consistent loading indicators and progress states
 */

'use client';

import { useState, useEffect } from 'react';
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

// Basic loading spinner
export function LoadingSpinner({
  size = 'default',
  className,
}: {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <Loader2 
      className={cn(
        'animate-spin',
        sizeClasses[size],
        className
      )} 
    />
  );
}

// Loading button
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  loadingText?: string;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'default' | 'lg';
}

export function LoadingButton({
  loading = false,
  loadingText = 'Loading...',
  variant = 'primary',
  size = 'default',
  children,
  className,
  disabled,
  ...props
}: LoadingButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    default: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };
  
  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={loading || disabled}
      {...props}
    >
      {loading && (
        <LoadingSpinner 
          size={size === 'lg' ? 'default' : 'sm'}
          className="mr-2" 
        />
      )}
      {loading ? loadingText : children}
    </button>
  );
}

// Progressive loading card
interface ProgressiveLoadingProps {
  isLoading: boolean;
  error?: Error | null;
  retry?: () => void;
  children: React.ReactNode;
  skeleton?: React.ReactNode;
  title?: string;
}

export function ProgressiveLoading({
  isLoading,
  error,
  retry,
  children,
  skeleton,
  title = 'Loading',
}: ProgressiveLoadingProps) {
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Data</h3>
          <p className="text-sm text-gray-600 mb-4">
            {error.message || 'An unexpected error occurred'}
          </p>
          {retry && (
            <button
              onClick={retry}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              <Loader2 className="h-4 w-4" />
              <span>Try Again</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return skeleton || (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
          <p className="text-sm text-gray-600">
            Please wait while we load the data...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Fade-in loading animation
interface FadeInLoadingProps {
  isLoading: boolean;
  children: React.ReactNode;
  duration?: number;
}

export function FadeInLoading({ 
  isLoading, 
  children, 
  duration = 300 
}: FadeInLoadingProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      const timer = setTimeout(() => setIsVisible(true), 50);
      return () => clearTimeout(timer);
    } else {
      setIsVisible(false);
    }
  }, [isLoading]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div 
      className={cn(
        'transition-opacity',
        isVisible ? 'opacity-100' : 'opacity-0'
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

// Step progress indicator
interface StepProgressProps {
  steps: Array<{
    id: string;
    name: string;
    description?: string;
    status: 'pending' | 'in_progress' | 'completed' | 'error';
  }>;
  orientation?: 'horizontal' | 'vertical';
}

export function StepProgress({ 
  steps, 
  orientation = 'vertical' 
}: StepProgressProps) {
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <LoadingSpinner size="sm" className="text-blue-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'in_progress':
        return 'border-blue-200 bg-blue-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (orientation === 'horizontal') {
    return (
      <div className="flex items-center space-x-4 overflow-x-auto pb-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center space-x-2">
            <div className={cn(
              'flex items-center space-x-2 px-3 py-2 rounded-lg border',
              getStepColor(step.status)
            )}>
              {getStepIcon(step.status)}
              <span className="text-sm font-medium whitespace-nowrap">
                {step.name}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className="h-px w-8 bg-gray-300" />
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {steps.map((step) => (
        <div
          key={step.id}
          className={cn(
            'p-4 rounded-lg border transition-all duration-300',
            getStepColor(step.status)
          )}
        >
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              {getStepIcon(step.status)}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gray-900">{step.name}</h4>
              {step.description && (
                <p className="text-sm text-gray-600 mt-1">{step.description}</p>
              )}
            </div>
            <div className="flex-shrink-0">
              {step.status === 'completed' && (
                <span className="text-xs font-medium text-green-600">✓ Done</span>
              )}
              {step.status === 'in_progress' && (
                <span className="text-xs font-medium text-blue-600">Working...</span>
              )}
              {step.status === 'error' && (
                <span className="text-xs font-medium text-red-600">Failed</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Floating loading indicator
export function FloatingLoader({
  message = 'Loading...',
  show = true,
}: {
  message?: string;
  show?: boolean;
}) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg p-6 mx-4 max-w-sm w-full">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-3" />
          <p className="text-gray-700 font-medium">{message}</p>
        </div>
      </div>
    </div>
  );
}

// Suspense-like loading boundary
interface LoadingBoundaryProps {
  children: React.ReactNode;
  isLoading: boolean;
  fallback?: React.ReactNode;
  error?: Error | null;
  retry?: () => void;
}

export function LoadingBoundary({
  children,
  isLoading,
  fallback,
  error,
  retry,
}: LoadingBoundaryProps) {
  if (error) {
    return (
      <div className="p-4 border border-red-200 rounded-lg bg-red-50">
        <div className="flex items-center space-x-2 mb-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="font-medium text-red-900">Error</span>
        </div>
        <p className="text-sm text-red-700 mb-3">{error.message}</p>
        {retry && (
          <button
            onClick={retry}
            className="text-sm text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  if (isLoading) {
    return fallback || (
      <div className="flex items-center justify-center p-8">
        <LoadingSpinner size="default" className="mr-3" />
        <span className="text-gray-600">Loading...</span>
      </div>
    );
  }

  return <>{children}</>;
}

// Intersection observer loading
export function LazyLoadingBoundary({
  children,
  onIntersect,
  loading = false,
  threshold = 0.1,
}: {
  children: React.ReactNode;
  onIntersect: () => void;
  loading?: boolean;
  threshold?: number;
}) {
  const [ref, inView] = useIntersectionObserver({
    threshold,
    triggerOnce: true,
  });

  useEffect(() => {
    if (inView && !loading) {
      onIntersect();
    }
  }, [inView, loading, onIntersect]);

  return (
    <div ref={ref}>
      {children}
      {loading && (
        <div className="flex justify-center p-4">
          <LoadingSpinner />
        </div>
      )}
    </div>
  );
}

// Simple intersection observer hook
function useIntersectionObserver({
  threshold = 0,
  root = null,
  rootMargin = '0%',
  triggerOnce = false,
}: {
  threshold?: number;
  root?: Element | null;
  rootMargin?: string;
  triggerOnce?: boolean;
}) {
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const [node, setNode] = useState<Element | null>(null);

  useEffect(() => {
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setEntry(entry);
        if (triggerOnce && entry.isIntersecting) {
          observer.disconnect();
        }
      },
      { threshold, root, rootMargin }
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, [node, threshold, root, rootMargin, triggerOnce]);

  return [setNode, entry?.isIntersecting ?? false] as const;
}