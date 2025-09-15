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
      case 'high': return 'text-green-400 bg-green-900/30';
      case 'medium': return 'text-yellow-400 bg-yellow-900/30';
      case 'low': return 'text-red-400 bg-red-900/30';
      default: return 'text-statslugger-text-muted bg-statslugger-navy-primary';
    }
  };

  const getWindowColor = (window: string) => {
    switch (window) {
      case 'win-now': return 'text-statslugger-orange-primary bg-statslugger-orange-primary/20';
      case 'retool': return 'text-purple-400 bg-purple-900/30';
      case 'rebuild': return 'text-blue-400 bg-blue-900/30';
      default: return 'text-statslugger-text-muted bg-statslugger-navy-primary';
    }
  };

  return (
    <div className="relative">
      {/* Selected Team Display / Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 border border-statslugger-navy-border rounded-lg bg-statslugger-navy-deep hover:bg-statslugger-navy-primary focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:border-statslugger-orange-primary"
      >
        <div className="flex items-center space-x-3">
          {selectedTeamData ? (
            <>
              <div 
                className="w-4 h-4 rounded-full flex-shrink-0"
                style={{ backgroundColor: selectedTeamData.colors?.primary || selectedTeamData.primary_color || '#1f2937' }}
              />
              <div className="text-left min-w-0">
                <div className="font-medium text-statslugger-text-primary truncate">{selectedTeamData.name}</div>
                <div className="text-sm text-statslugger-text-secondary truncate">{selectedTeamData.division}</div>
              </div>
            </>
          ) : (
            <div className="text-statslugger-text-muted">Select a team...</div>
          )}
        </div>
        <ChevronDown className={`h-5 w-5 text-statslugger-text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-statslugger-navy-deep border border-statslugger-navy-border rounded-lg shadow-lg max-h-96 overflow-hidden sm:max-h-80">
          {/* Search */}
          <div className="p-3 border-b border-statslugger-navy-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-statslugger-text-muted" />
              <input
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-statslugger-navy-border bg-statslugger-navy-primary text-statslugger-text-primary rounded-md focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:border-statslugger-orange-primary placeholder:text-statslugger-text-muted"
              />
            </div>
          </div>

          {/* Teams List */}
          <div className="max-h-80 overflow-y-auto">
            {Object.entries(teamsByDivision).map(([division, divisionTeams]) => (
              <div key={division}>
                <div className="px-3 py-2 text-xs font-medium text-statslugger-text-muted uppercase tracking-wider bg-statslugger-navy-primary border-b border-statslugger-navy-border">
                  {division}
                </div>
                {divisionTeams.map((team) => (
                  <button
                    key={team.key}
                    onClick={() => handleTeamSelect(team.key)}
                    className={`w-full flex items-center justify-between p-3 hover:bg-statslugger-navy-primary focus:outline-none focus:bg-statslugger-navy-primary border-b border-statslugger-navy-border/50 last:border-b-0 ${
                      selectedTeam === team.key ? 'bg-statslugger-orange-primary/20 border-l-4 border-l-statslugger-orange-primary' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-full flex-shrink-0"
                        style={{ backgroundColor: team.colors?.primary || team.primary_color || '#1f2937' }}
                      />
                      <div className="text-left min-w-0">
                        <div className="font-medium text-statslugger-text-primary truncate">{team.name}</div>
                        <div className="text-sm text-statslugger-text-secondary truncate">
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
            <div className="p-6 text-center text-statslugger-text-muted">
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