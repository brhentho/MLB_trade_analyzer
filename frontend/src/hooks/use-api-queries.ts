/**
 * React Query hooks for Baseball Trade AI
 * Provides optimized data fetching with caching, background updates, and error handling
 */

import { 
  useQuery, 
  useMutation, 
  useQueryClient,
  UseQueryOptions,
  UseMutationOptions,
  useInfiniteQuery,
} from '@tanstack/react-query';
import { useCallback, useRef } from 'react';

import { 
  optimizedAPI, 
  queryKeys, 
  type Team,
  type TradeRequest,
  type TradeAnalysis,
  type AnalysisProgress,
  type SystemHealth,
  getErrorMessage,
  isRetryableError,
} from '@/lib/optimized-api';

// Hook options with sensible defaults
const DEFAULT_QUERY_OPTIONS = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  retry: (failureCount: number, error: unknown) => {
    if (failureCount >= 3) return false;
    return isRetryableError(error);
  },
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
} as const;

// System health query
export function useSystemHealth(options?: Partial<UseQueryOptions<SystemHealth>>) {
  return useQuery({
    queryKey: queryKeys.systemHealth(),
    queryFn: () => optimizedAPI.getSystemHealth(),
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 30 * 1000, // 30 seconds - more frequent for health checks
    ...options,
  });
}

// Teams query
export function useTeams(options?: Partial<UseQueryOptions<{
  success: boolean;
  teams: Record<string, Team>;
  count: number;
  source: string;
}>>) {
  return useQuery({
    queryKey: queryKeys.teams(),
    queryFn: () => optimizedAPI.getTeams(),
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 10 * 60 * 1000, // 10 minutes - teams don't change often
    ...options,
  });
}

// Team roster query
export function useTeamRoster(
  teamKey: string,
  options?: Partial<UseQueryOptions<any>>
) {
  return useQuery({
    queryKey: queryKeys.teamRoster(teamKey),
    queryFn: () => optimizedAPI.getTeamRoster(teamKey),
    enabled: !!teamKey,
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 15 * 60 * 1000, // 15 minutes
    ...options,
  });
}

// Team needs query
export function useTeamNeeds(
  teamKey: string,
  options?: Partial<UseQueryOptions<any>>
) {
  return useQuery({
    queryKey: queryKeys.teamNeeds(teamKey),
    queryFn: () => optimizedAPI.getTeamNeeds(teamKey),
    enabled: !!teamKey,
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 20 * 60 * 1000, // 20 minutes
    ...options,
  });
}

// Analysis status query with automatic refetching for in-progress analyses
export function useAnalysisStatus(
  analysisId: string,
  options?: Partial<UseQueryOptions<TradeAnalysis>>
) {
  return useQuery({
    queryKey: queryKeys.analysisStatus(analysisId),
    queryFn: () => optimizedAPI.getAnalysisStatus(analysisId),
    enabled: !!analysisId && analysisId !== 'undefined',
    refetchInterval: (data) => {
      // Auto-refetch every 3 seconds for in-progress analyses
      if (data?.status === 'processing' || data?.status === 'analyzing') {
        return 3000;
      }
      return false;
    },
    refetchIntervalInBackground: true,
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 0, // Always fresh for analysis status
    ...options,
  });
}

// Analysis progress query with similar auto-refetching
export function useAnalysisProgress(
  analysisId: string,
  options?: Partial<UseQueryOptions<AnalysisProgress>>
) {
  return useQuery({
    queryKey: queryKeys.analysisProgress(analysisId),
    queryFn: () => optimizedAPI.getAnalysisProgress(analysisId),
    enabled: !!analysisId && analysisId !== 'undefined',
    refetchInterval: (data) => {
      // Auto-refetch every 2 seconds for active progress tracking
      if (data?.status !== 'completed' && data?.status !== 'error') {
        return 2000;
      }
      return false;
    },
    refetchIntervalInBackground: true,
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 0,
    ...options,
  });
}

// Player stats query
export function usePlayerStats(
  playerName: string,
  season: number = 2024,
  options?: Partial<UseQueryOptions<any>>
) {
  return useQuery({
    queryKey: queryKeys.playerStats(playerName, season),
    queryFn: () => optimizedAPI.getPlayerStats(playerName, season),
    enabled: !!playerName && playerName.length > 1,
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 60 * 60 * 1000, // 1 hour - stats don't change often
    ...options,
  });
}

// Cost monitoring query
export function useCostMonitoring(options?: Partial<UseQueryOptions<any>>) {
  return useQuery({
    queryKey: queryKeys.costMonitoring(),
    queryFn: () => optimizedAPI.getCostMonitoring(),
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Auto-refresh every minute
    ...options,
  });
}

// System status query
export function useSystemStatus(options?: Partial<UseQueryOptions<any>>) {
  return useQuery({
    queryKey: queryKeys.systemStatus(),
    queryFn: () => optimizedAPI.getSystemStatus(),
    ...DEFAULT_QUERY_OPTIONS,
    staleTime: 2 * 60 * 1000, // 2 minutes
    ...options,
  });
}

// Trade analysis mutation
export function useTradeAnalysisMutation(
  options?: UseMutationOptions<TradeAnalysis, Error, TradeRequest>
) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: TradeRequest) => optimizedAPI.analyzeTradeRequest(request),
    onSuccess: (data) => {
      // Cache the new analysis
      queryClient.setQueryData(queryKeys.analysisStatus(data.analysis_id), data);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ 
        queryKey: ['analysis'], 
        exact: false 
      });
    },
    onError: (error) => {
      console.error('Trade analysis failed:', getErrorMessage(error));
    },
    ...options,
  });
}

// Quick analysis mutation
export function useQuickAnalysisMutation(
  options?: UseMutationOptions<any, Error, { team: string; request: string }>
) {
  return useMutation({
    mutationFn: (request) => optimizedAPI.quickAnalysis(request),
    ...options,
  });
}

// Player search mutation
export function usePlayerSearchMutation(
  options?: UseMutationOptions<any, Error, Record<string, unknown>>
) {
  return useMutation({
    mutationFn: (criteria) => optimizedAPI.searchPlayers(criteria),
    ...options,
  });
}

// Connection test hook
export function useConnectionTest() {
  return useQuery({
    queryKey: ['connection', 'test'],
    queryFn: () => optimizedAPI.testConnection(),
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });
}

// Prefetch helpers
export function usePrefetchHooks() {
  const queryClient = useQueryClient();

  const prefetchTeams = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.teams(),
      queryFn: () => optimizedAPI.getTeams(),
      staleTime: 10 * 60 * 1000,
    });
  }, [queryClient]);

  const prefetchSystemHealth = useCallback(() => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.systemHealth(),
      queryFn: () => optimizedAPI.getSystemHealth(),
      staleTime: 30 * 1000,
    });
  }, [queryClient]);

  const prefetchTeamData = useCallback((teamKey: string) => {
    if (!teamKey) return;
    
    // Prefetch both roster and needs
    queryClient.prefetchQuery({
      queryKey: queryKeys.teamRoster(teamKey),
      queryFn: () => optimizedAPI.getTeamRoster(teamKey),
      staleTime: 15 * 60 * 1000,
    });
    
    queryClient.prefetchQuery({
      queryKey: queryKeys.teamNeeds(teamKey),
      queryFn: () => optimizedAPI.getTeamNeeds(teamKey),
      staleTime: 20 * 60 * 1000,
    });
  }, [queryClient]);

  return {
    prefetchTeams,
    prefetchSystemHealth,
    prefetchTeamData,
  };
}

// Optimized polling hook for analysis progress
export function useAnalysisPolling(analysisId: string, enabled: boolean = true) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const analysisQuery = useAnalysisStatus(analysisId, {
    enabled: enabled && !!analysisId,
  });
  
  const progressQuery = useAnalysisProgress(analysisId, {
    enabled: enabled && !!analysisId,
  });

  // Stop polling when analysis is complete
  const shouldPoll = enabled && 
    analysisQuery.data?.status !== 'completed' && 
    analysisQuery.data?.status !== 'error';

  // Custom polling control
  const startPolling = useCallback(() => {
    if (!shouldPoll || intervalRef.current) return;
    
    intervalRef.current = setInterval(() => {
      if (shouldPoll) {
        analysisQuery.refetch();
        progressQuery.refetch();
      } else {
        stopPolling();
      }
    }, 2000);
  }, [shouldPoll, analysisQuery, progressQuery]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return {
    analysis: analysisQuery.data,
    progress: progressQuery.data,
    isLoading: analysisQuery.isLoading || progressQuery.isLoading,
    error: analysisQuery.error || progressQuery.error,
    startPolling,
    stopPolling,
    refetch: () => {
      analysisQuery.refetch();
      progressQuery.refetch();
    },
  };
}

// Batch invalidation utility
export function useBatchInvalidation() {
  const queryClient = useQueryClient();

  const invalidateAllTeamData = useCallback(() => {
    queryClient.invalidateQueries({ 
      queryKey: ['teams'],
      exact: false 
    });
  }, [queryClient]);

  const invalidateAnalysisData = useCallback((analysisId?: string) => {
    if (analysisId) {
      queryClient.invalidateQueries({ 
        queryKey: ['analysis', analysisId],
        exact: false 
      });
    } else {
      queryClient.invalidateQueries({ 
        queryKey: ['analysis'],
        exact: false 
      });
    }
  }, [queryClient]);

  const invalidateSystemData = useCallback(() => {
    queryClient.invalidateQueries({ 
      queryKey: ['systemHealth'] 
    });
    queryClient.invalidateQueries({ 
      queryKey: ['system', 'status'] 
    });
  }, [queryClient]);

  return {
    invalidateAllTeamData,
    invalidateAnalysisData,
    invalidateSystemData,
  };
}

// Global error handler hook
export function useGlobalErrorHandler() {
  return useCallback((error: unknown) => {
    const message = getErrorMessage(error);
    console.error('API Error:', error);
    
    // You can extend this to integrate with error reporting services
    // like Sentry, Bugsnag, etc.
    
    return message;
  }, []);
}