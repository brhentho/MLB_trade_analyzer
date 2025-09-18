'use client';

import { useState, useEffect } from 'react';
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
  Shield
} from 'lucide-react';
import { tradeApi, type TradeAnalysis, type AnalysisProgress } from '@/lib/api';

interface AnalysisProgressProps {
  analysis: TradeAnalysis;
  onUpdate: (analysis: TradeAnalysis) => void;
}

export default function AnalysisProgress({ analysis, onUpdate }: AnalysisProgressProps) {
  const [progress, setProgress] = useState<AnalysisProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Polling interval for progress updates
  useEffect(() => {
    if (analysis.status === 'completed' || analysis.status === 'error') {
      return;
    }

    const pollProgress = async () => {
      try {
        if (!analysis.analysis_id) {
          console.warn('No analysis ID available for progress polling');
          return;
        }
        
        // Get progress data first
        const progressData = await tradeApi.getAnalysisProgress(analysis.analysis_id);
        setProgress(progressData);
        setError(null);
        
        // Also get updated analysis data
        const updatedAnalysis = await tradeApi.getAnalysisStatus(analysis.analysis_id);
        onUpdate(updatedAnalysis);
        
      } catch (error: any) {
        console.error('Failed to fetch progress:', {
          analysisId: analysis.analysis_id,
          error: error
        });
        
        // Set user-friendly error message
        const errorMessage = error.userMessage || error.message || 'Failed to get progress updates';
        setError(errorMessage);
        
        // If analysis is not found, stop polling
        if (error.message.includes('not found')) {
          setError('Analysis session expired. Please start a new analysis.');
        }
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(pollProgress, 3000);
    
    // Initial poll
    pollProgress();

    return () => clearInterval(interval);
  }, [analysis.analysis_id, analysis.status, onUpdate]);


  const steps = [
    {
      key: 'coordination',
      name: 'Front Office Leadership',
      description: 'Orchestrating multi-agent analysis',
      icon: Building2,
      color: 'blue'
    },
    {
      key: 'scouting',
      name: 'Scouting Department',
      description: 'Player evaluation & scouting insights',
      icon: Search,
      color: 'green'
    },
    {
      key: 'analytics',
      name: 'Analytics Department',
      description: 'Statistical analysis & projections',
      icon: BarChart3,
      color: 'purple'
    },
    {
      key: 'development',
      name: 'Player Development',
      description: 'Prospect evaluation & development',
      icon: Users,
      color: 'orange'
    },
    {
      key: 'business',
      name: 'Business Operations',
      description: 'Salary cap & financial analysis',
      icon: TrendingUp,
      color: 'red'
    },
    {
      key: 'gm_perspective',
      name: 'Team Management',
      description: 'Multi-team perspective analysis',
      icon: Activity,
      color: 'indigo'
    },
    {
      key: 'compliance',
      name: 'Commissioner Office',
      description: 'MLB regulation and rule verification',
      icon: Shield,
      color: 'gray'
    }
  ];

  const getStepStatus = (stepKey: string) => {
    if (!progress) return 'pending';
    
    // Check if this step is in completed departments
    const stepName = steps.find(s => s.key === stepKey)?.name;
    if (stepName && progress.completed_departments.includes(stepName)) {
      return 'completed';
    }
    
    // Check if this step is currently being processed
    if (stepName && progress.current_department === stepName) {
      return 'in_progress';
    }
    
    return 'pending';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-400" />;
      case 'in_progress':
        return (
          <div className="h-5 w-5 border-2 border-statslugger-orange-primary border-t-transparent rounded-full animate-spin" />
        );
      default:
        return <Clock className="h-5 w-5 text-statslugger-text-muted" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-900/30 border-green-600/30';
      case 'in_progress':
        return 'bg-statslugger-orange-primary/20 border-statslugger-orange-primary/30';
      default:
        return 'bg-statslugger-navy-primary border-statslugger-navy-border';
    }
  };

  const completedSteps = steps.filter(step => getStepStatus(step.key) === 'completed').length;
  const progressPercentage = progress ? progress.progress * 100 : (completedSteps / steps.length) * 100;
  
  // Format remaining time
  const formatRemainingTime = (seconds?: number) => {
    if (!seconds || seconds <= 0) return null;
    if (seconds < 60) return `${seconds} seconds`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes} minutes`;
  };

  return (
    <div className="bg-statslugger-navy-deep rounded-lg shadow-sm border border-statslugger-navy-border p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-statslugger-text-primary">
            AI Analysis in Progress
          </h3>
          <p className="text-sm text-statslugger-text-secondary">
            {analysis.team} • {analysis.original_request}
          </p>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-statslugger-orange-primary">
            {Math.round(progressPercentage)}%
          </div>
          <div className="text-sm text-statslugger-text-muted">
            {completedSteps} of {steps.length} complete
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="w-full bg-statslugger-navy-border rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-statslugger-orange-primary to-statslugger-orange-secondary h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step) => {
          const status = getStepStatus(step.key);
          const StepIcon = step.icon;
          
          return (
            <div
              key={step.key}
              className={`p-4 rounded-lg border transition-all duration-300 ${getStatusColor(status)}`}
            >
              <div className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  {getStatusIcon(status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <StepIcon className={`h-4 w-4 text-${step.color}-500`} />
                    <h4 className="font-medium text-statslugger-text-primary">
                      {step.name}
                    </h4>
                  </div>
                  <p className="text-sm text-statslugger-text-secondary mt-1">
                    {step.description}
                  </p>
                </div>
                
                <div className="flex-shrink-0">
                  {status === 'completed' && (
                    <span className="text-xs font-medium text-green-400">
                      ✓ Done
                    </span>
                  )}
                  {status === 'in_progress' && (
                    <span className="text-xs font-medium text-statslugger-orange-primary">
                      Working...
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Error Messages */}
      {error && (
        <div className="mt-6 p-4 bg-red-900/30 border border-red-600/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span className="font-medium text-red-300">Progress Update Failed</span>
          </div>
          <p className="text-sm text-red-700 mt-1">
            {error}
          </p>
        </div>
      )}

      {/* Status Messages */}
      {analysis.status === 'error' && (
        <div className="mt-6 p-4 bg-red-900/30 border border-red-600/30 rounded-lg">
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
        <div className="mt-6 p-4 bg-green-900/30 border border-green-600/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="font-medium text-green-900">Analysis Complete!</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            Your AI-powered trade analysis is ready. Scroll down to view the results.
          </p>
        </div>
      )}

      {/* Time Estimation */}
      {analysis.status !== 'completed' && analysis.status !== 'error' && (
        <div className="mt-6 p-4 bg-statslugger-orange-primary/20 border border-statslugger-orange-primary/30 rounded-lg">
          <p className="text-sm text-blue-700">
            <Clock className="inline h-4 w-4 mr-1" />
            {progress?.estimated_remaining_time ? (
              <>Estimated remaining time: {formatRemainingTime(progress.estimated_remaining_time)}</>
            ) : (
              <>Estimated completion time: 60-90 seconds</>
            )}
          </p>
          {progress?.current_department && (
            <p className="text-sm text-blue-600 mt-1">
              Currently processing: {progress.current_department}
            </p>
          )}
        </div>
      )}
    </div>
  );
}