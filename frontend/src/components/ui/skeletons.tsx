/**
 * Skeleton Loading Components
 * Provides consistent loading states across the application
 */

import { cn } from '@/lib/utils';

// Base skeleton component with accessibility
export function Skeleton({
  className,
  "aria-label": ariaLabel = "Loading...",
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  "aria-label"?: string;
}) {
  return (
    <div
      className={cn(
        'skeleton rounded-md bg-muted animate-pulse',
        'motion-safe:animate-pulse motion-reduce:animate-none',
        className
      )}
      role="status"
      aria-label={ariaLabel}
      aria-live="polite"
      {...props}
    />
  );
}

// Player card skeleton
export function PlayerCardSkeleton({ 
  compact = false,
  className 
}: { 
  compact?: boolean; 
  className?: string;
}) {
  return (
    <div 
      className={cn(
        "player-card space-y-3",
        compact ? "p-3" : "p-4",
        className
      )}
      role="status"
      aria-label="Loading player information"
    >
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-8 rounded-full" aria-label="Loading position badge" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-4 w-3/4" aria-label="Loading player name" />
          <Skeleton className="h-3 w-1/2" aria-label="Loading team information" />
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="stat-card p-2">
            <Skeleton className="h-3 w-12 mb-1" />
            <Skeleton className="h-4 w-8" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Team card skeleton
export function TeamCardSkeleton({ className }: { className?: string }) {
  return (
    <div 
      className={cn("card overflow-hidden", className)}
      role="status"
      aria-label="Loading team information"
    >
      <Skeleton className="h-2 w-full" aria-label="Loading team colors" />
      
      <div className="card-header">
        <div className="flex items-center gap-3">
          <Skeleton className="h-3 w-3 rounded-full" />
          <div className="space-y-1">
            <Skeleton className="h-4 w-24" aria-label="Loading team name" />
            <Skeleton className="h-3 w-32" aria-label="Loading division" />
          </div>
        </div>
      </div>
      
      <div className="card-content">
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="text-center">
              <Skeleton className="h-5 w-8 mx-auto mb-1" />
              <Skeleton className="h-3 w-12 mx-auto" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Team selector skeleton
export function TeamSelectorSkeleton() {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="grid grid-cols-1 gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    </div>
  );
}

// Trade form skeleton
export function TradeFormSkeleton() {
  return (
    <div className="space-y-6">
      {/* Request textarea */}
      <div>
        <Skeleton className="h-4 w-48 mb-2" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-3 w-64 mt-1" />
      </div>

      {/* Example requests */}
      <div>
        <Skeleton className="h-4 w-32 mb-3" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>

      {/* Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div>
          <Skeleton className="h-4 w-28 mb-2" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>

      {/* Submit button */}
      <Skeleton className="h-12 w-full" />
    </div>
  );
}

// Analysis progress skeleton
export function AnalysisProgressSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="text-right">
          <Skeleton className="h-8 w-16 mb-1" />
          <Skeleton className="h-4 w-24" />
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full w-1/3 animate-pulse" />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="p-4 rounded-lg border bg-gray-50">
            <div className="flex items-center space-x-4">
              <Skeleton className="h-5 w-5 rounded-full" />
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <Skeleton className="h-4 w-4" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Results display skeleton
export function ResultsDisplaySkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-6 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
          <div className="flex items-center space-x-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="px-6">
          <div className="flex space-x-8 -mb-px">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center space-x-2 py-4">
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        <div>
          <Skeleton className="h-5 w-32 mb-3" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Skeleton className="h-5 w-5" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-8 w-16 mb-1" />
              <Skeleton className="h-3 w-32" />
            </div>
          ))}
        </div>

        {/* Recommendation cards */}
        <div className="space-y-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <Skeleton className="h-6 w-8" />
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-4 w-48" />
                </div>
                <Skeleton className="h-6 w-24 rounded-full" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Array.from({ length: 3 }).map((_, j) => (
                  <div key={j}>
                    <Skeleton className="h-4 w-20 mb-2" />
                    <div className="space-y-1">
                      {Array.from({ length: 3 }).map((_, k) => (
                        <Skeleton key={k} className="h-3 w-full" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// System status skeleton
export function SystemStatusSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <Skeleton className="h-6 w-32 mb-4" />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="text-center p-4">
            <Skeleton className="h-8 w-8 rounded-full mx-auto mb-2" />
            <Skeleton className="h-4 w-20 mx-auto mb-1" />
            <Skeleton className="h-3 w-16 mx-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Department overview skeleton
export function DepartmentOverviewSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-white rounded-lg p-3 sm:p-4 shadow-sm border">
          <div className="flex items-center space-x-3">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="min-w-0 flex-1">
              <Skeleton className="h-4 w-24 mb-1" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Card skeleton for general use
export function CardSkeleton({
  lines = 3,
  showHeader = true,
  showAction = false,
  className,
}: {
  lines?: number;
  showHeader?: boolean;
  showAction?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('bg-white rounded-lg shadow-sm border p-4 sm:p-6', className)}>
      {showHeader && (
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-5 w-32" />
          {showAction && <Skeleton className="h-8 w-20" />}
        </div>
      )}
      
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton 
            key={i} 
            className={cn(
              'h-4',
              i === lines - 1 ? 'w-3/4' : 'w-full'
            )}
          />
        ))}
      </div>
    </div>
  );
}

// List skeleton
export function ListSkeleton({
  items = 5,
  showAvatar = false,
  className,
}: {
  items?: number;
  showAvatar?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-3">
          {showAvatar && <Skeleton className="h-10 w-10 rounded-full" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

// Trade analysis skeleton
export function TradeAnalysisSkeleton() {
  return (
    <div 
      className="card space-y-6"
      role="status"
      aria-label="Loading trade analysis"
    >
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-6 w-40 mb-2" aria-label="Loading analysis title" />
            <Skeleton className="h-4 w-60" aria-label="Loading trade details" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-20 rounded-full" />
            <Skeleton className="h-5 w-5 rounded-full" />
          </div>
        </div>
      </div>

      <div className="card-content space-y-4">
        {/* Trade participants */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <TeamCardSkeleton key={i} />
          ))}
        </div>

        {/* Analysis breakdown */}
        <div className="space-y-3">
          <Skeleton className="h-5 w-32" aria-label="Loading analysis section title" />
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="p-3 border border-border rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-6 w-16 rounded-full ml-auto" />
              </div>
              <Skeleton className="h-3 w-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Player search results skeleton
export function PlayerSearchSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div 
      className="space-y-3"
      role="status" 
      aria-label="Loading player search results"
    >
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" aria-label="Loading results count" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: count }).map((_, i) => (
          <PlayerCardSkeleton key={i} compact />
        ))}
      </div>
    </div>
  );
}

// Baseball field skeleton (for visual representations)
export function BaseballFieldSkeleton() {
  return (
    <div 
      className="aspect-square rounded-lg bg-muted p-4 relative overflow-hidden"
      role="status"
      aria-label="Loading baseball field visualization"
    >
      {/* Field background */}
      <Skeleton className="absolute inset-0" />
      
      {/* Position markers */}
      {Array.from({ length: 9 }).map((_, i) => (
        <Skeleton 
          key={i}
          className="absolute h-6 w-6 rounded-full"
          style={{
            top: `${20 + (i % 3) * 30}%`,
            left: `${20 + Math.floor(i / 3) * 30}%`,
          }}
        />
      ))}
    </div>
  );
}

// Trade timeline skeleton
export function TradeTimelineSkeleton() {
  return (
    <div 
      className="space-y-4"
      role="status"
      aria-label="Loading trade timeline"
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton className="h-8 w-8 rounded-full" />
            {i < 4 && <Skeleton className="h-8 w-px mt-2" />}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-3 w-16" />
            </div>
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Data table skeleton
export function DataTableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true,
}: {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}) {
  return (
    <div 
      className="border border-border rounded-lg overflow-hidden"
      role="status"
      aria-label="Loading data table"
    >
      {/* Table header */}
      {showHeader && (
        <div className="bg-muted/50 border-b border-border">
          <div className="grid gap-4 p-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-20" />
            ))}
          </div>
        </div>
      )}
      
      {/* Table rows */}
      <div className="space-y-0">
        {Array.from({ length: rows }).map((_, i) => (
          <div 
            key={i} 
            className="grid gap-4 p-4 border-b border-border last:border-b-0"
            style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
          >
            {Array.from({ length: columns }).map((_, j) => (
              <Skeleton key={j} className="h-4 w-full" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Page loading skeleton
export function PageLoadingSkeleton() {
  return (
    <div 
      className="min-h-screen bg-background"
      role="status"
      aria-label="Loading page content"
    >
      {/* Header skeleton */}
      <div className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col space-y-4 lg:flex-row lg:items-center lg:justify-between lg:space-y-0">
            <div>
              <Skeleton className="h-8 w-48 mb-2" aria-label="Loading page title" />
              <Skeleton className="h-4 w-64" aria-label="Loading page description" />
            </div>
            <div className="flex items-center space-x-4">
              <Skeleton className="h-5 w-20" />
              <Skeleton className="h-4 w-24" />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Department overview skeleton */}
        <div className="mb-8">
          <Skeleton className="h-6 w-48 mb-4" aria-label="Loading section title" />
          <DepartmentOverviewSkeleton />
        </div>

        {/* Main content skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-1">
            <CardSkeleton lines={8} showHeader={true} />
          </div>
          <div className="lg:col-span-2 space-y-6">
            <CardSkeleton lines={6} showHeader={true} showAction={true} />
            <CardSkeleton lines={10} showHeader={true} />
          </div>
        </div>

        {/* Footer skeleton */}
        <div className="mt-12">
          <CardSkeleton lines={4} showHeader={true} />
        </div>
      </div>
    </div>
  );
}