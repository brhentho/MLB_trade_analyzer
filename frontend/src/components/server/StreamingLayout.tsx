/**
 * Streaming Layout Component with React 18 Features
 * Provides progressive rendering and streaming SSR
 */

import { Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import ServerSystemHealth from './ServerSystemHealth';
import ServerTeamsProvider from './ServerTeamsProvider';
import { DepartmentOverviewSkeleton } from '@/components/ui/skeletons';

interface StreamingLayoutProps {
  children: React.ReactNode;
}

// Department data - can be static since it rarely changes
const DEPARTMENTS = [
  {
    name: 'AI Coordinator',
    description: 'Orchestrates multi-agent analysis',
    icon: 'Building2',
    color: 'bg-blue-500'
  },
  {
    name: 'Chief Scout', 
    description: 'Player evaluation & scouting insights',
    icon: 'Search',
    color: 'bg-green-500'
  },
  {
    name: 'Analytics Director',
    description: 'Statistical analysis & projections',
    icon: 'BarChart3',
    color: 'bg-purple-500'
  },
  {
    name: 'Player Development',
    description: 'Prospect evaluation & development',
    icon: 'Users',
    color: 'bg-orange-500'
  },
  {
    name: 'Business Operations',
    description: 'Salary cap & financial analysis',
    icon: 'TrendingUp',
    color: 'bg-red-500'
  },
  {
    name: 'Smart GM System',
    description: 'Multi-team perspective analysis',
    icon: 'Activity',
    color: 'bg-indigo-500'
  }
];

// Static department overview (doesn't need streaming)
function DepartmentOverview() {
  return (
    <div className="mb-6 lg:mb-8">
      <h2 className="text-lg sm:text-xl font-semibold text-gray-900 mb-4">
        AI Front Office Departments
      </h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
        {DEPARTMENTS.map((dept) => {
          // Dynamic icon import would happen here in a real implementation
          return (
            <div key={dept.name} className="bg-white rounded-lg p-3 sm:p-4 shadow-sm border">
              <div className="flex items-center space-x-3">
                <div className={`${dept.color} p-2 rounded-lg flex-shrink-0`}>
                  {/* Icon placeholder - in real app, use dynamic imports */}
                  <div className="h-4 w-4 sm:h-5 sm:w-5 bg-white bg-opacity-80 rounded" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-medium text-gray-900 text-sm sm:text-base truncate">
                    {dept.name}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600 line-clamp-2">
                    {dept.description}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Header with streaming system health
function StreamingHeader() {
  return (
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
          
          {/* System Status - Streams independently */}
          <Suspense 
            fallback={
              <div className="flex items-center space-x-3">
                <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
                <div className="h-6 w-24 bg-gray-200 rounded-full animate-pulse" />
              </div>
            }
          >
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span>Live</span>
              </div>
              <ServerSystemHealth />
            </div>
          </Suspense>
        </div>
      </div>
    </div>
  );
}

// Main content area with progressive enhancement
function StreamingContent({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Department Overview - Static */}
      <ErrorBoundary 
        fallback={<DepartmentOverviewSkeleton />}
        onError={(error) => console.error('Department overview error:', error)}
      >
        <DepartmentOverview />
      </ErrorBoundary>

      {/* Dynamic Content */}
      <ErrorBoundary
        fallback={
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800">Something went wrong loading the interface.</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Reload Page
            </button>
          </div>
        }
      >
        {children}
      </ErrorBoundary>
    </div>
  );
}

export default function StreamingLayout({ children }: StreamingLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header streams system health independently */}
      <StreamingHeader />
      
      {/* Main content with progressive loading */}
      <StreamingContent>
        {children}
      </StreamingContent>
    </div>
  );
}