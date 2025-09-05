/**
 * Web App Manifest for Baseball Trade AI
 * Enables PWA functionality and app-like experience
 */

import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Baseball Trade AI - MLB Trade Analysis Platform',
    short_name: 'Baseball Trade AI',
    description: 'AI-powered MLB trade analysis with real-time multi-agent evaluation',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#1f2937',
    orientation: 'portrait-primary',
    scope: '/',
    icons: [
      {
        src: '/icons/icon-72x72.png',
        sizes: '72x72',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icons/icon-96x96.png',
        sizes: '96x96',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icons/icon-128x128.png',
        sizes: '128x128',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icons/icon-144x144.png',
        sizes: '144x144',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icons/icon-152x152.png',
        sizes: '152x152',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icons/icon-192x192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'maskable any',
      },
      {
        src: '/icons/icon-384x384.png',
        sizes: '384x384',
        type: 'image/png',
        purpose: 'maskable any',
      },
      {
        src: '/icons/icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable any',
      },
    ],
    categories: ['sports', 'productivity', 'utilities'],
    screenshots: [
      {
        src: '/screenshots/desktop-home.png',
        sizes: '1280x720',
        type: 'image/png',
        form_factor: 'wide',
        label: 'Baseball Trade AI - Home Screen',
      },
      {
        src: '/screenshots/mobile-analysis.png',
        sizes: '375x667',
        type: 'image/png',
        form_factor: 'narrow',
        label: 'Trade Analysis in Progress',
      },
    ],
    shortcuts: [
      {
        name: 'Quick Analysis',
        short_name: 'Analyze',
        description: 'Start a new trade analysis',
        url: '/?quick=true',
        icons: [
          {
            src: '/icons/shortcut-analyze.png',
            sizes: '96x96',
            type: 'image/png',
          },
        ],
      },
    ],
  };
}