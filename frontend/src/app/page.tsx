'use client';

import { useState, useEffect } from 'react';

interface Team {
  id?: number;
  team_key?: string;
  name?: string;
  abbreviation?: string;
  city?: string;
  division?: string;
  league?: string;
  budget_level?: string;
  competitive_window?: string;
  market_size?: string;
  philosophy?: string;
}

interface TeamsResponse {
  teams: Team[] | Record<string, Team>;
  total?: number;
  total_teams?: number;
  last_updated: string;
}

interface SystemHealth {
  service: string;
  version: string;
  status: string;
  endpoints: Record<string, string>;
  features: string[];
}

interface TradeAnalysis {
  team: string;
  original_request: string;
  parsed_analysis: {
    primary_need: string;
    urgency: string;
    confidence_score: number;
  };
  recommended_next_steps: string[];
}

export default function HomePage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [tradeRequest, setTradeRequest] = useState<string>('');
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysis, setAnalysis] = useState<TradeAnalysis | null>(null);
  const [error, setError] = useState<string>('');

  // Fetch system health and teams on load
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        
        // Fetch system health
        const healthResponse = await fetch('http://localhost:8000/');
        if (!healthResponse.ok) throw new Error('Backend not responding');
        const health = await healthResponse.json();
        setSystemHealth(health);

        // Fetch teams using the new API structure
        const teamsResponse = await fetch('http://localhost:8000/api/teams');
        if (!teamsResponse.ok) throw new Error('Could not load teams');
        const teamsData: TeamsResponse = await teamsResponse.json();
        // Convert teams object to array for state
        const teamsArray = Array.isArray(teamsData.teams) ? teamsData.teams : Object.values(teamsData.teams);
        setTeams(teamsArray);
        
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTeam || !tradeRequest) {
      alert('Please select a team and enter a trade request');
      return;
    }

    try {
      setAnalyzing(true);
      const response = await fetch('http://localhost:8000/api/quick-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          team: selectedTeam,
          request: tradeRequest,
          urgency: 'medium'
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');
      
      const result = await response.json();
      setAnalysis(result);
      setAnalyzing(false);
      
    } catch (err) {
      alert('Error: ' + (err instanceof Error ? err.message : 'Unknown error'));
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-300 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Baseball Trade AI...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg max-w-md">
            <strong className="font-bold">Error!</strong>
            <span className="block mt-1">{error}</span>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Baseball Trade AI
          </h1>
          <p className="text-gray-600 mb-4">
            AI-Powered MLB Trade Analysis with Multi-Agent System
          </p>
          
          {systemHealth && (
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span className="status-operational px-3 py-1 rounded-full border">
                Status: {systemHealth.status}
              </span>
              <span className="text-gray-600">
                Version: {systemHealth.version}
              </span>
              <span className="text-gray-600">
                Teams: {teams.length}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* AI Features Overview */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            AI-Powered Features
          </h2>
          {systemHealth && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {systemHealth.features.map((feature, index) => (
                <div key={index} className="trade-card">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full flex-shrink-0"></div>
                    <div>
                      <h3 className="font-medium text-gray-900 text-sm">{feature}</h3>
                      <p className="text-gray-600 text-xs">Available now</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Team Selection */}
          <div className="trade-card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Select Your Team
            </h2>
            
            <select 
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Choose a team...</option>
              {teams.map((team) => (
                <option key={team.team_key || team.id} value={team.team_key || team.abbreviation}>
                  {team.name || `${team.city} ${team.abbreviation}`}
                </option>
              ))}
            </select>
            
            {selectedTeam && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800 text-sm">
                  Selected: <strong>{teams.find(t => (t.team_key || t.abbreviation) === selectedTeam)?.name}</strong>
                </p>
                <p className="text-blue-600 text-xs mt-1">
                  Ready for AI trade analysis
                </p>
              </div>
            )}
          </div>

          {/* Trade Request Form */}
          <div className="trade-card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Trade Request
            </h2>
            
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe what you're looking for:
                </label>
                <textarea
                  value={tradeRequest}
                  onChange={(e) => setTradeRequest(e.target.value)}
                  placeholder="e.g., Find me a starting pitcher with an ERA under 4.0 and at least 3 years of team control"
                  rows={4}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
                />
              </div>
              
              <button
                type="submit"
                disabled={!selectedTeam || !tradeRequest || analyzing}
                className={`w-full py-3 px-4 rounded-md font-medium text-base transition-colors ${
                  analyzing
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                    : !selectedTeam || !tradeRequest
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
                }`}
              >
                {analyzing ? 'Analyzing Trade...' : 'Analyze Trade'}
              </button>
            </form>
          </div>
        </div>

        {/* Analysis Results */}
        {analysis && (
          <div className="mt-8 trade-card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Analysis Results
            </h2>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-2">
                Team: {analysis.team}
              </h3>
              <p className="text-gray-700 mb-4">
                <strong>Request:</strong> {analysis.original_request}
              </p>
              
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-2">
                  Parsed Analysis:
                </h4>
                <div className="space-y-1 text-sm text-gray-600">
                  <p><span className="font-medium">Primary Need:</span> {analysis.parsed_analysis.primary_need}</p>
                  <p><span className="font-medium">Urgency:</span> {analysis.parsed_analysis.urgency}</p>
                  <p><span className="font-medium">Confidence:</span> {(analysis.parsed_analysis.confidence_score * 100).toFixed(1)}%</p>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  Recommended Next Steps:
                </h4>
                <ul className="space-y-1 text-sm text-gray-600">
                  {analysis.recommended_next_steps.map((step: string, index: number) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* API Endpoints Information */}
        {systemHealth && (
          <div className="mt-8 trade-card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Available API Endpoints
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemHealth.endpoints).map(([name, endpoint]) => (
                <div key={name} className="p-3 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 text-sm mb-1">
                    {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h3>
                  <code className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    {endpoint}
                  </code>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}