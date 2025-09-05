/**
 * Robots.txt configuration for Baseball Trade AI
 */

import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: [
        '/api/',
        '/admin/',
        '/_next/',
        '/private/',
        '/internal/',
        '/analysis/*/raw', // Don't index raw analysis data
      ],
    },
    sitemap: 'https://baseball-trade-ai.com/sitemap.xml',
  };
}