/**
 * Health Check API Route
 * Provides comprehensive application health status
 */

import { NextResponse } from 'next/server';
import { serverAPI } from '@/lib/server-api';

export async function GET() {
  const startTime = Date.now();
  
  try {
    // Parallel health checks
    const [backendHealth, teamsCheck] = await Promise.allSettled([
      serverAPI.health.check(),
      serverAPI.teams.getAll(),
    ]);

    const health = {
      service: 'Baseball Trade AI Frontend',
      status: 'operational',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV,
      region: process.env.VERCEL_REGION || 'local',
      checks: {
        backend: {
          status: backendHealth.status === 'fulfilled' ? 'healthy' : 'unhealthy',
          responseTime: Date.now() - startTime,
          ...(backendHealth.status === 'fulfilled' && backendHealth.value),
          ...(backendHealth.status === 'rejected' && {
            error: backendHealth.reason?.message || 'Backend unreachable',
          }),
        },
        database: {
          status: teamsCheck.status === 'fulfilled' ? 'healthy' : 'unhealthy',
          teamsCount: teamsCheck.status === 'fulfilled' 
            ? (Array.isArray(teamsCheck.value?.data) ? teamsCheck.value.data.length : 0)
            : 0,
          ...(teamsCheck.status === 'rejected' && {
            error: teamsCheck.reason?.message || 'Database unreachable',
          }),
        },
      },
      performance: {
        totalResponseTime: Date.now() - startTime,
        memoryUsage: process.memoryUsage ? {
          heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          heapTotal: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
          external: Math.round(process.memoryUsage().external / 1024 / 1024),
        } : undefined,
      },
    };

    // Determine overall status
    const allHealthy = Object.values(health.checks).every(check => check.status === 'healthy');
    health.status = allHealthy ? 'operational' : 'degraded';

    const statusCode = allHealthy ? 200 : 503;

    return NextResponse.json(health, {
      status: statusCode,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json',
        'X-Health-Check': 'true',
        'X-Response-Time': `${Date.now() - startTime}ms`,
      },
    });

  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json({
      service: 'Baseball Trade AI Frontend',
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Health check failed',
      performance: {
        totalResponseTime: Date.now() - startTime,
      },
    }, {
      status: 500,
      headers: {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'X-Health-Check': 'true',
        'X-Response-Time': `${Date.now() - startTime}ms`,
      },
    });
  }
}