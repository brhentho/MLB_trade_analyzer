/**
 * Analytics API Route
 * Handles performance metrics, web vitals, and custom event tracking
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

// Validation schemas
const WebVitalSchema = z.object({
  id: z.string(),
  name: z.enum(['CLS', 'FID', 'FCP', 'LCP', 'TTFB']),
  value: z.number(),
  delta: z.number(),
  rating: z.enum(['good', 'needs-improvement', 'poor']),
  timestamp: z.number(),
});

const CustomMetricSchema = z.object({
  name: z.string(),
  value: z.number(),
  tags: z.record(z.string()).optional(),
  timestamp: z.number(),
});

const AnalyticsEventSchema = z.object({
  type: z.enum(['web_vital', 'custom_metric', 'error', 'user_event']),
  data: z.any(),
  sessionId: z.string(),
  timestamp: z.number(),
  url: z.string(),
  userAgent: z.string(),
});

// In-memory storage for development (use database in production)
const analyticsStore = {
  webVitals: new Map<string, any[]>(),
  customMetrics: new Map<string, any[]>(),
  errors: new Map<string, any[]>(),
  sessions: new Map<string, any>(),
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const event = AnalyticsEventSchema.parse(body);
    
    // Store analytics data based on type
    switch (event.type) {
      case 'web_vital':
        const webVital = WebVitalSchema.parse(event.data);
        storeWebVital(event.sessionId, webVital);
        break;
        
      case 'custom_metric':
        const customMetric = CustomMetricSchema.parse(event.data);
        storeCustomMetric(event.sessionId, customMetric);
        break;
        
      case 'error':
        storeError(event.sessionId, event.data);
        break;
        
      case 'user_event':
        storeUserEvent(event.sessionId, event.data);
        break;
    }
    
    // Update session info
    updateSession(event.sessionId, {
      lastActivity: event.timestamp,
      url: event.url,
      userAgent: event.userAgent,
    });
    
    return NextResponse.json({ success: true });
    
  } catch (error) {
    console.error('Analytics processing error:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid analytics data', details: error.errors },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { error: 'Failed to process analytics data' },
      { status: 500 }
    );
  }
}

// GET endpoint for analytics dashboard
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const sessionId = searchParams.get('session');
  const type = searchParams.get('type');
  const timeframe = searchParams.get('timeframe') || '1h';
  
  try {
    if (sessionId) {
      // Get data for specific session
      return NextResponse.json({
        session: getSessionData(sessionId),
      });
    }
    
    if (type) {
      // Get aggregated data by type
      return NextResponse.json({
        data: getAggregatedData(type, timeframe),
      });
    }
    
    // Return analytics summary
    return NextResponse.json({
      summary: getAnalyticsSummary(),
      timestamp: Date.now(),
    });
    
  } catch (error) {
    console.error('Analytics retrieval error:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve analytics data' },
      { status: 500 }
    );
  }
}

// Helper functions for data storage
function storeWebVital(sessionId: string, vital: any): void {
  const vitals = analyticsStore.webVitals.get(sessionId) || [];
  vitals.push(vital);
  analyticsStore.webVitals.set(sessionId, vitals);
  
  // Log significant performance issues
  if (vital.rating === 'poor') {
    console.warn(`[Analytics] Poor ${vital.name} detected:`, vital.value);
  }
}

function storeCustomMetric(sessionId: string, metric: any): void {
  const metrics = analyticsStore.customMetrics.get(sessionId) || [];
  metrics.push(metric);
  analyticsStore.customMetrics.set(sessionId, metrics);
  
  // Log slow operations
  if (metric.name.includes('duration') && metric.value > 5000) {
    console.warn(`[Analytics] Slow operation detected: ${metric.name} = ${metric.value}ms`);
  }
}

function storeError(sessionId: string, error: any): void {
  const errors = analyticsStore.errors.get(sessionId) || [];
  errors.push(error);
  analyticsStore.errors.set(sessionId, errors);
  
  console.error(`[Analytics] Error recorded for session ${sessionId}:`, error);
}

function storeUserEvent(sessionId: string, event: any): void {
  // Store user interaction events
  const session = analyticsStore.sessions.get(sessionId) || { events: [] };
  session.events = session.events || [];
  session.events.push(event);
  analyticsStore.sessions.set(sessionId, session);
}

function updateSession(sessionId: string, data: any): void {
  const existingSession = analyticsStore.sessions.get(sessionId) || {};
  analyticsStore.sessions.set(sessionId, {
    ...existingSession,
    ...data,
  });
}

function getSessionData(sessionId: string) {
  return {
    info: analyticsStore.sessions.get(sessionId),
    webVitals: analyticsStore.webVitals.get(sessionId) || [],
    customMetrics: analyticsStore.customMetrics.get(sessionId) || [],
    errors: analyticsStore.errors.get(sessionId) || [],
  };
}

function getAggregatedData(type: string, timeframe: string) {
  const cutoffTime = getCutoffTime(timeframe);
  
  switch (type) {
    case 'web_vitals':
      return aggregateWebVitals(cutoffTime);
    case 'custom_metrics':
      return aggregateCustomMetrics(cutoffTime);
    case 'errors':
      return aggregateErrors(cutoffTime);
    default:
      return {};
  }
}

function getCutoffTime(timeframe: string): number {
  const now = Date.now();
  switch (timeframe) {
    case '1h': return now - (60 * 60 * 1000);
    case '6h': return now - (6 * 60 * 60 * 1000);
    case '24h': return now - (24 * 60 * 60 * 1000);
    case '7d': return now - (7 * 24 * 60 * 60 * 1000);
    default: return now - (60 * 60 * 1000);
  }
}

function aggregateWebVitals(cutoffTime: number) {
  const aggregated: Record<string, any> = {};
  
  analyticsStore.webVitals.forEach((vitals) => {
    vitals.forEach((vital) => {
      if (vital.timestamp > cutoffTime) {
        if (!aggregated[vital.name]) {
          aggregated[vital.name] = [];
        }
        aggregated[vital.name].push(vital.value);
      }
    });
  });
  
  // Calculate statistics
  Object.keys(aggregated).forEach(name => {
    const values = aggregated[name];
    aggregated[name] = {
      count: values.length,
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
      p95: percentile(values, 95),
    };
  });
  
  return aggregated;
}

function aggregateCustomMetrics(cutoffTime: number) {
  const aggregated: Record<string, any> = {};
  
  analyticsStore.customMetrics.forEach((metrics) => {
    metrics.forEach((metric) => {
      if (metric.timestamp > cutoffTime) {
        if (!aggregated[metric.name]) {
          aggregated[metric.name] = [];
        }
        aggregated[metric.name].push(metric.value);
      }
    });
  });
  
  // Calculate statistics
  Object.keys(aggregated).forEach(name => {
    const values = aggregated[name];
    aggregated[name] = {
      count: values.length,
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      min: Math.min(...values),
      max: Math.max(...values),
    };
  });
  
  return aggregated;
}

function aggregateErrors(cutoffTime: number) {
  const errors: any[] = [];
  
  analyticsStore.errors.forEach((sessionErrors) => {
    sessionErrors.forEach((error) => {
      if (error.timestamp > cutoffTime) {
        errors.push(error);
      }
    });
  });
  
  return {
    total: errors.length,
    byMessage: groupBy(errors, 'message'),
    recent: errors.slice(-10),
  };
}

function getAnalyticsSummary() {
  return {
    totalSessions: analyticsStore.sessions.size,
    totalWebVitals: Array.from(analyticsStore.webVitals.values()).flat().length,
    totalCustomMetrics: Array.from(analyticsStore.customMetrics.values()).flat().length,
    totalErrors: Array.from(analyticsStore.errors.values()).flat().length,
    lastActivity: getLastActivity(),
  };
}

function getLastActivity(): number {
  let lastActivity = 0;
  
  analyticsStore.sessions.forEach((session) => {
    if (session.lastActivity > lastActivity) {
      lastActivity = session.lastActivity;
    }
  });
  
  return lastActivity;
}

// Utility functions
function percentile(values: number[], p: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  
  if (lower === upper) {
    return sorted[lower];
  }
  
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}

function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const value = String(item[key]);
    groups[value] = groups[value] || [];
    groups[value].push(item);
    return groups;
  }, {} as Record<string, T[]>);
}