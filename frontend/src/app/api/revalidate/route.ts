/**
 * Cache Revalidation API Route
 * Provides on-demand revalidation for ISR content
 */

import { NextRequest, NextResponse } from 'next/server';
import { revalidateTag, revalidatePath } from 'next/cache';
import { CACHE_TAGS } from '@/lib/server-api';

// Revalidation secret for security - SECURE IMPLEMENTATION
const REVALIDATION_SECRET = process.env.REVALIDATION_SECRET;

// Fail fast if secret is not configured in production
if (!REVALIDATION_SECRET && process.env.NODE_ENV === 'production') {
  throw new Error('REVALIDATION_SECRET environment variable is required in production');
}

// Use fallback only in development
const SECRET_TO_USE = REVALIDATION_SECRET || (
  process.env.NODE_ENV === 'development' 
    ? 'dev-' + crypto.randomUUID() 
    : (() => { throw new Error('REVALIDATION_SECRET required'); })()
);

export async function POST(request: NextRequest) {
  try {
    // Verify secret
    const secret = request.nextUrl.searchParams.get('secret');
    if (secret !== SECRET_TO_USE) {
      return NextResponse.json(
        { error: 'Invalid secret' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { type, targets } = body;

    switch (type) {
      case 'teams':
        revalidateTag(CACHE_TAGS.teams);
        if (targets?.length) {
          targets.forEach((teamKey: string) => {
            revalidateTag(`team-${teamKey}`);
          });
        }
        break;

      case 'team':
        if (!targets?.length) {
          return NextResponse.json(
            { error: 'Team key required' },
            { status: 400 }
          );
        }
        targets.forEach((teamKey: string) => {
          revalidateTag(`team-${teamKey}`);
          revalidateTag(CACHE_TAGS.TEAM_ROSTER);
          revalidateTag(CACHE_TAGS.TEAM_NEEDS);
        });
        break;

      case 'player':
        if (!targets?.length) {
          return NextResponse.json(
            { error: 'Player name required' },
            { status: 400 }
          );
        }
        targets.forEach((playerName: string) => {
          revalidateTag(`player-${playerName}`);
          revalidateTag(CACHE_TAGS.PLAYER_STATS);
        });
        break;

      case 'system':
        revalidateTag(CACHE_TAGS.SYSTEM_HEALTH);
        break;

      case 'all':
        // Revalidate all cache tags
        Object.values(CACHE_TAGS).forEach(tag => {
          revalidateTag(tag);
        });
        // Also revalidate paths
        revalidatePath('/');
        revalidatePath('/teams');
        revalidatePath('/analysis');
        break;

      case 'path':
        if (!targets?.length) {
          return NextResponse.json(
            { error: 'Path required' },
            { status: 400 }
          );
        }
        targets.forEach((path: string) => {
          revalidatePath(path);
        });
        break;

      default:
        return NextResponse.json(
          { error: 'Invalid revalidation type' },
          { status: 400 }
        );
    }

    return NextResponse.json({
      success: true,
      type,
      targets,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Revalidation error:', error);
    return NextResponse.json(
      { error: 'Revalidation failed' },
      { status: 500 }
    );
  }
}

export async function GET() {
  // Health check endpoint
  return NextResponse.json({
    service: 'revalidation',
    status: 'operational',
    timestamp: new Date().toISOString(),
    availableTypes: ['teams', 'team', 'player', 'system', 'all', 'path'],
  });
}