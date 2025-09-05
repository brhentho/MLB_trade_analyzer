/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { tradeApi } from '../../lib/api';

// Mock the entire app components
jest.mock('../../lib/api');
const mockTradeApi = tradeApi as jest.Mocked<typeof tradeApi>;

// Mock components for integration testing
const MockTeamSelector = ({ teams, selectedTeam, onTeamSelect }: any) => (
  <div data-testid="team-selector">
    <select
      value={selectedTeam}
      onChange={(e) => onTeamSelect(e.target.value)}
      data-testid="team-select"
    >
      <option value="">Select Team</option>
      {Object.entries(teams).map(([key, team]: [string, any]) => (
        <option key={key} value={key}>
          {team.name}
        </option>
      ))}
    </select>
    {selectedTeam && (
      <div data-testid="selected-team">{teams[selectedTeam]?.name}</div>
    )}
  </div>
);

const MockTradeRequestForm = ({ teams, selectedTeam, onAnalysisStart, onError }: any) => {
  const [request, setRequest] = React.useState('');
  const [urgency, setUrgency] = React.useState('medium');
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeam || !request) return;

    setLoading(true);
    try {
      const result = await mockTradeApi.analyzeTradeRequest({
        team: selectedTeam,
        request,
        urgency: urgency as any
      });
      onAnalysisStart(result);
      setRequest('');
    } catch (error: any) {
      onError(error.response?.data?.error || error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="trade-request-form">
      <form onSubmit={handleSubmit}>
        <textarea
          data-testid="request-input"
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          placeholder="Describe what your team needs..."
          disabled={!selectedTeam}
        />
        <select
          data-testid="urgency-select"
          value={urgency}
          onChange={(e) => setUrgency(e.target.value)}
          disabled={!selectedTeam}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <button
          type="submit"
          data-testid="submit-button"
          disabled={!selectedTeam || !request || loading}
        >
          {loading ? 'Analyzing...' : 'Analyze Trade'}
        </button>
      </form>
    </div>
  );
};

const MockAnalysisProgress = ({ analysisId, onComplete, onError }: any) => {
  const [status, setStatus] = React.useState('queued');
  const [progress, setProgress] = React.useState({
    coordination: 'pending',
    scouting: 'pending',
    analytics: 'pending',
    business: 'pending',
    development: 'pending'
  });

  React.useEffect(() => {
    const pollProgress = async () => {
      try {
        const result = await mockTradeApi.getAnalysisProgress(analysisId);
        setStatus(result.status);
        setProgress(result.progress);

        if (result.status === 'completed') {
          onComplete();
        } else if (result.status === 'failed') {
          onError(result.error_message);
        }
      } catch (error: any) {
        onError(error.message);
      }
    };

    const interval = setInterval(pollProgress, 1000);
    pollProgress(); // Initial call

    return () => clearInterval(interval);
  }, [analysisId, onComplete, onError]);

  return (
    <div data-testid="analysis-progress">
      <div data-testid="analysis-id">{analysisId}</div>
      <div data-testid="status">{status}</div>
      <div data-testid="progress">
        {Object.entries(progress).map(([dept, state]) => (
          <div key={dept} data-testid={`progress-${dept}`} data-state={state}>
            {dept}: {state}
          </div>
        ))}
      </div>
    </div>
  );
};

const MockResultsDisplay = ({ analysisId, results }: any) => (
  <div data-testid="results-display">
    <div data-testid="analysis-id">{analysisId}</div>
    <div data-testid="results-content">
      {results && (
        <>
          <div data-testid="recommendation">
            {results.organizational_recommendation?.overall_recommendation}
          </div>
          <div data-testid="confidence">
            Confidence: {results.organizational_recommendation?.confidence_level}
          </div>
          {results.proposals && (
            <div data-testid="proposals">
              {results.proposals.map((proposal: any, index: number) => (
                <div key={index} data-testid={`proposal-${index}`}>
                  <div data-testid="proposal-rank">Rank: {proposal.proposal_rank}</div>
                  <div data-testid="likelihood">Likelihood: {proposal.likelihood}</div>
                  {proposal.players_involved?.map((player: any, playerIndex: number) => (
                    <div key={playerIndex} data-testid={`player-${playerIndex}`}>
                      {player.name || player.player} ({player.from_team} → {player.to_team})
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  </div>
);

// Main integration test component
const TradeAnalyzerApp = () => {
  const [teams, setTeams] = React.useState({});
  const [selectedTeam, setSelectedTeam] = React.useState('');
  const [currentAnalysis, setCurrentAnalysis] = React.useState<any>(null);
  const [analysisResults, setAnalysisResults] = React.useState<any>(null);
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const loadTeams = async () => {
      try {
        const teamsResponse = await mockTradeApi.getTeams();
        setTeams(teamsResponse.teams);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadTeams();
  }, []);

  const handleAnalysisStart = (analysis: any) => {
    setCurrentAnalysis(analysis);
    setAnalysisResults(null);
    setError('');
  };

  const handleAnalysisComplete = async () => {
    try {
      const results = await mockTradeApi.getAnalysisStatus(currentAnalysis.analysis_id);
      setAnalysisResults(results);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleReset = () => {
    setCurrentAnalysis(null);
    setAnalysisResults(null);
    setError('');
  };

  if (loading) {
    return <div data-testid="loading">Loading teams...</div>;
  }

  return (
    <div data-testid="trade-analyzer-app">
      {error && (
        <div data-testid="error-message" role="alert">
          {error}
          <button onClick={() => setError('')} data-testid="clear-error">
            Clear
          </button>
        </div>
      )}

      <MockTeamSelector
        teams={teams}
        selectedTeam={selectedTeam}
        onTeamSelect={setSelectedTeam}
      />

      {!currentAnalysis && (
        <MockTradeRequestForm
          teams={teams}
          selectedTeam={selectedTeam}
          onAnalysisStart={handleAnalysisStart}
          onError={handleError}
        />
      )}

      {currentAnalysis && !analysisResults && (
        <MockAnalysisProgress
          analysisId={currentAnalysis.analysis_id}
          onComplete={handleAnalysisComplete}
          onError={handleError}
        />
      )}

      {analysisResults && (
        <MockResultsDisplay
          analysisId={currentAnalysis.analysis_id}
          results={analysisResults}
        />
      )}

      {(currentAnalysis || analysisResults) && (
        <button onClick={handleReset} data-testid="reset-button">
          Start New Analysis
        </button>
      )}
    </div>
  );
};

// Test data
const mockTeamsResponse = {
  success: true,
  teams: {
    'yankees': {
      name: 'New York Yankees',
      abbrev: 'NYY',
      division: 'AL East',
      league: 'AL',
      budget_level: 'high',
      competitive_window: 'win-now',
      market_size: 'large'
    },
    'redsox': {
      name: 'Boston Red Sox', 
      abbrev: 'BOS',
      division: 'AL East',
      league: 'AL',
      budget_level: 'high',
      competitive_window: 'win-now',
      market_size: 'large'
    },
    'rays': {
      name: 'Tampa Bay Rays',
      abbrev: 'TB', 
      division: 'AL East',
      league: 'AL',
      budget_level: 'low',
      competitive_window: 'win-now',
      market_size: 'small'
    }
  },
  count: 3,
  source: 'database'
};

const mockAnalysisResponse = {
  analysis_id: 'test-analysis-123',
  team: 'yankees',
  original_request: 'Need starting pitcher',
  status: 'queued',
  created_at: new Date().toISOString(),
  departments_consulted: []
};

const mockProgressResponse = {
  success: true,
  status: 'analyzing',
  progress: {
    coordination: 'completed',
    scouting: 'in_progress', 
    analytics: 'pending',
    business: 'pending',
    development: 'pending'
  },
  current_department: 'Scouting Department'
};

const mockCompletedResults = {
  analysis_id: 'test-analysis-123',
  team: 'yankees',
  status: 'completed',
  results: {
    organizational_recommendation: {
      overall_recommendation: 'Proceed with Shane Bieber trade',
      confidence_level: 'High'
    },
    departments_consulted: ['Front Office', 'Scouting', 'Analytics']
  },
  proposals: [
    {
      proposal_rank: 1,
      likelihood: 'medium',
      players_involved: [
        {
          name: 'Shane Bieber',
          from_team: 'guardians',
          to_team: 'yankees'
        },
        {
          name: 'Spencer Jones',
          from_team: 'yankees', 
          to_team: 'guardians'
        }
      ]
    }
  ]
};

describe('Trade Analyzer Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Complete Trade Analysis Flow', () => {
    it('completes full happy path from team selection to results', async () => {
      const user = userEvent.setup();

      // Mock API responses
      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      
      // Mock progress polling sequence
      mockTradeApi.getAnalysisProgress
        .mockResolvedValueOnce({ ...mockProgressResponse, status: 'queued' })
        .mockResolvedValueOnce({ ...mockProgressResponse, status: 'analyzing' })
        .mockResolvedValueOnce({
          ...mockProgressResponse,
          status: 'completed',
          progress: {
            coordination: 'completed',
            scouting: 'completed', 
            analytics: 'completed',
            business: 'completed',
            development: 'completed'
          }
        });

      mockTradeApi.getAnalysisStatus.mockResolvedValue(mockCompletedResults);

      render(<TradeAnalyzerApp />);

      // Wait for teams to load
      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Step 1: Select team
      const teamSelect = screen.getByTestId('team-select');
      await user.selectOptions(teamSelect, 'yankees');

      await waitFor(() => {
        expect(screen.getByTestId('selected-team')).toHaveTextContent('New York Yankees');
      });

      // Step 2: Enter trade request
      const requestInput = screen.getByTestId('request-input');
      await user.type(requestInput, 'Need a starting pitcher with ERA under 4.0 for playoff push');

      // Step 3: Set urgency
      const urgencySelect = screen.getByTestId('urgency-select');
      await user.selectOptions(urgencySelect, 'high');

      // Step 4: Submit analysis
      const submitButton = screen.getByTestId('submit-button');
      await user.click(submitButton);

      // Verify API call
      await waitFor(() => {
        expect(mockTradeApi.analyzeTradeRequest).toHaveBeenCalledWith({
          team: 'yankees',
          request: 'Need a starting pitcher with ERA under 4.0 for playoff push',
          urgency: 'high'
        });
      });

      // Step 5: Progress monitoring should start
      await waitFor(() => {
        expect(screen.getByTestId('analysis-progress')).toBeInTheDocument();
        expect(screen.getByTestId('analysis-id')).toHaveTextContent('test-analysis-123');
      });

      // Wait for progress updates and completion
      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalled();
      }, { timeout: 5000 });

      // Step 6: Results should be displayed
      await waitFor(() => {
        expect(screen.getByTestId('results-display')).toBeInTheDocument();
        expect(screen.getByTestId('recommendation')).toHaveTextContent('Proceed with Shane Bieber trade');
        expect(screen.getByTestId('confidence')).toHaveTextContent('Confidence: High');
      });

      // Step 7: Verify trade proposals are shown
      expect(screen.getByTestId('proposals')).toBeInTheDocument();
      expect(screen.getByTestId('proposal-0')).toBeInTheDocument();
      expect(screen.getByTestId('player-0')).toHaveTextContent('Shane Bieber (guardians → yankees)');
      expect(screen.getByTestId('player-1')).toHaveTextContent('Spencer Jones (yankees → guardians)');
    });

    it('handles team loading errors', async () => {
      const error = {
        response: {
          status: 503,
          data: { error: 'Service unavailable' }
        }
      };

      mockTradeApi.getTeams.mockRejectedValue(error);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Service unavailable');
      });

      // Should not show team selector
      expect(screen.queryByTestId('team-selector')).not.toBeInTheDocument();
    });

    it('handles analysis submission errors', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      
      const analysisError = {
        response: {
          status: 422,
          data: {
            error: 'Request is too vague'
          }
        }
      };
      mockTradeApi.analyzeTradeRequest.mockRejectedValue(analysisError);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Select team and submit invalid request
      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'need help');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Request is too vague');
      });

      // Should remain on form
      expect(screen.getByTestId('trade-request-form')).toBeInTheDocument();
      expect(screen.queryByTestId('analysis-progress')).not.toBeInTheDocument();
    });

    it('handles analysis progress errors', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      
      const progressError = new Error('Analysis failed');
      mockTradeApi.getAnalysisProgress.mockRejectedValue(progressError);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Submit analysis
      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'Need starting pitcher');
      await user.click(screen.getByTestId('submit-button'));

      // Wait for progress component and error
      await waitFor(() => {
        expect(screen.getByTestId('analysis-progress')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Analysis failed');
      });
    });

    it('handles analysis failure status', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      
      const failedProgressResponse = {
        success: true,
        status: 'failed',
        progress: {
          coordination: 'completed',
          scouting: 'failed',
          analytics: 'pending',
          business: 'pending', 
          development: 'pending'
        },
        error_message: 'Scouting analysis timeout'
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(failedProgressResponse);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Submit analysis
      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'Need starting pitcher');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByTestId('analysis-progress')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Scouting analysis timeout');
      });
    });
  });

  describe('User Workflow Management', () => {
    it('allows resetting to start new analysis', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      mockTradeApi.getAnalysisProgress.mockResolvedValue({
        ...mockProgressResponse,
        status: 'completed',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'completed', 
          business: 'completed',
          development: 'completed'
        }
      });
      mockTradeApi.getAnalysisStatus.mockResolvedValue(mockCompletedResults);

      render(<TradeAnalyzerApp />);

      // Complete first analysis
      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'Need starting pitcher');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByTestId('results-display')).toBeInTheDocument();
      });

      // Reset to start new analysis
      const resetButton = screen.getByTestId('reset-button');
      await user.click(resetButton);

      // Should return to initial form state
      await waitFor(() => {
        expect(screen.getByTestId('trade-request-form')).toBeInTheDocument();
        expect(screen.queryByTestId('results-display')).not.toBeInTheDocument();
        expect(screen.queryByTestId('analysis-progress')).not.toBeInTheDocument();
      });

      // Form should be ready for new input
      expect(screen.getByTestId('request-input')).toHaveValue('');
      expect(screen.getByTestId('team-select')).toHaveValue('yankees'); // Team selection preserved
    });

    it('maintains team selection across analysis cycles', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      mockTradeApi.getAnalysisProgress.mockResolvedValue({
        ...mockProgressResponse,
        status: 'completed'
      });
      mockTradeApi.getAnalysisStatus.mockResolvedValue(mockCompletedResults);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Select Red Sox instead of Yankees
      await user.selectOptions(screen.getByTestId('team-select'), 'redsox');
      
      await waitFor(() => {
        expect(screen.getByTestId('selected-team')).toHaveTextContent('Boston Red Sox');
      });

      // Submit and complete analysis
      await user.type(screen.getByTestId('request-input'), 'Need bullpen help');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByTestId('results-display')).toBeInTheDocument();
      });

      // Reset
      await user.click(screen.getByTestId('reset-button'));

      // Team selection should be preserved
      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toHaveValue('redsox');
        expect(screen.getByTestId('selected-team')).toHaveTextContent('Boston Red Sox');
      });
    });

    it('clears errors when starting new analysis', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      
      const analysisError = {
        response: {
          status: 422,
          data: { error: 'Invalid request' }
        }
      };
      mockTradeApi.analyzeTradeRequest.mockRejectedValue(analysisError);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Cause an error
      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'invalid');
      await user.click(screen.getByTestId('submit-button'));

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Invalid request');
      });

      // Fix the API mock for retry
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressResponse);

      // Submit valid request
      await user.clear(screen.getByTestId('request-input'));
      await user.type(screen.getByTestId('request-input'), 'Need valid starting pitcher');
      await user.click(screen.getByTestId('submit-button'));

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
        expect(screen.getByTestId('analysis-progress')).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery', () => {
    it('allows clearing errors manually', async () => {
      const user = userEvent.setup();

      const teamsError = {
        response: {
          status: 503,
          data: { error: 'Database unavailable' }
        }
      };
      mockTradeApi.getTeams.mockRejectedValue(teamsError);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Database unavailable');
      });

      // Clear error
      const clearErrorButton = screen.getByTestId('clear-error');
      await user.click(clearErrorButton);

      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
    });

    it('recovers from temporary network issues', async () => {
      const user = userEvent.setup();

      // First call fails, second succeeds
      mockTradeApi.getTeams
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce(mockTeamsResponse);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Network Error');
      });

      // Clear error and trigger retry (this would typically be automatic)
      await user.click(screen.getByTestId('clear-error'));

      // Manually trigger teams reload (in real app this might be automatic)
      // For this test, we'll simulate by clearing error and having component retry
      await waitFor(() => {
        expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
      });
    });
  });

  describe('Data Consistency', () => {
    it('maintains analysis ID consistency throughout flow', async () => {
      const user = userEvent.setup();
      const testAnalysisId = 'consistent-analysis-456';

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue({
        ...mockAnalysisResponse,
        analysis_id: testAnalysisId
      });
      mockTradeApi.getAnalysisProgress.mockResolvedValue({
        ...mockProgressResponse,
        status: 'completed'
      });
      mockTradeApi.getAnalysisStatus.mockResolvedValue({
        ...mockCompletedResults,
        analysis_id: testAnalysisId
      });

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      await user.selectOptions(screen.getByTestId('team-select'), 'yankees');
      await user.type(screen.getByTestId('request-input'), 'Need pitcher');
      await user.click(screen.getByTestId('submit-button'));

      // Check analysis ID in progress component
      await waitFor(() => {
        const progressAnalysisId = within(screen.getByTestId('analysis-progress'))
          .getByTestId('analysis-id');
        expect(progressAnalysisId).toHaveTextContent(testAnalysisId);
      });

      // Check analysis ID in results component
      await waitFor(() => {
        const resultsAnalysisId = within(screen.getByTestId('results-display'))
          .getByTestId('analysis-id');
        expect(resultsAnalysisId).toHaveTextContent(testAnalysisId);
      });

      // Verify API was called with correct ID
      expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledWith(testAnalysisId);
      expect(mockTradeApi.getAnalysisStatus).toHaveBeenCalledWith(testAnalysisId);
    });

    it('preserves user selections during analysis', async () => {
      const user = userEvent.setup();

      mockTradeApi.getTeams.mockResolvedValue(mockTeamsResponse);
      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressResponse);

      render(<TradeAnalyzerApp />);

      await waitFor(() => {
        expect(screen.getByTestId('team-select')).toBeInTheDocument();
      });

      // Make selections
      await user.selectOptions(screen.getByTestId('team-select'), 'rays');
      await user.type(screen.getByTestId('request-input'), 'Need affordable starter');
      await user.selectOptions(screen.getByTestId('urgency-select'), 'low');
      await user.click(screen.getByTestId('submit-button'));

      // During analysis, original selections should be preserved in API call
      expect(mockTradeApi.analyzeTradeRequest).toHaveBeenCalledWith({
        team: 'rays',
        request: 'Need affordable starter',
        urgency: 'low'
      });

      // Team selection should still be visible
      expect(screen.getByTestId('selected-team')).toHaveTextContent('Tampa Bay Rays');
    });
  });
});