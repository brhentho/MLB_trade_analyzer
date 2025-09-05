'use client';

import { useState } from 'react';
import { Search, ChevronDown } from 'lucide-react';
import { type Team } from '@/lib/api';

interface TeamSelectorProps {
  teams: Record<string, Team>;
  selectedTeam: string;
  onTeamSelect: (teamKey: string) => void;
}

export default function TeamSelector({ teams, selectedTeam, onTeamSelect }: TeamSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  // Convert teams object to array and add keys
  const teamsArray = Object.entries(teams).map(([key, team]) => ({
    key,
    ...team
  }));

  // Filter teams based on search term
  const filteredTeams = teamsArray.filter(team =>
    team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    team.city.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (team.abbrev && team.abbrev.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (team.abbreviation && team.abbreviation.toLowerCase().includes(searchTerm.toLowerCase())) ||
    team.division.toLowerCase().includes(searchTerm.toLowerCase()) ||
    team.league.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group teams by division for better organization
  const teamsByDivision = filteredTeams.reduce((acc, team) => {
    if (!acc[team.division]) {
      acc[team.division] = [];
    }
    acc[team.division].push(team);
    return acc;
  }, {} as Record<string, typeof teamsArray>);

  const selectedTeamData = selectedTeam ? teams[selectedTeam] : null;

  const handleTeamSelect = (teamKey: string) => {
    onTeamSelect(teamKey);
    setIsOpen(false);
    setSearchTerm('');
  };

  const getBudgetColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-green-600 bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getWindowColor = (window: string) => {
    switch (window) {
      case 'win-now': return 'text-blue-600 bg-blue-50';
      case 'retool': return 'text-purple-600 bg-purple-50';
      case 'rebuild': return 'text-orange-600 bg-orange-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="relative">
      {/* Selected Team Display / Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <div className="flex items-center space-x-3">
          {selectedTeamData ? (
            <>
              <div 
                className="w-4 h-4 rounded-full flex-shrink-0"
                style={{ backgroundColor: selectedTeamData.colors?.primary || selectedTeamData.primary_color || '#1f2937' }}
              />
              <div className="text-left min-w-0">
                <div className="font-medium text-gray-900 truncate">{selectedTeamData.name}</div>
                <div className="text-sm text-gray-500 truncate">{selectedTeamData.division}</div>
              </div>
            </>
          ) : (
            <div className="text-gray-500">Select a team...</div>
          )}
        </div>
        <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-hidden sm:max-h-80">
          {/* Search */}
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Teams List */}
          <div className="max-h-80 overflow-y-auto">
            {Object.entries(teamsByDivision).map(([division, divisionTeams]) => (
              <div key={division}>
                <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">
                  {division}
                </div>
                {divisionTeams.map((team) => (
                  <button
                    key={team.key}
                    onClick={() => handleTeamSelect(team.key)}
                    className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                      selectedTeam === team.key ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: team.colors?.primary || team.primary_color || '#1f2937' }}
                      />
                      <div className="text-left min-w-0">
                        <div className="font-medium text-gray-900 truncate">{team.name}</div>
                        <div className="text-sm text-gray-500 truncate">
                          {team.city} • {team.abbrev || team.abbreviation}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
                      <span className={`px-1 sm:px-2 py-1 text-xs font-medium rounded-full ${getBudgetColor(team.budget_level)}`}>
                        <span className="sm:hidden">{team.budget_level.charAt(0).toUpperCase()}</span>
                        <span className="hidden sm:inline">{team.budget_level}</span>
                      </span>
                      <span className={`px-1 sm:px-2 py-1 text-xs font-medium rounded-full ${getWindowColor(team.competitive_window)}`}>
                        <span className="sm:hidden">
                          {team.competitive_window === 'win-now' ? 'W' : team.competitive_window === 'retool' ? 'R' : 'B'}
                        </span>
                        <span className="hidden sm:inline">{team.competitive_window}</span>
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            ))}
          </div>

          {filteredTeams.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              No teams found matching &ldquo;{searchTerm}&rdquo;
            </div>
          )}
        </div>
      )}

      {/* Overlay to close dropdown */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}