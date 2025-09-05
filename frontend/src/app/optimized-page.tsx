/**
 * Optimized Baseball Trade AI Homepage
 * Uses React Query for state management and streaming for real-time updates
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import { toast } from 'react-hot-toast';
import { 
  Activity, 
  BarChart3, 
  Users, 
  Building2, 
  Search,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Zap
} from 'lucide-react';

// Optimized API hooks
import {
  useSystemHealth,
  useTeams,
  useTradeAnalysisMutation,
  usePrefetchHooks,
  useGlobalErrorHandler,
} from '@/hooks/use-api-queries';

import { useStreamingAnalysis, useBackgroundSync } from '@/lib/streaming-api';
import { type Team, type TradeAnalysis } from '@/lib/optimized-api';

// Components with error boundaries
import { ComponentErrorBoundary, APIErrorBoundary } from '@/components/ui/error-boundary';
import { ProgressiveLoading, LoadingButton } from '@/components/ui/loading-states';
import { 
  TeamSelectorSkeleton, 
  TradeFormSkeleton, 
  AnalysisProgressSkeleton,
  DepartmentOverviewSkeleton,
} from '@/components/ui/skeletons';

// Optimized component imports (will be created next)
import OptimizedTeamSelector from '@/components/optimized/OptimizedTeamSelector';
import OptimizedTradeForm from '@/components/optimized/OptimizedTradeForm';
import OptimizedAnalysisProgress from '@/components/optimized/OptimizedAnalysisProgress';
import OptimizedResultsDisplay from '@/components/optimized/OptimizedResultsDisplay';

export default function OptimizedHomePage() {
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [currentAnalysis, setCurrentAnalysis] = useState<TradeAnalysis | null>(null);
  
  // React Query hooks
  const systemHealthQuery = useSystemHealth();
  const teamsQuery = useTeams();
  const tradeAnalysisMutation = useTradeAnalysisMutation();
  const { prefetchTeamData } = usePrefetchHooks();
  const handleError = useGlobalErrorHandler();
  
  // Streaming and connectivity
  const { isOnline } = useBackgroundSync();
  const streamingAnalysis = useStreamingAnalysis(
    currentAnalysis?.analysis_id || '',
    !!currentAnalysis
  );

  // Memoized derived state
  const selectedTeamData = useMemo(() => {
    if (!selectedTeam || !teamsQuery.data?.teams) return null;
    return teamsQuery.data.teams[selectedTeam] || null;
  }, [selectedTeam, teamsQuery.data?.teams]);

  const systemHealth = systemHealthQuery.data;
  const isLoadingInitial = systemHealthQuery.isLoading || teamsQuery.isLoading;
  const hasConnectionError = systemHealthQuery.error || teamsQuery.error;

  // Prefetch team data when team is selected
  const handleTeamSelect = useCallback((teamKey: string) => {
    setSelectedTeam(teamKey);
    if (teamKey) {
      prefetchTeamData(teamKey);
    }
  }, [prefetchTeamData]);

  // Handle trade request with optimized error handling
  const handleTradeRequest = useCallback(async (requestData: {
    request: string;
    urgency: 'low' | 'medium' | 'high';
    budget_limit?: number;
  }) => {
    if (!selectedTeam) {
      toast.error('Please select a team first');
      return;
    }

    try {
      const analysis = await tradeAnalysisMutation.mutateAsync({
        ...requestData,
        team: selectedTeam,
      });
      
      setCurrentAnalysis(analysis);
      toast.success('AI trade analysis initiated!');
      
      // Start streaming updates
      streamingAnalysis.connect();
      
    } catch (error) {
      const message = handleError(error);
      toast.error(message);
    }
  }, [selectedTeam, tradeAnalysisMutation, streamingAnalysis, handleError]);

  // Department configuration
  const departments = useMemo(() => [
    {
      name: 'AI Coordinator',
      description: 'Orchestrates multi-agent analysis',
      icon: Building2,
      color: 'bg-blue-500'
    },
    {
      name: 'Chief Scout', 
      description: 'Player evaluation & scouting insights',
      icon: Search,
      color: 'bg-green-500'
    },
    {
      name: 'Analytics Director',
      description: 'Statistical analysis & projections',
      icon: BarChart3,
      color: 'bg-purple-500'
    },
    {
      name: 'Player Development',
      description: 'Prospect evaluation & development',
      icon: Users,
      color: 'bg-orange-500'
    },
    {
      name: 'Business Operations',
      description: 'Salary cap & financial analysis',
      icon: TrendingUp,
      color: 'bg-red-500'
    },
    {
      name: 'Smart GM System',
      description: 'Multi-team perspective analysis',
      icon: Activity,
      color: 'bg-indigo-500'
    }
  ], []);

  // Connection status display
  const ConnectionStatus = useMemo(() => {
    if (!isOnline) {
      return (
        <div className="flex items-center space-x-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs">
          <AlertCircle className="h-3 w-3" />
          <span>Offline</span>
        </div>
      );
    }

    if (streamingAnalysis.streaming.connected) {
      return (
        <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
          <CheckCircle className="h-3 w-3" />
          <span>Live Updates</span>
        </div>
      );
    }

    return null;
  }, [isOnline, streamingAnalysis.streaming.connected]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Baseball Trade AI
              </h1>
              <p className="text-gray-600 mt-1 text-sm sm:text-base">
                AI-Powered MLB Trade Analysis with Live Data
              </p>
            </div>
            
            {/* System Status and Connection */}
            <div className="flex items-center space-x-3">
              {ConnectionStatus}
              
              {systemHealth && (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    {systemHealth.status === 'operational' ? (
                      <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500" />
                    )}
                    <span className="text-xs sm:text-sm font-medium text-gray-700">
                      {typeof systemHealth.available_teams === 'number' 
                        ? systemHealth.available_teams 
                        : Array.isArray(systemHealth.available_teams)
                        ? systemHealth.available_teams.length
                        : 30
                      } Teams
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Zap className="h-3 w-3 sm:h-4 sm:w-4 text-blue-500" />
                    <span className="text-xs sm:text-sm text-gray-600">
                      Live Analysis
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* System Overview */}
        <div className="mb-6 lg:mb-8">
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4">
            AI Front Office Departments
          </h2>
          
          <ComponentErrorBoundary>
            <ProgressiveLoading
              isLoading={isLoadingInitial}
              skeleton={<DepartmentOverviewSkeleton />}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {departments.map((dept) => (
                  <div key={dept.name} className="bg-white rounded-lg p-3 sm:p-4 shadow-sm border">
                    <div className="flex items-center space-x-3">
                      <div className={`${dept.color} p-2 rounded-lg flex-shrink-0`}>
                        <dept.icon className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-medium text-gray-900 text-sm sm:text-base truncate">{dept.name}</h3>
                        <p className="text-xs sm:text-sm text-gray-600 line-clamp-2">{dept.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ProgressiveLoading>
          </ComponentErrorBoundary>
        </div>

        {/* Connection Error Display */}
        {hasConnectionError && (
          <APIErrorBoundary>
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <span className="font-medium text-red-900">Connection Error</span>
              </div>
              <p className="text-sm text-red-700 mt-1">
                {handleError(hasConnectionError)}
              </p>
              <div className="mt-3 flex space-x-3">
                <LoadingButton
                  onClick={() => {
                    systemHealthQuery.refetch();
                    teamsQuery.refetch();
                  }}
                  loading={systemHealthQuery.isRefetching || teamsQuery.isRefetching}
                  loadingText="Reconnecting..."
                  variant="outline"
                  size="sm"
                >
                  Try Again
                </LoadingButton>
              </div>
            </div>
          </APIErrorBoundary>
        )}

        {/* Main Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
          {/* Left Column - Team Selection */}
          <div className="lg:col-span-1 order-1 lg:order-1">
            <div className="bg-white rounded-lg shadow-sm border p-4 sm:p-6 lg:sticky lg:top-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Select Your Team
              </h3>
              
              <ComponentErrorBoundary>
                <ProgressiveLoading
                  isLoading={teamsQuery.isLoading}
                  error={teamsQuery.error}
                  retry={() => teamsQuery.refetch()}
                  skeleton={<TeamSelectorSkeleton />}
                >
                  <OptimizedTeamSelector
                    teams={teamsQuery.data?.teams || {}}
                    selectedTeam={selectedTeam}
                    onTeamSelect={handleTeamSelect}
                    loading={teamsQuery.isLoading}
                  />
                </ProgressiveLoading>
              </ComponentErrorBoundary>
              
              {/* Selected team display */}
              {selectedTeamData && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {selectedTeamData.name}
                  </h4>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><span className="font-medium">Division:</span> {selectedTeamData.division}</p>
                    <p><span className="font-medium">Budget:</span> {selectedTeamData.budget_level}</p>
                    <p><span className="font-medium">Window:</span> {selectedTeamData.competitive_window}</p>
                    <p><span className="font-medium">Philosophy:</span> {selectedTeamData.philosophy}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Trade Request & Results */}
          <div className="lg:col-span-2 space-y-6 order-2 lg:order-2">
            {/* Trade Request Form */}
            <div className="bg-white rounded-lg shadow-sm border p-4 sm:p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Trade Request
              </h3>
              
              <ComponentErrorBoundary>
                <ProgressiveLoading
                  isLoading={false} // Form doesn't need loading state
                  skeleton={<TradeFormSkeleton />}
                >
                  <OptimizedTradeForm
                    onSubmit={handleTradeRequest}
                    loading={tradeAnalysisMutation.isPending}
                    selectedTeam={selectedTeam}
                    selectedTeamData={selectedTeamData}
                    error={tradeAnalysisMutation.error}
                  />
                </ProgressiveLoading>
              </ComponentErrorBoundary>
            </div>

            {/* Analysis Progress */}
            {currentAnalysis && (
              <ComponentErrorBoundary>
                <ProgressiveLoading
                  isLoading={false}
                  skeleton={<AnalysisProgressSkeleton />}
                >
                  <OptimizedAnalysisProgress
                    analysis={streamingAnalysis.analysis || currentAnalysis}
                    progress={streamingAnalysis.progress}
                    streaming={streamingAnalysis.streaming}
                    onUpdate={setCurrentAnalysis}
                  />
                </ProgressiveLoading>
              </ComponentErrorBoundary>
            )}

            {/* Results Display */}
            {(currentAnalysis?.status === 'completed' || streamingAnalysis.analysis?.status === 'completed') && (
              <ComponentErrorBoundary>
                <OptimizedResultsDisplay 
                  analysis={streamingAnalysis.analysis || currentAnalysis} 
                />
              </ComponentErrorBoundary>
            )}
          </div>
        </div>

        {/* System Status Footer */}
        <div className="mt-12">
          <ComponentErrorBoundary>
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                System Status
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div className="p-4">
                  <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    systemHealth?.status === 'operational' ? 'bg-green-100' : 'bg-yellow-100'
                  }`}>
                    {systemHealth?.status === 'operational' ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                    )}
                  </div>
                  <p className="font-medium text-gray-900">Backend</p>
                  <p className="text-sm text-gray-600">
                    {systemHealth?.status || 'Unknown'}
                  </p>
                </div>
                
                <div className="p-4">
                  <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    teamsQuery.data?.source === 'database' ? 'bg-green-100' : 'bg-blue-100'
                  }`}>
                    <Activity className={`h-5 w-5 ${
                      teamsQuery.data?.source === 'database' ? 'text-green-600' : 'text-blue-600'
                    }`} />
                  </div>
                  <p className="font-medium text-gray-900">Data Source</p>
                  <p className="text-sm text-gray-600 capitalize">
                    {teamsQuery.data?.source || 'Loading...'}
                  </p>
                </div>
                
                <div className="p-4">
                  <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
                    isOnline ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    <Zap className={`h-5 w-5 ${
                      isOnline ? 'text-green-600' : 'text-red-600'
                    }`} />
                  </div>
                  <p className="font-medium text-gray-900">Connection</p>
                  <p className="text-sm text-gray-600">
                    {isOnline ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>
              
              {/* Performance metrics (development only) */}
              {process.env.NODE_ENV === 'development' && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <details className="text-sm">
                    <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                      Performance Metrics
                    </summary>
                    <div className="mt-2 space-y-1 text-xs text-gray-600">
                      <p>Teams Query: {teamsQuery.dataUpdatedAt ? 'Cached' : 'Fresh'}</p>
                      <p>Health Check: {systemHealthQuery.dataUpdatedAt ? 'Cached' : 'Fresh'}</p>
                      <p>Streaming: {streamingAnalysis.streaming.connected ? 'Connected' : 'Disconnected'}</p>
                    </div>
                  </details>
                </div>
              )}
            </div>
          </ComponentErrorBoundary>
        </div>
      </div>
    </div>
  );
}