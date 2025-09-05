/**
 * Server Component for System Health
 * Provides real-time system status with efficient caching
 */

import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { CheckCircle, AlertCircle, Activity, Zap } from 'lucide-react';
import { serverAPI } from '@/lib/server-api';

async function SystemHealthData() {
  try {
    const healthData = await serverAPI.system.getHealth();
    
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
        <div className="p-4">
          <div className={`w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center ${
            healthData?.status === 'operational' ? 'bg-green-100' : 'bg-yellow-100'
          }`}>
            {healthData?.status === 'operational' ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600" />
            )}
          </div>
          <p className="font-medium text-gray-900">Backend</p>
          <p className="text-sm text-gray-600">
            {healthData?.status || 'Unknown'}
          </p>
        </div>
        
        <div className="p-4">
          <div className="w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center bg-blue-100">
            <Activity className="h-5 w-5 text-blue-600" />
          </div>
          <p className="font-medium text-gray-900">Teams</p>
          <p className="text-sm text-gray-600">
            {typeof healthData?.available_teams === 'number' 
              ? healthData.available_teams 
              : Array.isArray(healthData?.available_teams)
              ? healthData.available_teams.length
              : 30
            } Available
          </p>
        </div>
        
        <div className="p-4">
          <div className="w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center bg-green-100">
            <Zap className="h-5 w-5 text-green-600" />
          </div>
          <p className="font-medium text-gray-900">AI Agents</p>
          <p className="text-sm text-gray-600">
            {Array.isArray(healthData?.departments) 
              ? healthData.departments.length 
              : 6
            } Active
          </p>
        </div>
      </div>
    );
  } catch (error) {
    console.error('System health fetch failed:', error);
    throw error;
  }
}

function SystemHealthSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="p-4">
          <div className="w-8 h-8 rounded-full mx-auto mb-2 bg-gray-200 animate-pulse" />
          <div className="h-4 bg-gray-200 rounded mx-auto w-16 mb-2 animate-pulse" />
          <div className="h-3 bg-gray-200 rounded mx-auto w-20 animate-pulse" />
        </div>
      ))}
    </div>
  );
}

function SystemHealthError({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
      <AlertCircle className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
      <h3 className="text-yellow-800 font-medium mb-2">System Status Unavailable</h3>
      <p className="text-yellow-600 text-sm mb-3">
        Unable to fetch system health information.
      </p>
      <button
        onClick={resetErrorBoundary}
        className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 transition-colors"
      >
        Retry
      </button>
    </div>
  );
}

export default function ServerSystemHealth() {
  return (
    <ErrorBoundary FallbackComponent={SystemHealthError}>
      <Suspense fallback={<SystemHealthSkeleton />}>
        <SystemHealthData />
      </Suspense>
    </ErrorBoundary>
  );
}