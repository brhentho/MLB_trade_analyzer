/**
 * API exports for compatibility with existing components
 */

export {
  type Team,
  type Player,
  type TradeAnalysis,
  type TradeProposal
} from './optimized-api';

export type AnalysisProgress = {
  stage: string;
  progress: number;
  currentTask?: string;
  error?: string;
  completed_departments: string[];
  current_department?: string;
  estimated_remaining_time?: number;
};

export type TradeRecommendation = {
  id: string;
  title: string;
  description: string;
  teams_involved: any;
  players_involved: any;
  likelihood: 'low' | 'medium' | 'high';
  financial_impact?: any;
  risk_assessment?: any;
};

export type SystemHealth = {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    database: 'online' | 'offline';
    llm: 'online' | 'offline';
    cache: 'online' | 'offline';
  };
  performance: {
    response_time: number;
    memory_usage: number;
    cpu_usage: number;
  };
};

// Mock trade API implementation for components
export const tradeApi = {
  async getAnalysisProgress(analysisId: string): Promise<AnalysisProgress> {
    // Mock implementation
    return {
      stage: 'analyzing',
      progress: 0.5,
      currentTask: 'Evaluating trade proposal',
      completed_departments: ['Front Office Leadership'],
      current_department: 'Scouting Department',
    };
  },

  async getAnalysisStatus(analysisId: string): Promise<TradeAnalysis> {
    // Mock implementation - this should be replaced with actual API calls
    throw new Error('Not implemented - replace with actual API call');
  },

  async getSystemHealth(): Promise<SystemHealth> {
    // Mock implementation
    return {
      status: 'healthy',
      services: {
        database: 'online',
        llm: 'online', 
        cache: 'online',
      },
      performance: {
        response_time: 150,
        memory_usage: 0.45,
        cpu_usage: 0.25,
      },
    };
  },

  getPerformanceStats() {
    return {
      requests: 0,
      errors: 0,
      avgResponseTime: 0,
    };
  },

  clearCache() {
    // Mock implementation
  },

  async makeRequest(endpoint: string, options?: any) {
    // Mock implementation for performance testing
    return { status: 200, data: {} };
  },
};