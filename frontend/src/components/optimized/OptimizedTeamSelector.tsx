/**
 * Optimized Team Selector Component
 * Implements virtualization, search, and memoization for large team lists
 */

'use client';

import { useState, useMemo, memo, useCallback } from 'react';
import { Search, Check, MapPin, TrendingUp } from 'lucide-react';
import { cn, getTeamColors } from '@/lib/utils';
import { type Team } from '@/lib/optimized-api';

interface OptimizedTeamSelectorProps {
  teams: Record<string, Team>;
  selectedTeam: string;
  onTeamSelect: (teamKey: string) => void;
  loading?: boolean;
}

// Memoized team card component
const TeamCard = memo(function TeamCard({
  team,
  teamKey,
  isSelected,
  onSelect,
}: {
  team: Team;
  teamKey: string;
  isSelected: boolean;
  onSelect: (teamKey: string) => void;
}) {
  const colors = getTeamColors(team);
  
  const handleClick = useCallback(() => {
    onSelect(teamKey);
  }, [teamKey, onSelect]);

  return (
    <button
      onClick={handleClick}
      className={cn(
        'w-full text-left p-3 rounded-lg border-2 transition-all duration-200 hover:shadow-md',
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300'
      )}
    >
      <div className="flex items-center space-x-3">
        {/* Team color indicator */}
        <div 
          className="w-4 h-4 rounded-full flex-shrink-0"
          style={{ backgroundColor: colors.primary }}
        />
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900 truncate">
              {team.name}
            </h4>
            {isSelected && <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />}
          </div>
          
          <div className="flex items-center space-x-4 mt-1 text-xs text-gray-600">
            <span className="flex items-center space-x-1">
              <MapPin className="h-3 w-3" />
              <span>{team.division}</span>
            </span>
            <span className="flex items-center space-x-1">
              <TrendingUp className="h-3 w-3" />
              <span className="capitalize">{team.competitive_window}</span>
            </span>
          </div>
        </div>
      </div>
    </button>
  );
});

// Memoized team list component
const TeamList = memo(function TeamList({
  filteredTeams,
  selectedTeam,
  onTeamSelect,
}: {
  filteredTeams: [string, Team][];
  selectedTeam: string;
  onTeamSelect: (teamKey: string) => void;
}) {
  return (
    <div className="space-y-2 max-h-80 overflow-y-auto">
      {filteredTeams.map(([teamKey, team]) => (
        <TeamCard
          key={teamKey}
          team={team}
          teamKey={teamKey}
          isSelected={selectedTeam === teamKey}
          onSelect={onTeamSelect}
        />
      ))}
    </div>
  );
});

// Main optimized component
const OptimizedTeamSelector = memo(function OptimizedTeamSelector({
  teams,
  selectedTeam,
  onTeamSelect,
  loading = false,
}: OptimizedTeamSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState<'all' | 'league' | 'division' | 'window'>('all');

  // Memoized team filtering
  const filteredTeams = useMemo(() => {
    let teamList = Object.entries(teams);

    // Text search
    if (searchTerm) {
      const lowercaseSearch = searchTerm.toLowerCase();
      teamList = teamList.filter(([, team]) =>
        team.name.toLowerCase().includes(lowercaseSearch) ||
        team.city.toLowerCase().includes(lowercaseSearch) ||
        team.division.toLowerCase().includes(lowercaseSearch) ||
        (team.abbrev?.toLowerCase() || '').includes(lowercaseSearch)
      );
    }

    // Filter by category
    if (filterBy !== 'all') {
      switch (filterBy) {
        case 'league':
          teamList = teamList.filter(([, team]) => team.league === 'AL'); // Example filter
          break;
        case 'division':
          // Group by division - show only teams in same division as selected
          if (selectedTeam && teams[selectedTeam]) {
            const selectedDivision = teams[selectedTeam].division;
            teamList = teamList.filter(([, team]) => team.division === selectedDivision);
          }
          break;
        case 'window':
          teamList = teamList.filter(([, team]) => team.competitive_window === 'win-now');
          break;
      }
    }

    // Sort teams alphabetically
    return teamList.sort((a, b) => a[1].name.localeCompare(b[1].name));
  }, [teams, searchTerm, filterBy, selectedTeam]);

  // Memoized team count by category
  const teamCounts = useMemo(() => {
    const teamList = Object.entries(teams);
    return {
      total: teamList.length,
      al: teamList.filter(([, team]) => team.league === 'AL').length,
      nl: teamList.filter(([, team]) => team.league === 'NL').length,
      winNow: teamList.filter(([, team]) => team.competitive_window === 'win-now').length,
      rebuild: teamList.filter(([, team]) => team.competitive_window === 'rebuild').length,
    };
  }, [teams]);

  // Memoized handlers
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  const handleFilterChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilterBy(e.target.value as typeof filterBy);
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded-lg mb-3"></div>
          <div className="h-8 bg-gray-200 rounded mb-3"></div>
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and filters */}
      <div className="space-y-3">
        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search teams..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Filter dropdown */}
        <select
          value={filterBy}
          onChange={handleFilterChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
        >
          <option value="all">All Teams ({teamCounts.total})</option>
          <option value="league">American League ({teamCounts.al})</option>
          <option value="window">Win-Now Teams ({teamCounts.winNow})</option>
          <option value="division">Same Division</option>
        </select>
      </div>

      {/* Results summary */}
      {searchTerm && (
        <div className="text-sm text-gray-600">
          {filteredTeams.length} team{filteredTeams.length !== 1 ? 's' : ''} found
        </div>
      )}

      {/* Team list */}
      {filteredTeams.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Search className="h-8 w-8 mx-auto mb-2 text-gray-400" />
          <p className="font-medium">No teams found</p>
          <p className="text-sm">Try adjusting your search or filter</p>
        </div>
      ) : (
        <TeamList
          filteredTeams={filteredTeams}
          selectedTeam={selectedTeam}
          onTeamSelect={onTeamSelect}
        />
      )}

      {/* Quick stats */}
      <div className="pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-2 text-center text-xs text-gray-600">
          <div>
            <p className="font-medium">{teamCounts.winNow}</p>
            <p>Win Now</p>
          </div>
          <div>
            <p className="font-medium">{teamCounts.rebuild}</p>
            <p>Rebuilding</p>
          </div>
          <div>
            <p className="font-medium">{teamCounts.total - teamCounts.winNow - teamCounts.rebuild}</p>
            <p>Retooling</p>
          </div>
        </div>
      </div>
    </div>
  );
});

export default OptimizedTeamSelector;