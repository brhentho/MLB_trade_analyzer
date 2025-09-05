/**
 * Individual Team API Route Handler
 * Provides team-specific data with ISR and cache optimization
 */

import { NextRequest, NextResponse } from 'next/server';
import { serverAPI } from '@/lib/server-api';
import { z } from 'zod';

const TeamParamsSchema = z.object({
  teamKey: z.string().min(1).max(50),
});

export async function GET(
  request: NextRequest,
  { params }: { params: { teamKey: string } }
) {
  const startTime = Date.now();
  
  try {
    // Validate team key parameter
    const { teamKey } = TeamParamsSchema.parse(params);
    const endpoint = `/api/teams/${teamKey}`;
    
    // Get team data (roster and needs in parallel)
    const [rosterData, needsData] = await Promise.allSettled([
      serverAPI.teams.getRoster(teamKey),
      serverAPI.teams.getNeeds(teamKey),
    ]);

    // Process results
    const teamData: any = {
      teamKey,
      timestamp: new Date().toISOString(),
    };

    if (rosterData.status === 'fulfilled') {
      teamData.roster = rosterData.value;
    } else {
      console.warn(`Roster fetch failed for ${teamKey}:`, rosterData.reason);
      teamData.rosterError = 'Failed to load roster data';
    }

    if (needsData.status === 'fulfilled') {
      teamData.needs = needsData.value;
    } else {
      console.warn(`Needs fetch failed for ${teamKey}:`, needsData.reason);
      teamData.needsError = 'Failed to load needs analysis';
    }

    const responseTime = Date.now() - startTime;

    return NextResponse.json(teamData, {
      headers: {
        'Cache-Control': 'public, s-maxage=600, stale-while-revalidate=1800', // 10min cache, 30min stale
        'Content-Type': 'application/json',
        'X-Response-Time': `${responseTime}ms`,
        'X-Team-Key': teamKey,
      },
    });

  } catch (error) {
    console.error('Team API error:', error);
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: 'Invalid team key',
          detail: 'Team key must be a valid string',
          validation: error.errors,
        },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      {
        error: 'Failed to fetch team data',
        detail: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      {
        status: 500,
        headers: {
          'X-Response-Time': `${Date.now() - startTime}ms`,
        },
      }
    );
  }
}