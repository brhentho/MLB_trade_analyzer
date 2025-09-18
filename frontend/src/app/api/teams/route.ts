/**
 * Teams API Route Handler
 * Provides cached team data with proper error handling and validation
 */

import { NextResponse } from 'next/server';

// Response time logging
function logResponseTime(startTime: number, endpoint: string) {
  const duration = Date.now() - startTime;
  if (duration > 1000) {
    console.warn(`Slow API response: ${endpoint} took ${duration}ms`);
  }
}

export async function GET() {
  const startTime = Date.now();
  const endpoint = '/api/teams';

  try {
    // Mock teams data for now
    const teamsData = {
      success: true,
      data: [
        { id: 'nyy', name: 'New York Yankees', division: 'AL East' },
        { id: 'bos', name: 'Boston Red Sox', division: 'AL East' },
      ]
    };
    
    logResponseTime(startTime, endpoint);
    
    return NextResponse.json(teamsData, {
      headers: {
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
        'Content-Type': 'application/json',
        'X-Response-Time': `${Date.now() - startTime}ms`,
      },
    });

  } catch (error) {
    console.error('Teams API error:', error);
    logResponseTime(startTime, endpoint);
    
    return NextResponse.json(
      {
        error: 'Failed to fetch teams',
        detail: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'X-Response-Time': `${Date.now() - startTime}ms`,
        },
      }
    );
  }
}