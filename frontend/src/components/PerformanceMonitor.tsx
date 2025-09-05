'use client';

import { useState, useEffect } from 'react';
import { tradeApi, SystemHealth } from '../lib/api';
import toast from 'react-hot-toast';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Zap, 
  Database, 
  Activity,
  BarChart,
  RefreshCw,
  Trash2 
} from 'lucide-react';

interface PerformanceStats {
  [endpoint: string]: {
    avgResponseTime: number;
    minResponseTime: number;
    maxResponseTime: number;
    requestCount: number;
    errorCount: number;
  };
}

interface BackendPerformanceStats {
  cache_stats?: {
    enabled: boolean;
    memory_cache_size: number;
    redis_available: boolean;
  };
  request_stats?: {
    [endpoint: string]: {
      avg_response_time: number;
      min_response_time: number;
      max_response_time: number;
      request_count: number;
    };
  };
  error_stats?: Record<string, number>;
}

export default function PerformanceMonitor() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [frontendStats, setFrontendStats] = useState<PerformanceStats | null>(null);
  const [backendStats, setBackendStats] = useState<BackendPerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadAllStats();
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadAllStats();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadAllStats = async () => {
    try {
      setError(null);
      
      // Load system health
      const healthData = await tradeApi.getSystemHealth();
      setHealth(healthData);
      
      // Load frontend performance stats
      const frontendPerf = tradeApi.getPerformanceStats();
      setFrontendStats(frontendPerf);
      
      // Try to load backend performance stats
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/performance`);
        if (response.ok) {
          const backendPerf = await response.json();
          setBackendStats(backendPerf);
        }
      } catch (backendErr) {
        // Backend performance endpoint might not be available
        console.warn('Backend performance stats unavailable:', backendErr);
      }
      
      setLastRefresh(new Date());
    } catch (err: any) {
      console.error('Failed to load performance stats:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearCache = async () => {
    try {
      tradeApi.clearCache();
      toast.success('Frontend cache cleared');
      
      // Try to clear backend cache if available
      try {
        await tradeApi.makeRequest(
          { method: 'POST', url: '/api/cache/clear' },
          false,
          'clear_cache'
        );
        toast.success('Backend cache cleared');
      } catch {
        // Backend cache clearing might not be available
      }
      
      loadAllStats(); // Refresh stats
    } catch (err: any) {
      toast.error('Failed to clear cache');
    }
  };

  const formatResponseTime = (time: number) => {
    return time > 1000 ? `${(time / 1000).toFixed(1)}s` : `${time.toFixed(0)}ms`;
  };

  const getHealthColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'unhealthy':
      case 'error':
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getHealthIcon = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
      case 'error':
      case 'down':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Performance Monitor</h2>
        <div className="text-gray-600">Loading performance data...</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center">
          <BarChart className="h-6 w-6 mr-2" />
          Performance Monitor
        </h2>
        <div className="flex gap-2">
          <button 
            onClick={clearCache}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200 flex items-center"
            title="Clear all caches"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Clear Cache
          </button>
          <button 
            onClick={() => setShowDetails(!showDetails)}
            className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200"
          >
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
          <button 
            onClick={loadAllStats}
            className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200 flex items-center"
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </button>
        </div>
      </div>
      
      {error ? (
        <div className="text-red-600 mb-4">
          <p className="font-medium">Connection Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      ) : null}

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="flex items-center space-x-3">
          {getHealthIcon(health?.status)}
          <div>
            <div className="font-medium text-gray-900">System Status</div>
            <div className={`text-sm capitalize ${getHealthColor(health?.status)}`}>
              {health?.status || 'Unknown'}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Activity className="h-5 w-5 text-blue-500" />
          <div>
            <div className="font-medium text-gray-900">Frontend Cache</div>
            <div className="text-sm text-gray-600">
              {frontendStats ? `${Object.keys(frontendStats).length} endpoints cached` : 'No cache data'}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <Database className="h-5 w-5 text-purple-500" />
          <div>
            <div className="font-medium text-gray-900">Backend Cache</div>
            <div className="text-sm text-gray-600">
              {backendStats?.cache_stats?.enabled 
                ? `${backendStats.cache_stats.redis_available ? 'Redis' : 'Memory'} cache`
                : 'Disabled'
              }
            </div>
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      {frontendStats && Object.keys(frontendStats).length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Frontend Performance Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-600">Total Requests</div>
              <div className="font-semibold text-lg">
                {Object.values(frontendStats).reduce((sum, stats) => sum + stats.requestCount, 0)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Total Errors</div>
              <div className="font-semibold text-lg text-red-600">
                {Object.values(frontendStats).reduce((sum, stats) => sum + stats.errorCount, 0)}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Avg Response Time</div>
              <div className="font-semibold text-lg">
                {formatResponseTime(
                  Object.values(frontendStats).reduce((sum, stats) => sum + stats.avgResponseTime, 0) /
                  Object.values(frontendStats).length
                )}
              </div>
            </div>
            <div>
              <div className="text-gray-600">Last Updated</div>
              <div className="font-semibold text-sm">
                {lastRefresh.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detailed Performance Stats */}
      {showDetails && (
        <div className="space-y-6">
          {/* Frontend Stats */}
          {frontendStats && Object.keys(frontendStats).length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Frontend API Performance</h3>
              <div className="space-y-2">
                {Object.entries(frontendStats)
                  .sort(([,a], [,b]) => b.requestCount - a.requestCount)
                  .map(([endpoint, stats]) => (
                  <div key={endpoint} className="bg-white border border-gray-200 p-3 rounded">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm text-gray-800">{endpoint}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          stats.errorCount > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}>
                          {stats.errorCount > 0 ? `${stats.errorCount} errors` : 'No errors'}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          stats.avgResponseTime > 2000 
                            ? 'bg-red-100 text-red-700' 
                            : stats.avgResponseTime > 1000 
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-green-100 text-green-700'
                        }`}>
                          {formatResponseTime(stats.avgResponseTime)}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs text-gray-600">
                      <div>Min: {formatResponseTime(stats.minResponseTime)}</div>
                      <div>Max: {formatResponseTime(stats.maxResponseTime)}</div>
                      <div>Requests: {stats.requestCount}</div>
                      <div>Success: {((stats.requestCount - stats.errorCount) / stats.requestCount * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Backend Stats */}
          {backendStats && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Backend Performance</h3>
              
              {/* Cache Stats */}
              {backendStats.cache_stats && (
                <div className="mb-4 p-3 bg-blue-50 rounded">
                  <h4 className="font-medium text-blue-900 mb-2">Cache Statistics</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-blue-700">Status:</span>
                      <span className="ml-2 font-medium">
                        {backendStats.cache_stats.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div>
                      <span className="text-blue-700">Type:</span>
                      <span className="ml-2 font-medium">
                        {backendStats.cache_stats.redis_available ? 'Redis' : 'Memory'}
                      </span>
                    </div>
                    <div>
                      <span className="text-blue-700">Memory Size:</span>
                      <span className="ml-2 font-medium">{backendStats.cache_stats.memory_cache_size}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Request Stats */}
              {backendStats.request_stats && Object.keys(backendStats.request_stats).length > 0 && (
                <div className="space-y-2">
                  {Object.entries(backendStats.request_stats).map(([endpoint, stats]) => (
                    <div key={endpoint} className="bg-white border border-gray-200 p-3 rounded">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm text-gray-800">{endpoint}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          stats.avg_response_time > 2 
                            ? 'bg-red-100 text-red-700' 
                            : stats.avg_response_time > 1 
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-green-100 text-green-700'
                        }`}>
                          {formatResponseTime(stats.avg_response_time * 1000)}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                        <div>Min: {formatResponseTime(stats.min_response_time * 1000)}</div>
                        <div>Max: {formatResponseTime(stats.max_response_time * 1000)}</div>
                        <div>Count: {stats.request_count}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Error Stats */}
              {backendStats.error_stats && Object.keys(backendStats.error_stats).length > 0 && (
                <div className="mt-4 p-3 bg-red-50 rounded">
                  <h4 className="font-medium text-red-900 mb-2">Error Statistics</h4>
                  <div className="space-y-1">
                    {Object.entries(backendStats.error_stats).map(([errorType, count]) => (
                      <div key={errorType} className="flex justify-between text-sm">
                        <span className="text-red-700">{errorType}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Export performance utilities for other components
export const usePerformanceStats = () => {
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  
  useEffect(() => {
    const loadStats = () => {
      const performanceStats = tradeApi.getPerformanceStats();
      setStats(performanceStats);
    };
    
    loadStats();
    const interval = setInterval(loadStats, 10000); // Update every 10 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  return stats;
};