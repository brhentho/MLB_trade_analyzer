/**
 * Optimized Analysis Progress Component
 * Implements streaming updates, performance monitoring, and optimized rendering
 */

'use client';

import { memo, useMemo, useCallback, useEffect } from 'react';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Search,
  BarChart3,
  Users,
  Building2,
  TrendingUp,
  Activity,
  Shield,
  Wifi,
  WifiOff
} from 'lucide-react';

import { cn, formatDuration } from '@/lib/utils';
import { StepProgress } from '@/components/ui/loading-states';
import { type TradeAnalysis, type AnalysisProgress } from '@/lib/optimized-api';
import { type SSEConnectionStatus } from '@/lib/streaming-api';

interface OptimizedAnalysisProgressProps {
  analysis: TradeAnalysis;
  progress?: AnalysisProgress | null;
  streaming?: {
    connected: boolean;
    lastEvent?: any;
    error?: string;
  };
  onUpdate: (analysis: TradeAnalysis) => void;
}

// Memoized progress header
const ProgressHeader = memo(function ProgressHeader({
  analysis,
  progressPercentage,
  completedSteps,
  totalSteps,
  streamingConnected,
}: {
  analysis: TradeAnalysis;
  progressPercentage: number;
  completedSteps: number;
  totalSteps: number;
  streamingConnected: boolean;
}) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-1">
          <h3 className="text-lg font-semibold text-gray-900">
            AI Analysis in Progress
          </h3>
          {streamingConnected ? (
            <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
              <Wifi className="h-3 w-3" />
              <span>Live</span>
            </div>
          ) : (
            <div className="flex items-center space-x-1 px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
              <WifiOff className="h-3 w-3" />
              <span>Polling</span>
            </div>
          )}
        </div>
        <p className="text-sm text-gray-600">
          {analysis.team} • {analysis.original_request}
        </p>
      </div>
      
      <div className="text-right ml-4">
        <div className="text-2xl font-bold text-blue-600">
          {Math.round(progressPercentage)}%
        </div>
        <div className="text-sm text-gray-500">
          {completedSteps} of {totalSteps} complete
        </div>
      </div>
    </div>
  );
});

// Memoized progress bar
const ProgressBar = memo(function ProgressBar({
  percentage,
  animated = true,
}: {
  percentage: number;
  animated?: boolean;
}) {
  return (
    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
      <div 
        className={cn(
          'h-2 rounded-full bg-gradient-to-r from-blue-500 to-blue-600',
          animated && 'transition-all duration-500 ease-out'
        )}
        style={{ width: `${Math.max(0, Math.min(100, percentage))}%` }}
      />
    </div>
  );
});

// Memoized time estimation display
const TimeEstimation = memo(function TimeEstimation({
  analysis,
  progress,
  streamingError,
}: {
  analysis: TradeAnalysis;
  progress?: AnalysisProgress | null;
  streamingError?: string;
}) {
  const estimatedTime = progress?.estimated_remaining_time;
  const isActive = analysis.status !== 'completed' && analysis.status !== 'error';

  if (!isActive) return null;

  return (
    <div className={cn(
      'p-4 rounded-lg border',
      streamingError 
        ? 'bg-yellow-50 border-yellow-200' 
        : 'bg-blue-50 border-blue-200'
    )}>
      <div className="flex items-center space-x-2">
        <Clock className={cn(
          'h-4 w-4',
          streamingError ? 'text-yellow-600' : 'text-blue-600'
        )} />
        <p className={cn(
          'text-sm font-medium',
          streamingError ? 'text-yellow-700' : 'text-blue-700'
        )}>
          {estimatedTime ? (
            <>Estimated remaining: {formatDuration(estimatedTime)}</>
          ) : (
            <>Estimated completion: 60-90 seconds</>
          )}
        </p>
      </div>
      
      {progress?.current_department && (
        <p className={cn(
          'text-sm mt-1',
          streamingError ? 'text-yellow-600' : 'text-blue-600'
        )}>
          Currently processing: {progress.current_department}
        </p>
      )}
      
      {streamingError && (
        <p className="text-xs text-yellow-600 mt-1">
          Connection issue: {streamingError} (using fallback polling)
        </p>
      )}
    </div>
  );
});

// Main progress component
const OptimizedAnalysisProgress = memo(function OptimizedAnalysisProgress({
  analysis,
  progress,
  streaming,
  onUpdate,
}: OptimizedAnalysisProgressProps) {
  // Memoized steps configuration
  const steps = useMemo(() => [
    {
      id: 'coordination',
      name: 'Front Office Leadership',
      description: 'Orchestrating multi-agent analysis',
      icon: Building2,
      color: 'blue'
    },
    {
      id: 'scouting',
      name: 'Scouting Department',
      description: 'Player evaluation & scouting insights',
      icon: Search,
      color: 'green'
    },
    {
      id: 'analytics',
      name: 'Analytics Department',
      description: 'Statistical analysis & projections',
      icon: BarChart3,
      color: 'purple'
    },
    {
      id: 'development',
      name: 'Player Development',
      description: 'Prospect evaluation & development',
      icon: Users,
      color: 'orange'
    },
    {
      id: 'business',
      name: 'Business Operations',
      description: 'Salary cap & financial analysis',
      icon: TrendingUp,
      color: 'red'
    },
    {
      id: 'gm_perspective',
      name: 'Team Management',
      description: 'Multi-team perspective analysis',
      icon: Activity,
      color: 'indigo'
    },
  ], []);

  // Memoized step status calculation
  const stepStatuses = useMemo(() => {
    return steps.map(step => {
      const stepName = step.name;
      
      // Check if completed
      if (progress?.completed_departments.includes(stepName)) {
        return 'completed';
      }
      
      // Check if currently processing
      if (progress?.current_department === stepName) {
        return 'in_progress';
      }
      
      return 'pending';
    });
  }, [steps, progress]);

  // Memoized progress calculations
  const progressMetrics = useMemo(() => {
    const completedSteps = stepStatuses.filter(status => status === 'completed').length;
    const progressPercentage = progress?.progress 
      ? progress.progress * 100 
      : (completedSteps / steps.length) * 100;
    
    return {
      completedSteps,
      progressPercentage: Math.max(0, Math.min(100, progressPercentage)),
      totalSteps: steps.length,
    };
  }, [stepStatuses, progress, steps.length]);

  // Memoized steps with status
  const stepsWithStatus = useMemo(() => {
    return steps.map((step, index) => ({
      ...step,
      status: stepStatuses[index] as 'pending' | 'in_progress' | 'completed' | 'error',
    }));
  }, [steps, stepStatuses]);

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <ProgressHeader
        analysis={analysis}
        progressPercentage={progressMetrics.progressPercentage}
        completedSteps={progressMetrics.completedSteps}
        totalSteps={progressMetrics.totalSteps}
        streamingConnected={streaming?.connected || false}
      />

      {/* Progress Bar */}
      <div className="mb-6">
        <ProgressBar 
          percentage={progressMetrics.progressPercentage}
          animated={true}
        />
      </div>

      {/* Steps */}
      <StepProgress 
        steps={stepsWithStatus}
        orientation="vertical"
      />

      {/* Status Messages */}
      {analysis.status === 'error' && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span className="font-medium text-red-900">Analysis Failed</span>
          </div>
          <p className="text-sm text-red-700 mt-1">
            {analysis.error_message || 'An unexpected error occurred during analysis.'}
          </p>
        </div>
      )}

      {analysis.status === 'completed' && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="font-medium text-green-900">Analysis Complete!</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            Your AI-powered trade analysis is ready. Results are displayed below.
          </p>
        </div>
      )}

      {/* Time Estimation */}
      <TimeEstimation
        analysis={analysis}
        progress={progress}
        streamingError={streaming?.error}
      />
    </div>
  );
});

export default OptimizedAnalysisProgress;