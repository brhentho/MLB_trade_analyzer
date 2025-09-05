/**
 * Global Not Found Component for App Router
 * Provides helpful navigation when users hit invalid routes
 */

import Link from 'next/link';
import { Search, Home, ArrowLeft, Users, BarChart3 } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        {/* 404 Visual */}
        <div className="mb-8">
          <div className="relative">
            {/* Baseball diamond background */}
            <div className="w-32 h-32 mx-auto bg-gradient-to-br from-green-400 to-green-600 rounded-lg transform rotate-45 opacity-20" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white rounded-full p-6 shadow-lg">
                <Search className="h-12 w-12 text-gray-400" />
              </div>
            </div>
          </div>
        </div>

        <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">
          Page Not Found
        </h2>
        <p className="text-gray-600 mb-8 leading-relaxed">
          Looks like this page struck out. The page you're looking for doesn't exist 
          or may have been moved to the trading block.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-8">
          <Link
            href="/"
            className="inline-flex items-center justify-center px-6 py-3 border border-transparent rounded-lg text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <Home className="h-4 w-4 mr-2" />
            Back to Home
          </Link>
          
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 rounded-lg text-base font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </button>
        </div>

        {/* Helpful Links */}
        <div className="border-t border-gray-200 pt-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Popular Destinations
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
            <Link
              href="/teams"
              className="flex items-center space-x-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group"
            >
              <div className="flex-shrink-0">
                <Users className="h-5 w-5 text-blue-500 group-hover:text-blue-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900 group-hover:text-blue-600">Team Rosters</div>
                <div className="text-sm text-gray-500">Browse all 30 MLB teams</div>
              </div>
            </Link>

            <Link
              href="/analysis"
              className="flex items-center space-x-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group"
            >
              <div className="flex-shrink-0">
                <BarChart3 className="h-5 w-5 text-green-500 group-hover:text-green-600" />
              </div>
              <div>
                <div className="font-medium text-gray-900 group-hover:text-green-600">Trade Analysis</div>
                <div className="text-sm text-gray-500">Start a new analysis</div>
              </div>
            </Link>
          </div>
        </div>

        {/* Search Suggestion */}
        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700">
            <strong>Pro Tip:</strong> Use the search feature on our homepage to find trade analysis, 
            team data, or specific players you're looking for.
          </p>
        </div>
      </div>
    </div>
  );
}