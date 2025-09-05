/**
 * Global Loading Component for App Router
 * Provides consistent loading experience across all routes
 */

import { Skeleton } from '@/components/ui/skeletons';
import { Loader2, BarChart3 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Skeleton */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
            <div className="space-y-2">
              <Skeleton className="h-8 w-64" />
              <Skeleton className="h-4 w-80" />
            </div>
            <div className="flex items-center space-x-3">
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="h-6 w-24 rounded-full" />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading indicator with animation */}
        <div className="flex flex-col items-center justify-center py-12">
          <div className="relative">
            <BarChart3 className="h-12 w-12 text-blue-300 animate-pulse" />
            <Loader2 className="h-6 w-6 text-blue-600 animate-spin absolute -bottom-1 -right-1" />
          </div>
          
          <h2 className="mt-4 text-xl font-semibold text-gray-900">
            Loading Baseball Trade AI
          </h2>
          <p className="mt-2 text-sm text-gray-600 text-center max-w-md">
            Initializing AI agents and connecting to live MLB data...
          </p>
          
          {/* Progressive loading steps */}
          <div className="mt-6 space-y-2 w-full max-w-sm">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="text-sm text-gray-600">Connecting to backend services</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{animationDelay: '0.5s'}} />
              <span className="text-sm text-gray-400">Loading team data</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 w-2 h-2 bg-gray-300 rounded-full animate-pulse" style={{animationDelay: '1s'}} />
              <span className="text-sm text-gray-400">Initializing AI agents</span>
            </div>
          </div>
        </div>

        {/* Department Overview Skeleton */}
        <div className="mb-8">
          <Skeleton className="h-6 w-48 mb-4" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white rounded-lg p-4 shadow-sm border">
                <div className="flex items-center space-x-3">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Interface Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Team Selection Skeleton */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <Skeleton className="h-6 w-32 mb-4" />
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <div className="space-y-2">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Trade Form and Results Skeleton */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <Skeleton className="h-6 w-32 mb-4" />
              <div className="space-y-4">
                <Skeleton className="h-32 w-full" />
                <div className="flex space-x-4">
                  <Skeleton className="h-10 w-24" />
                  <Skeleton className="h-10 w-32" />
                  <Skeleton className="h-10 w-28" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}