/**
 * Service Worker registration and management hook
 */

'use client';

import { useEffect, useState, useCallback } from 'react';

interface ServiceWorkerState {
  isSupported: boolean;
  isRegistered: boolean;
  isUpdateAvailable: boolean;
  registration: ServiceWorkerRegistration | null;
  error: string | null;
}

export function useServiceWorker() {
  const [state, setState] = useState<ServiceWorkerState>({
    isSupported: false,
    isRegistered: false,
    isUpdateAvailable: false,
    registration: null,
    error: null,
  });

  const updateServiceWorker = useCallback(async () => {
    if (state.registration?.waiting) {
      state.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }, [state.registration]);

  const cacheAnalysis = useCallback((analysisId: string, data: any) => {
    if (state.registration?.active) {
      state.registration.active.postMessage({
        type: 'CACHE_ANALYSIS',
        analysisId,
        data,
      });
    }
  }, [state.registration]);

  useEffect(() => {
    // Check if service workers are supported
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      setState(prev => ({ 
        ...prev, 
        isSupported: false,
        error: 'Service Workers are not supported in this browser' 
      }));
      return;
    }

    setState(prev => ({ ...prev, isSupported: true }));

    // Register service worker
    const registerSW = async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
        });

        console.log('Service Worker registered:', registration);

        setState(prev => ({
          ...prev,
          isRegistered: true,
          registration,
          error: null,
        }));

        // Check for updates
        registration.addEventListener('updatefound', () => {
          console.log('Service Worker update found');
          const newWorker = registration.installing;
          
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.log('Service Worker update available');
                setState(prev => ({ ...prev, isUpdateAvailable: true }));
              }
            });
          }
        });

        // Handle controller changes
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          console.log('Service Worker controller changed');
          window.location.reload();
        });

      } catch (error) {
        console.error('Service Worker registration failed:', error);
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Registration failed',
        }));
      }
    };

    registerSW();

    // Handle page visibility changes for background sync
    const handleVisibilityChange = () => {
      if (!document.hidden && state.registration) {
        // Check for updates when page becomes visible
        state.registration.update();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return {
    ...state,
    updateServiceWorker,
    cacheAnalysis,
  };
}

// Hook for offline detection and handling
export function useOfflineHandler() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [showOfflineMessage, setShowOfflineMessage] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setShowOfflineMessage(false);
      console.log('App is online');
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowOfflineMessage(true);
      console.log('App is offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const hideOfflineMessage = useCallback(() => {
    setShowOfflineMessage(false);
  }, []);

  return {
    isOnline,
    showOfflineMessage,
    hideOfflineMessage,
  };
}

// Hook for background sync
export function useBackgroundSync() {
  const [isRegistered, setIsRegistered] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      navigator.serviceWorker.ready.then((registration) => {
        setIsRegistered(true);
        console.log('Background sync is supported');
      });
    }
  }, []);

  const scheduleBackgroundSync = useCallback(async (tag: string) => {
    if (!isRegistered) {
      console.warn('Background sync not available');
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register(tag);
      console.log('Background sync scheduled:', tag);
      return true;
    } catch (error) {
      console.error('Background sync failed:', error);
      return false;
    }
  }, [isRegistered]);

  return {
    isRegistered,
    scheduleBackgroundSync,
  };
}