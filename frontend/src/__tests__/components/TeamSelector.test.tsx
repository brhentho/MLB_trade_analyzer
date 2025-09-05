/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import TeamSelector from '../../components/TeamSelector';

// Mock team data
const mockTeams = {
  'yankees': {
    name: 'New York Yankees',
    abbrev: 'NYY',
    division: 'AL East',
    league: 'AL',
    city: 'New York',
    budget_level: 'high' as const,
    competitive_window: 'win-now' as const,
    market_size: 'large' as const,
    philosophy: 'Win championships with proven talent',
    colors: {
      primary: '#132448',
      secondary: '#C4CED4'
    }
  },
  'redsox': {
    name: 'Boston Red Sox',
    abbrev: 'BOS',
    division: 'AL East',
    league: 'AL',
    city: 'Boston',
    budget_level: 'high' as const,
    competitive_window: 'win-now' as const,
    market_size: 'large' as const,
    philosophy: 'Smart analytics-driven decisions',
    colors: {
      primary: '#BD3039',
      secondary: '#0C2340'
    }
  },
  'dodgers': {
    name: 'Los Angeles Dodgers',
    abbrev: 'LAD',
    division: 'NL West',
    league: 'NL',
    city: 'Los Angeles',
    budget_level: 'high' as const,
    competitive_window: 'win-now' as const,
    market_size: 'large' as const,
    philosophy: 'Development and smart spending',
    colors: {
      primary: '#005A9C',
      secondary: '#EF3E42'
    }
  }
};

describe('TeamSelector Component', () => {
  const mockOnTeamSelect = jest.fn();

  beforeEach(() => {
    mockOnTeamSelect.mockClear();
  });

  it('renders with no team selected initially', () => {
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    expect(screen.getByText('Select Team')).toBeInTheDocument();
    expect(screen.getByText('Choose your team to begin analysis...')).toBeInTheDocument();
  });

  it('displays selected team information', () => {
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam="yankees"
        onTeamSelect={mockOnTeamSelect}
      />
    );

    expect(screen.getByText('New York Yankees')).toBeInTheDocument();
    expect(screen.getByText('NYY')).toBeInTheDocument();
  });

  it('opens dropdown when clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    await waitFor(() => {
      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
      expect(screen.getByText('Boston Red Sox')).toBeInTheDocument();
      expect(screen.getByText('Los Angeles Dodgers')).toBeInTheDocument();
    });
  });

  it('filters teams based on search input', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    const searchInput = screen.getByPlaceholderText('Search teams...');
    await user.type(searchInput, 'yankees');

    await waitFor(() => {
      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
      expect(screen.queryByText('Boston Red Sox')).not.toBeInTheDocument();
      expect(screen.queryByText('Los Angeles Dodgers')).not.toBeInTheDocument();
    });
  });

  it('filters teams by division', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    const searchInput = screen.getByPlaceholderText('Search teams...');
    await user.type(searchInput, 'AL East');

    await waitFor(() => {
      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
      expect(screen.getByText('Boston Red Sox')).toBeInTheDocument();
      expect(screen.queryByText('Los Angeles Dodgers')).not.toBeInTheDocument();
    });
  });

  it('selects team when clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    const yankeesOption = screen.getByText('New York Yankees');
    await user.click(yankeesOption);

    expect(mockOnTeamSelect).toHaveBeenCalledWith('yankees');
  });

  it('displays team colors correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    await waitFor(() => {
      const colorIndicators = screen.getAllByTestId(/team-color-/);
      expect(colorIndicators.length).toBeGreaterThan(0);
    });
  });

  it('handles empty teams object gracefully', () => {
    render(
      <TeamSelector 
        teams={{}}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    expect(screen.getByText('Select Team')).toBeInTheDocument();
  });

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    
    // Open with Enter key
    await user.type(dropdown, '{Enter}');

    await waitFor(() => {
      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
    });

    // Navigate with arrow keys
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{Enter}');

    // Should select the second team (Red Sox)
    expect(mockOnTeamSelect).toHaveBeenCalledWith('redsox');
  });

  it('closes dropdown when clicking outside', async () => {
    const user = userEvent.setup();
    
    render(
      <div>
        <TeamSelector 
          teams={mockTeams}
          selectedTeam=""
          onTeamSelect={mockOnTeamSelect}
        />
        <div data-testid="outside-element">Outside</div>
      </div>
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    // Dropdown should be open
    await waitFor(() => {
      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
    });

    // Click outside
    const outsideElement = screen.getByTestId('outside-element');
    await user.click(outsideElement);

    // Dropdown should be closed
    await waitFor(() => {
      expect(screen.queryByText('Boston Red Sox')).not.toBeInTheDocument();
    });
  });

  it('displays loading state when teams are empty', () => {
    render(
      <TeamSelector 
        teams={{}}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    // Should show placeholder when no teams available
    expect(screen.getByText('Select Team')).toBeInTheDocument();
  });

  it('maintains accessibility standards', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    
    // Should have proper ARIA attributes
    expect(dropdown).toHaveAttribute('aria-expanded', 'false');
    expect(dropdown).toHaveAttribute('aria-haspopup', 'true');

    await user.click(dropdown);

    await waitFor(() => {
      expect(dropdown).toHaveAttribute('aria-expanded', 'true');
    });
  });

  it('shows correct team abbreviation on mobile', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam="yankees"
        onTeamSelect={mockOnTeamSelect}
      />
    );

    // On mobile, should show abbreviation
    expect(screen.getByText('NYY')).toBeInTheDocument();
  });

  it('handles special characters in search', async () => {
    const user = userEvent.setup();
    
    render(
      <TeamSelector 
        teams={mockTeams}
        selectedTeam=""
        onTeamSelect={mockOnTeamSelect}
      />
    );

    const dropdown = screen.getByRole('button');
    await user.click(dropdown);

    const searchInput = screen.getByPlaceholderText('Search teams...');
    await user.type(searchInput, 'Los Angeles');

    await waitFor(() => {
      expect(screen.getByText('Los Angeles Dodgers')).toBeInTheDocument();
      expect(screen.queryByText('New York Yankees')).not.toBeInTheDocument();
    });
  });
});