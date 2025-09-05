/**
 * React Query Provider with optimized configuration
 * Handles caching, background updates, and error boundaries
 */

'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { performanceMonitor, getErrorMessage } from '@/lib/optimized-api';

// Optimized Query Client configuration
function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Network mode configuration
        networkMode: 'online',
        
        // Retry configuration
        retry: (failureCount, error) => {
          // Don't retry on client errors (4xx)
          if (failureCount >= 3) return false;
          
          const errorStatus = (error as any)?.status;
          if (errorStatus >= 400 && errorStatus < 500 && errorStatus !== 429) {
            return false;
          }
          
          return true;
        },
        
        // Timing configuration
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 30 * 60 * 1000, // 30 minutes
        refetchOnMount: 'always',
        refetchOnWindowFocus: true,
        refetchOnReconnect: 'always',
        
        // Retry delay with exponential backoff
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        
        // Error handling
        throwOnError: false,
      },
      mutations: {
        // Mutation configuration
        retry: (failureCount, error) => {
          if (failureCount >= 2) return false;
          
          const errorStatus = (error as any)?.status;
          return errorStatus >= 500 || errorStatus === 429;
        },
        
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
        
        networkMode: 'online',
        throwOnError: false,
      },
    },
    
    // Global error handler
    logger: {
      log: console.log,
      warn: console.warn,
      error: (error) => {
        console.error('React Query Error:', error);
        
        // Track errors in performance monitor
        performanceMonitor.recordRequest('query_error', 0, true);
        
        // You can extend this to report to error tracking services
      },
    },
  });
}

interface QueryProviderProps {
  children: React.ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  // Create query client instance only once
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools 
          initialIsOpen={false}
          position="bottom-right"
          toggleButtonProps={{
            style: {
              marginLeft: '5px',
              transform: undefined,
              width: '30px',
              height: '30px',
            },
          }}
        />
      )}
    </QueryClientProvider>
  );
}

// Query client utilities for use outside of components
let globalQueryClient: QueryClient | null = null;

export function getQueryClient(): QueryClient {
  if (!globalQueryClient) {
    globalQueryClient = createQueryClient();
  }
  return globalQueryClient;
}

// Prefetch utilities for server-side rendering
export async function prefetchSystemHealth() {
  const queryClient = getQueryClient();
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.systemHealth(),
    queryFn: () => optimizedAPI.getSystemHealth(),
    staleTime: 30 * 1000,
  });
  
  return queryClient;
}

export async function prefetchTeamsData() {
  const queryClient = getQueryClient();
  
  await queryClient.prefetchQuery({
    queryKey: queryKeys.teams(),
    queryFn: () => optimizedAPI.getTeams(),
    staleTime: 10 * 60 * 1000,
  });
  
  return queryClient;
}