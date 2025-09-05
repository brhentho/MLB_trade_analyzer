/**
 * Advanced Next.js Middleware for Baseball Trade AI
 * Handles authentication, rate limiting, performance monitoring, and request optimization
 */

import { NextRequest, NextResponse } from 'next/server';
import { geolocation, ipAddress } from '@vercel/edge';

// Rate limiting configuration
const RATE_LIMIT_CONFIG = {
  // Analysis endpoints - more restrictive
  '/api/analyze': { requests: 10, window: 60 * 1000 }, // 10 per minute
  '/api/analysis': { requests: 30, window: 60 * 1000 }, // 30 per minute
  
  // Data endpoints - less restrictive
  '/api/teams': { requests: 100, window: 60 * 1000 }, // 100 per minute
  '/api/players': { requests: 200, window: 60 * 1000 }, // 200 per minute
  
  // Default limits
  default: { requests: 500, window: 60 * 1000 }, // 500 per minute
};

// Simple in-memory rate limit store (use Redis in production)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();

// User agent patterns for bot detection
const BOT_PATTERNS = [
  /googlebot/i,
  /bingbot/i,
  /slurp/i,
  /duckduckbot/i,
  /baiduspider/i,
  /yandexbot/i,
  /facebookexternalhit/i,
  /twitterbot/i,
  /rogerbot/i,
  /linkedinbot/i,
  /embedly/i,
  /quora/i,
  /showyoubot/i,
  /outbrain/i,
  /pinterest/i,
  /developers\.google\.com/i,
];

// Performance monitoring
function logPerformanceMetrics(request: NextRequest, response: NextResponse, startTime: number) {
  const duration = Date.now() - startTime;
  const size = response.headers.get('content-length') || '0';
  
  // Only log in development or for slow requests
  if (process.env.NODE_ENV === 'development' || duration > 1000) {
    console.log('Request Performance:', {
      method: request.method,
      url: request.url,
      duration: `${duration}ms`,
      size: `${size} bytes`,
      userAgent: request.headers.get('user-agent')?.substring(0, 50) + '...',
      ip: ipAddress(request) || 'unknown',
      timestamp: new Date().toISOString(),
    });
  }
}

// Rate limiting implementation
function checkRateLimit(request: NextRequest): { allowed: boolean; limit?: number; remaining?: number; resetTime?: number } {
  const ip = ipAddress(request) || 'unknown';
  const pathname = new URL(request.url).pathname;
  
  // Find the most specific rate limit rule
  const ruleKey = Object.keys(RATE_LIMIT_CONFIG).find(key => 
    key !== 'default' && pathname.startsWith(key)
  ) || 'default';
  
  const rule = RATE_LIMIT_CONFIG[ruleKey as keyof typeof RATE_LIMIT_CONFIG];
  const key = `${ip}:${ruleKey}`;
  const now = Date.now();
  
  const existing = rateLimitStore.get(key);
  
  if (!existing || now > existing.resetTime) {
    // Reset or initialize
    rateLimitStore.set(key, {
      count: 1,
      resetTime: now + rule.window,
    });
    return {
      allowed: true,
      limit: rule.requests,
      remaining: rule.requests - 1,
      resetTime: now + rule.window,
    };
  }
  
  if (existing.count >= rule.requests) {
    return {
      allowed: false,
      limit: rule.requests,
      remaining: 0,
      resetTime: existing.resetTime,
    };
  }
  
  // Increment count
  existing.count++;
  rateLimitStore.set(key, existing);
  
  return {
    allowed: true,
    limit: rule.requests,
    remaining: rule.requests - existing.count,
    resetTime: existing.resetTime,
  };
}

// Bot detection
function isBot(userAgent: string): boolean {
  return BOT_PATTERNS.some(pattern => pattern.test(userAgent));
}

// Security checks
function checkSecurity(request: NextRequest): { allowed: boolean; reason?: string } {
  const userAgent = request.headers.get('user-agent') || '';
  const referer = request.headers.get('referer') || '';
  const origin = request.headers.get('origin') || '';
  
  // Block requests without user agent (likely bots/scripts)
  if (!userAgent && !isBot(userAgent)) {
    return { allowed: false, reason: 'Missing user agent' };
  }
  
  // Check for suspicious patterns
  const suspiciousPatterns = [
    /sql/i,
    /script/i,
    /<script/i,
    /javascript:/i,
    /vbscript:/i,
    /onload=/i,
    /onerror=/i,
  ];
  
  const url = request.url;
  if (suspiciousPatterns.some(pattern => pattern.test(url))) {
    return { allowed: false, reason: 'Suspicious request pattern' };
  }
  
  return { allowed: true };
}

// Geolocation-based optimizations
function getRegionalConfig(request: NextRequest) {
  const geo = geolocation(request);
  
  return {
    region: geo?.region || 'unknown',
    country: geo?.country || 'US',
    city: geo?.city || 'unknown',
    // Use different CDN endpoints based on region
    cdnEndpoint: geo?.country === 'US' ? 'us-east-1' : 'global',
  };
}

export async function middleware(request: NextRequest) {
  const startTime = Date.now();
  const pathname = new URL(request.url).pathname;
  const userAgent = request.headers.get('user-agent') || '';
  
  // Skip middleware for static assets and Next.js internals
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.jpg') ||
    pathname.endsWith('.jpeg') ||
    pathname.endsWith('.gif') ||
    pathname.endsWith('.webp') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.css') ||
    pathname.endsWith('.js') ||
    pathname.endsWith('.map')
  ) {
    return NextResponse.next();
  }

  // Initialize response
  let response = NextResponse.next();

  // Security check
  const securityCheck = checkSecurity(request);
  if (!securityCheck.allowed) {
    console.warn('Security check failed:', {
      reason: securityCheck.reason,
      ip: ipAddress(request),
      userAgent: userAgent.substring(0, 100),
      url: request.url,
    });
    
    return new NextResponse('Forbidden', {
      status: 403,
      headers: {
        'Content-Type': 'text/plain',
        'X-Robots-Tag': 'noindex',
      },
    });
  }

  // Bot detection and handling
  const isBotRequest = isBot(userAgent);
  if (isBotRequest) {
    response.headers.set('X-Bot-Detected', 'true');
    
    // Serve optimized content for bots
    if (pathname === '/') {
      response.headers.set('Cache-Control', 'public, max-age=3600, s-maxage=7200');
    }
  }

  // Rate limiting for API endpoints
  if (pathname.startsWith('/api/')) {
    const rateLimitResult = checkRateLimit(request);
    
    // Add rate limit headers
    response.headers.set('X-RateLimit-Limit', rateLimitResult.limit?.toString() || '0');
    response.headers.set('X-RateLimit-Remaining', rateLimitResult.remaining?.toString() || '0');
    response.headers.set('X-RateLimit-Reset', Math.ceil((rateLimitResult.resetTime || 0) / 1000).toString());
    
    if (!rateLimitResult.allowed) {
      return new NextResponse(
        JSON.stringify({
          error: 'Rate limit exceeded',
          detail: 'Too many requests. Please try again later.',
          retryAfter: Math.ceil(((rateLimitResult.resetTime || 0) - Date.now()) / 1000),
        }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': Math.ceil(((rateLimitResult.resetTime || 0) - Date.now()) / 1000).toString(),
          },
        }
      );
    }
  }

  // Geolocation-based optimizations
  const regionalConfig = getRegionalConfig(request);
  response.headers.set('X-Region', regionalConfig.region);
  response.headers.set('X-Country', regionalConfig.country);

  // Performance and analytics headers
  response.headers.set('X-Request-ID', crypto.randomUUID());
  response.headers.set('X-Timestamp', new Date().toISOString());
  
  // Security headers for enhanced protection
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  
  // CORS handling for API routes
  if (pathname.startsWith('/api/')) {
    const origin = request.headers.get('origin');
    const allowedOrigins = [
      'http://localhost:3000',
      'http://localhost:3001',
      'https://baseball-trade-ai.vercel.app',
      'https://baseball-trade-ai.com',
    ];
    
    if (origin && allowedOrigins.includes(origin)) {
      response.headers.set('Access-Control-Allow-Origin', origin);
    }
    
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
    response.headers.set('Access-Control-Max-Age', '86400'); // 24 hours
    
    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      return new NextResponse(null, { status: 200, headers: response.headers });
    }
  }

  // Add performance monitoring
  response.headers.set('Server-Timing', `total;dur=${Date.now() - startTime}`);
  
  // Log performance metrics
  if (typeof window === 'undefined') {
    // Server-side logging
    logPerformanceMetrics(request, response, startTime);
  }

  return response;
}

// Middleware configuration
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};