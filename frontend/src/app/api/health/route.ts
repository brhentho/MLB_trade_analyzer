/**
 * Health Check API Route
 * Provides comprehensive application health status
 */

import { NextResponse } from 'next/server';

export async function GET() {
  const startTime = Date.now();
  
  try {
    const health = {
      service: 'Baseball Trade AI Frontend',
      status: 'operational',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV,
      region: process.env.VERCEL_REGION || 'local',
      performance: {
        totalResponseTime: Date.now() - startTime,
        memoryUsage: process.memoryUsage ? {
          heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          heapTotal: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
          external: Math.round(process.memoryUsage().external / 1024 / 1024),
        } : undefined,
      },
    };

    const statusCode = 200;

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