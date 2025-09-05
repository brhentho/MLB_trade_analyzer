'use client';

import { CheckCircle, AlertCircle, Clock, Zap, Database, Activity } from 'lucide-react';

interface SystemStatusProps {
  systemHealth: {
    status?: string;
    agents?: number;
    database_status?: string;
    version?: string;
    performance?: {
      avg_response_time?: string;
      uptime?: string;
    };
  } | null;
}

export default function SystemStatus({ systemHealth }: SystemStatusProps) {
  if (!systemHealth) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <div className="flex items-center space-x-2">
          <Clock className="h-5 w-5 text-gray-400" />
          <span className="text-gray-600">Loading system status...</span>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      case 'down':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Overall Status */}
        <div className="flex items-center space-x-3">
          {getStatusIcon(systemHealth.status || 'unknown')}
          <div>
            <div className="font-medium text-gray-900">System</div>
            <div className={`text-sm capitalize ${getStatusColor(systemHealth.status || 'unknown')}`}>
              {systemHealth.status || 'Unknown'}
            </div>
          </div>
        </div>

        {/* AI Agents */}
        <div className="flex items-center space-x-3">
          <Activity className="h-5 w-5 text-blue-500" />
          <div>
            <div className="font-medium text-gray-900">AI Agents</div>
            <div className="text-sm text-gray-600">
              {systemHealth.agents || 0} active
            </div>
          </div>
        </div>

        {/* Database */}
        <div className="flex items-center space-x-3">
          <Database className="h-5 w-5 text-purple-500" />
          <div>
            <div className="font-medium text-gray-900">Database</div>
            <div className="text-sm text-gray-600">
              {systemHealth.database_status || 'Connected'}
            </div>
          </div>
        </div>
      </div>

      {/* Additional Details */}
      {systemHealth.version && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>Version: {systemHealth.version}</span>
            <div className="flex items-center space-x-1">
              <Zap className="h-4 w-4" />
              <span>Cost Optimized</span>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {systemHealth.performance && (
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Avg Response Time:</span>
            <span className="ml-2 font-medium">{systemHealth.performance.avg_response_time || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-600">Uptime:</span>
            <span className="ml-2 font-medium">{systemHealth.performance.uptime || 'N/A'}</span>
          </div>
        </div>
      )}
    </div>
  );
}