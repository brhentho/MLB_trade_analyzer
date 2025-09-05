/**
 * Performance Dashboard Component
 * Displays real-time performance metrics and system health
 */

'use client';

import { useState, useEffect, memo } from 'react';
import { 
  Activity, 
  Zap, 
  Clock, 
  MemoryStick,
  Wifi,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Monitor
} from 'lucide-react';

import { cn, formatDuration } from '@/lib/utils';
import { performanceMonitor, analyticsTracker } from '@/lib/analytics';
import { useWebVitals, useAnalytics } from '@/lib/analytics';
import { performanceMonitor as apiPerformanceMonitor } from '@/lib/optimized-api';

interface PerformanceDashboardProps {
  show?: boolean;
  onClose?: () => void;
}

const PerformanceDashboard = memo(function PerformanceDashboard({
  show = false,
  onClose,
}: PerformanceDashboardProps) {
  const [metrics, setMetrics] = useState<any>(null);
  const [apiMetrics, setApiMetrics] = useState<any>(null);
  const [webVitals, setWebVitals] = useState<any>(null);
  
  const { getPerformanceSummary } = useWebVitals();

  useEffect(() => {
    if (!show) return;

    const updateMetrics = () => {
      // Get component performance metrics
      const componentMetrics = getPerformanceSummary();
      setMetrics(componentMetrics);

      // Get API performance metrics
      const apiStats = apiPerformanceMonitor.getMetrics();
      setApiMetrics(apiStats);

      // Get analytics summary
      const analyticsData = analyticsTracker.getAnalyticsSummary();
      
      // Get memory usage
      const memoryInfo = performanceMonitor.getMemoryUsage();
      
      setWebVitals({
        memory: memoryInfo,
        analytics: analyticsData,
      });
    };

    updateMetrics();
    const interval = setInterval(updateMetrics, 5000);

    return () => clearInterval(interval);
  }, [show, getPerformanceSummary]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Monitor className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Performance Dashboard</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-theme(spacing.24))]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Component Performance */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <Activity className="h-5 w-5 text-purple-600 mr-2" />
                Component Performance
              </h3>
              
              {metrics?.componentRenders && Object.keys(metrics.componentRenders).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(metrics.componentRenders).map(([component, stats]: [string, any]) => (
                    <div key={component} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium text-gray-900 text-sm">{component}</span>
                        <span className={cn(
                          'text-xs px-2 py-1 rounded',
                          stats.averageTime > 16 
                            ? 'bg-red-100 text-red-700' 
                            : stats.averageTime > 8
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        )}>
                          {stats.averageTime.toFixed(1)}ms avg
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                        <span>Max: {stats.maxTime.toFixed(1)}ms</span>
                        <span>Renders: {stats.renderCount}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  No component performance data available
                </div>
              )}
            </div>

            {/* API Performance */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <Zap className="h-5 w-5 text-blue-600 mr-2" />
                API Performance
              </h3>
              
              {apiMetrics && Object.keys(apiMetrics).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(apiMetrics).map(([endpoint, stats]: [string, any]) => (
                    <div key={endpoint} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium text-gray-900 text-sm truncate" title={endpoint}>
                          {endpoint}
                        </span>
                        <span className={cn(
                          'text-xs px-2 py-1 rounded',
                          stats.averageTime > 2000 
                            ? 'bg-red-100 text-red-700' 
                            : stats.averageTime > 1000
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        )}>
                          {stats.averageTime.toFixed(0)}ms
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-600">
                        <span>Requests: {stats.requestCount}</span>
                        <span>Errors: {stats.errorCount}</span>
                        <span>Rate: {((1 - stats.errorRate) * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  No API performance data available
                </div>
              )}
            </div>

            {/* Memory Usage */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <MemoryStick className="h-5 w-5 text-green-600 mr-2" />
                Memory Usage
              </h3>
              
              {webVitals?.memory ? (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm">
                        <span>Used JS Heap:</span>
                        <span className="font-medium">
                          {(webVitals.memory.usedJSHeapSize / 1024 / 1024).toFixed(1)} MB
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ 
                            width: `${(webVitals.memory.usedJSHeapSize / webVitals.memory.totalJSHeapSize) * 100}%` 
                          }}
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                      <div>
                        <span>Total: {(webVitals.memory.totalJSHeapSize / 1024 / 1024).toFixed(1)} MB</span>
                      </div>
                      <div>
                        <span>Limit: {(webVitals.memory.jsHeapSizeLimit / 1024 / 1024).toFixed(1)} MB</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  Memory information not available
                </div>
              )}
            </div>

            {/* User Activity */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <BarChart3 className="h-5 w-5 text-orange-600 mr-2" />
                User Activity
              </h3>
              
              {webVitals?.analytics ? (
                <div className="space-y-3">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Total Events:</span>
                        <div className="font-medium">{webVitals.analytics.totalEvents}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Event Types:</span>
                        <div className="font-medium">{Object.keys(webVitals.analytics.eventTypes).length}</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Recent events */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Events</h4>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {webVitals.analytics.recentEvents.map((event: any, index: number) => (
                        <div key={index} className="flex justify-between items-center text-xs">
                          <span className="font-mono">{event.event}</span>
                          <span className="text-gray-500">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500 text-center py-4">
                  No user activity data available
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="mt-6 pt-6 border-t border-gray-200 flex justify-end space-x-3">
            <button
              onClick={() => {
                performanceMonitor.clearMetrics();
                analyticsTracker.getAnalyticsSummary(); // Reset analytics
                setMetrics(null);
                setApiMetrics(null);
                setWebVitals(null);
              }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded hover:bg-gray-50"
            >
              Clear Metrics
            </button>
            <button
              onClick={() => {
                const data = {
                  component_metrics: metrics,
                  api_metrics: apiMetrics,
                  web_vitals: webVitals,
                  timestamp: new Date().toISOString(),
                };
                
                const blob = new Blob([JSON.stringify(data, null, 2)], {
                  type: 'application/json',
                });
                
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `performance-report-${Date.now()}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              }}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Export Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

export default PerformanceDashboard;