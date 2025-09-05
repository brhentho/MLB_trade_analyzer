/**
 * Service Worker for Baseball Trade AI
 * Provides offline functionality and background sync
 */

const CACHE_NAME = 'baseball-trade-ai-v1';
const STATIC_CACHE_NAME = 'baseball-trade-ai-static-v1';
const DYNAMIC_CACHE_NAME = 'baseball-trade-ai-dynamic-v1';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/_next/static/css/',
  '/_next/static/js/',
];

// API endpoints to cache
const CACHEABLE_APIS = [
  '/api/teams',
  '/api/system/health',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker installing');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && 
              cacheName !== STATIC_CACHE_NAME && 
              cacheName !== DYNAMIC_CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  self.clients.claim();
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and Chrome extensions
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle different types of requests
  if (url.pathname.startsWith('/_next/static/')) {
    // Static assets - cache first with long TTL
    event.respondWith(cacheFirst(request, STATIC_CACHE_NAME, 86400000)); // 24 hours
  } else if (url.pathname.startsWith('/api/')) {
    // API requests - network first with short cache
    if (CACHEABLE_APIs.some(api => url.pathname.startsWith(api))) {
      event.respondWith(networkFirst(request, DYNAMIC_CACHE_NAME, 300000)); // 5 minutes
    } else {
      // Don't cache non-cacheable APIs
      event.respondWith(fetch(request));
    }
  } else {
    // HTML pages - network first with cache fallback
    event.respondWith(networkFirst(request, DYNAMIC_CACHE_NAME, 3600000)); // 1 hour
  }
});

// Cache first strategy - good for static assets
async function cacheFirst(request, cacheName, maxAge) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {
    const cachedDate = new Date(cached.headers.get('date') || Date.now());
    const now = new Date();
    const age = now.getTime() - cachedDate.getTime();
    
    if (age < maxAge) {
      return cached;
    }
  }
  
  try {
    const response = await fetch(request);
    if (response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    if (cached) {
      console.log('Network failed, serving stale cache for:', request.url);
      return cached;
    }
    throw error;
  }
}

// Network first strategy - good for dynamic content
async function networkFirst(request, cacheName, maxAge) {
  const cache = await caches.open(cacheName);
  
  try {
    const response = await fetch(request);
    
    if (response.status === 200) {
      // Clone and cache successful responses
      const responseClone = response.clone();
      cache.put(request, responseClone);
    }
    
    return response;
  } catch (error) {
    console.log('Network failed, trying cache for:', request.url);
    
    const cached = await cache.match(request);
    if (cached) {
      const cachedDate = new Date(cached.headers.get('date') || Date.now());
      const now = new Date();
      const age = now.getTime() - cachedDate.getTime();
      
      // Serve stale cache if not too old
      if (age < maxAge * 2) { // Allow stale for double the max age
        return cached;
      }
    }
    
    // Return offline page or error
    if (request.destination === 'document') {
      return new Response(
        createOfflinePage(),
        {
          status: 200,
          headers: { 'Content-Type': 'text/html' }
        }
      );
    }
    
    throw error;
  }
}

// Background sync for failed requests
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'background-sync-trade-analysis') {
    event.waitUntil(syncFailedRequests());
  }
});

// Sync failed trade analysis requests
async function syncFailedRequests() {
  console.log('Syncing failed trade analysis requests');
  
  // Get failed requests from IndexedDB (would need to implement storage)
  // For now, just log the sync attempt
  console.log('Background sync completed');
}

// Push notifications for analysis completion
self.addEventListener('push', (event) => {
  console.log('Push notification received');
  
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (error) {
      console.error('Failed to parse push data:', error);
    }
  }

  const options = {
    body: data.body || 'Your trade analysis is complete!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: data,
    actions: [
      {
        action: 'view',
        title: 'View Results',
        icon: '/icons/action-view.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icons/action-close.png'
      }
    ],
    tag: 'trade-analysis',
    renotify: true,
  };

  event.waitUntil(
    self.registration.showNotification('Baseball Trade AI', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  if (event.action === 'view') {
    // Open the app to view results
    event.waitUntil(
      clients.openWindow('/analysis/' + (event.notification.data?.analysisId || ''))
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Create offline page HTML
function createOfflinePage() {
  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Offline - Baseball Trade AI</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          margin: 0;
          padding: 0;
          background: #f9fafb;
          color: #374151;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
        }
        .container {
          text-align: center;
          padding: 2rem;
          max-width: 400px;
        }
        .icon {
          width: 64px;
          height: 64px;
          margin: 0 auto 1rem;
          background: #6b7280;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;
        }
        h1 {
          margin: 0 0 0.5rem;
          color: #1f2937;
        }
        p {
          margin: 0 0 1rem;
          color: #6b7280;
        }
        .button {
          background: #2563eb;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          cursor: pointer;
          font-size: 1rem;
          transition: background 0.2s;
        }
        .button:hover {
          background: #1d4ed8;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="icon">⚾</div>
        <h1>You're Offline</h1>
        <p>Please check your internet connection and try again.</p>
        <button class="button" onclick="window.location.reload()">
          Try Again
        </button>
      </div>
    </body>
    </html>
  `;
}

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_ANALYSIS') {
    // Cache analysis results for offline viewing
    const { analysisId, data } = event.data;
    caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
      const response = new Response(JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' }
      });
      cache.put(`/api/analysis/${analysisId}`, response);
    });
  }
});

console.log('Service Worker loaded');