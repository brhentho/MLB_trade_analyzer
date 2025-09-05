/**
 * Advanced Service Worker for Baseball Trade AI
 * Implements intelligent caching, offline support, and background sync
 */

const CACHE_NAME = 'baseball-trade-ai-v1.2';
const RUNTIME_CACHE = 'runtime-cache-v1';
const DATA_CACHE = 'data-cache-v1';
const OFFLINE_URL = '/offline';

// Cache strategies configuration
const CACHE_STRATEGIES = {
  // Static assets - cache first
  STATIC_ASSETS: [
    '/_next/static/',
    '/icons/',
    '/images/',
    '/fonts/',
    '/favicon.ico',
  ],
  
  // API data - network first with fallback
  API_ENDPOINTS: [
    '/api/teams',
    '/api/health',
  ],
  
  // Analysis endpoints - network only (real-time required)
  REALTIME_ENDPOINTS: [
    '/api/analysis',
    '/api/analyze',
  ],
  
  // Pages - stale while revalidate
  PAGES: [
    '/',
    '/teams',
    '/analysis',
  ],
};

// Pre-cache critical resources
const PRECACHE_RESOURCES = [
  '/',
  '/offline',
  '/_next/static/css/',
  '/_next/static/chunks/framework',
  '/_next/static/chunks/main',
  '/_next/static/chunks/pages/',
];

// Install event - pre-cache critical resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');
  
  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        
        // Pre-cache critical resources
        const criticalResources = [
          '/',
          '/offline.html',
          '/manifest.json',
        ];
        
        await cache.addAll(criticalResources);
        console.log('[SW] Pre-cached critical resources');
        
        // Skip waiting to activate immediately
        self.skipWaiting();
      } catch (error) {
        console.error('[SW] Install failed:', error);
      }
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');
  
  event.waitUntil(
    (async () => {
      try {
        // Clean up old cache versions
        const cacheNames = await caches.keys();
        const oldCaches = cacheNames.filter(
          name => name !== CACHE_NAME && 
                 name !== RUNTIME_CACHE && 
                 name !== DATA_CACHE
        );
        
        await Promise.all(
          oldCaches.map(cacheName => {
            console.log(`[SW] Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          })
        );
        
        // Take control of all clients immediately
        await self.clients.claim();
        
        console.log('[SW] Service worker activated');
      } catch (error) {
        console.error('[SW] Activation failed:', error);
      }
    })()
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests for caching
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  event.respondWith(handleFetch(request));
});

async function handleFetch(request) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  
  try {
    // Strategy 1: Static Assets - Cache First
    if (isStaticAsset(pathname)) {
      return await cacheFirst(request, CACHE_NAME);
    }
    
    // Strategy 2: API Data - Network First with Cache Fallback
    if (isAPIEndpoint(pathname)) {
      if (isRealtimeEndpoint(pathname)) {
        // Real-time endpoints - network only
        return await networkOnly(request);
      } else {
        // Regular API - network first
        return await networkFirstWithCache(request, DATA_CACHE, 300); // 5 min cache
      }
    }
    
    // Strategy 3: Pages - Stale While Revalidate
    if (isPage(pathname)) {
      return await staleWhileRevalidate(request, RUNTIME_CACHE);
    }
    
    // Default strategy - Network first
    return await networkFirst(request);
    
  } catch (error) {
    console.error('[SW] Fetch error:', error);
    
    // Return offline page for navigation requests
    if (request.destination === 'document') {
      return await getOfflinePage();
    }
    
    // Return cached version if available
    const cachedResponse = await getCachedResponse(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return generic offline response
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable',
    });
  }
}

// Helper functions for URL classification
function isStaticAsset(pathname) {
  return CACHE_STRATEGIES.STATIC_ASSETS.some(pattern => pathname.startsWith(pattern));
}

function isAPIEndpoint(pathname) {
  return pathname.startsWith('/api/');
}

function isRealtimeEndpoint(pathname) {
  return CACHE_STRATEGIES.REALTIME_ENDPOINTS.some(pattern => pathname.startsWith(pattern));
}

function isPage(pathname) {
  return CACHE_STRATEGIES.PAGES.includes(pathname) || 
         pathname === '/' || 
         !pathname.includes('.');
}

// Cache strategies implementation
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {
    return cached;
  }
  
  const response = await fetch(request);
  if (response.ok) {
    cache.put(request, response.clone());
  }
  
  return response;
}

async function networkFirst(request, cacheName = RUNTIME_CACHE) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
      return cached;
    }
    
    throw error;
  }
}

async function networkFirstWithCache(request, cacheName, maxAge) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(cacheName);
      
      // Add timestamp for cache expiration
      const responseWithTimestamp = new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: {
          ...response.headers,
          'sw-cached-at': Date.now().toString(),
          'sw-max-age': maxAge.toString(),
        },
      });
      
      cache.put(request, responseWithTimestamp.clone());
      return response;
    }
    
    return response;
  } catch (error) {
    // Return cached version if available and not expired
    const cached = await getCachedResponseWithExpiry(request, cacheName, maxAge);
    if (cached) {
      return cached;
    }
    
    throw error;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  // Always try to fetch fresh content in background
  const networkPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.warn('[SW] Background update failed:', error);
    return null;
  });
  
  // Return cached content immediately if available
  if (cached) {
    // Don't await the network request - let it update in background
    networkPromise;
    return cached;
  }
  
  // No cached version - wait for network
  return await networkPromise;
}

async function networkOnly(request) {
  return await fetch(request);
}

async function getCachedResponse(request) {
  const caches_list = [CACHE_NAME, RUNTIME_CACHE, DATA_CACHE];
  
  for (const cacheName of caches_list) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
  }
  
  return null;
}

async function getCachedResponseWithExpiry(request, cacheName, maxAge) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (!cached) return null;
  
  const cachedAt = cached.headers.get('sw-cached-at');
  const cacheMaxAge = cached.headers.get('sw-max-age');
  
  if (cachedAt && cacheMaxAge) {
    const age = (Date.now() - parseInt(cachedAt)) / 1000;
    if (age > parseInt(cacheMaxAge)) {
      // Cache expired
      cache.delete(request);
      return null;
    }
  }
  
  return cached;
}

async function getOfflinePage() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const offlineResponse = await cache.match('/offline');
    
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // Fallback offline response
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Offline - Baseball Trade AI</title>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { 
              font-family: system-ui, sans-serif; 
              text-align: center; 
              padding: 2rem;
              background: #f9fafb;
            }
            .container {
              max-width: 400px;
              margin: 2rem auto;
              padding: 2rem;
              background: white;
              border-radius: 8px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .icon { font-size: 3rem; margin-bottom: 1rem; }
            h1 { color: #374151; margin-bottom: 1rem; }
            p { color: #6b7280; margin-bottom: 1.5rem; }
            button {
              background: #3b82f6;
              color: white;
              border: none;
              padding: 0.75rem 1.5rem;
              border-radius: 6px;
              cursor: pointer;
              font-weight: 500;
            }
            button:hover { background: #2563eb; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="icon">⚾</div>
            <h1>You're Offline</h1>
            <p>Baseball Trade AI needs an internet connection to access live MLB data and AI analysis.</p>
            <button onclick="window.location.reload()">Try Again</button>
          </div>
        </body>
      </html>
    `, {
      headers: {
        'Content-Type': 'text/html',
      },
    });
  } catch (error) {
    console.error('[SW] Failed to get offline page:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  switch (event.tag) {
    case 'trade-analysis-queue':
      event.waitUntil(processPendingTradeAnalysis());
      break;
    case 'cache-warmup':
      event.waitUntil(warmCriticalCaches());
      break;
    default:
      console.log('[SW] Unknown sync tag:', event.tag);
  }
});

async function processPendingTradeAnalysis() {
  try {
    // This would process queued trade analysis requests when back online
    console.log('[SW] Processing pending trade analysis requests');
    
    // Get pending requests from IndexedDB or local storage
    // Submit them to the backend when connection is restored
    // Notify the main thread of completion
    
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

async function warmCriticalCaches() {
  try {
    console.log('[SW] Warming critical caches');
    
    const criticalUrls = [
      '/api/teams',
      '/api/health',
    ];
    
    const cache = await caches.open(DATA_CACHE);
    
    await Promise.allSettled(
      criticalUrls.map(async (url) => {
        try {
          const response = await fetch(url);
          if (response.ok) {
            await cache.put(url, response);
            console.log(`[SW] Cached: ${url}`);
          }
        } catch (error) {
          console.error(`[SW] Failed to cache ${url}:`, error);
        }
      })
    );
  } catch (error) {
    console.error('[SW] Cache warming failed:', error);
  }
}

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_CACHE_STATS':
      getCacheStats().then(stats => {
        event.ports[0].postMessage({
          type: 'CACHE_STATS',
          payload: stats,
        });
      });
      break;
      
    case 'CLEAR_CACHE':
      clearCaches(payload?.cacheNames).then(() => {
        event.ports[0].postMessage({
          type: 'CACHE_CLEARED',
          payload: { success: true },
        });
      });
      break;
      
    case 'WARM_CACHE':
      warmCriticalCaches().then(() => {
        event.ports[0].postMessage({
          type: 'CACHE_WARMED',
          payload: { success: true },
        });
      });
      break;
      
    default:
      console.log('[SW] Unknown message type:', type);
  }
});

async function getCacheStats() {
  try {
    const cacheNames = await caches.keys();
    const stats = {};
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const keys = await cache.keys();
      stats[cacheName] = {
        size: keys.length,
        urls: keys.map(req => req.url).slice(0, 10), // First 10 URLs
      };
    }
    
    return stats;
  } catch (error) {
    console.error('[SW] Failed to get cache stats:', error);
    return {};
  }
}

async function clearCaches(cacheNames) {
  try {
    const namesToClear = cacheNames || [RUNTIME_CACHE, DATA_CACHE];
    
    await Promise.all(
      namesToClear.map(async (cacheName) => {
        const deleted = await caches.delete(cacheName);
        console.log(`[SW] Cache ${cacheName} ${deleted ? 'cleared' : 'not found'}`);
      })
    );
  } catch (error) {
    console.error('[SW] Failed to clear caches:', error);
  }
}

// Performance monitoring
let performanceMetrics = {
  cacheHits: 0,
  cacheMisses: 0,
  networkRequests: 0,
  networkFailures: 0,
};

function recordMetric(type) {
  if (performanceMetrics[type] !== undefined) {
    performanceMetrics[type]++;
  }
}

// Periodic performance reporting (every 5 minutes)
setInterval(() => {
  if (performanceMetrics.networkRequests > 0) {
    console.log('[SW] Performance metrics:', {
      ...performanceMetrics,
      cacheHitRate: (performanceMetrics.cacheHits / (performanceMetrics.cacheHits + performanceMetrics.cacheMisses)).toFixed(2),
      networkFailureRate: (performanceMetrics.networkFailures / performanceMetrics.networkRequests).toFixed(2),
    });
  }
}, 5 * 60 * 1000);

console.log('[SW] Service worker loaded successfully');