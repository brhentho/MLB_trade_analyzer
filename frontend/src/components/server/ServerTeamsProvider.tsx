/**
 * Server Component for Teams Data
 * Provides static generation with ISR for optimal performance
 */

import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { serverAPI } from '@/lib/server-api';
import { TeamSelectorSkeleton } from '@/components/ui/skeletons';

interface ServerTeamsProviderProps {
  children: (teams: Record<string, any>) => React.ReactNode;
  fallback?: React.ReactNode;
}

async function TeamsData({ children }: { children: (teams: Record<string, any>) => React.ReactNode }) {
  try {
    const teamsData = await serverAPI.teams.getAll();
    return <>{children(teamsData?.teams || {})}</>;
  } catch (error) {
    console.error('Server teams fetch failed:', error);
    throw error;
  }
}

function TeamsErrorFallback({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <h3 className="text-red-800 font-medium mb-2">Failed to load teams</h3>
      <p className="text-red-600 text-sm mb-3">{error.message}</p>
      <button
        onClick={resetErrorBoundary}
        className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
      >
        Try Again
      </button>
    </div>
  );
}

export default function ServerTeamsProvider({ children, fallback }: ServerTeamsProviderProps) {
  return (
    <ErrorBoundary FallbackComponent={TeamsErrorFallback}>
      <Suspense fallback={fallback || <TeamSelectorSkeleton />}>
        <TeamsData>
          {children}
        </TeamsData>
      </Suspense>
    </ErrorBoundary>
  );
}