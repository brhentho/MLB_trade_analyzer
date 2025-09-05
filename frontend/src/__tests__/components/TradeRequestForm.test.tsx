/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import TradeRequestForm from '../../components/TradeRequestForm';
import { tradeApi } from '../../lib/api';

// Mock the API
jest.mock('../../lib/api');
const mockTradeApi = tradeApi as jest.Mocked<typeof tradeApi>;

// Mock teams data
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
  }
};

describe('TradeRequestForm Component', () => {
  const mockOnAnalysisStart = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockTradeApi.analyzeTradeRequest.mockClear();
  });

  const renderForm = (props = {}) => {
    const defaultProps = {
      teams: mockTeams,
      selectedTeam: '',
      onAnalysisStart: mockOnAnalysisStart,
      onError: mockOnError,
      ...props
    };

    return render(<TradeRequestForm {...defaultProps} />);
  };

  describe('Initial Render', () => {
    it('renders form with all required elements', () => {
      renderForm();

      expect(screen.getByText('Trade Request')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/describe what your team needs/i)).toBeInTheDocument();
      expect(screen.getByText('Urgency Level')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /analyze trade/i })).toBeInTheDocument();
    });

    it('shows team selection when no team is selected', () => {
      renderForm();

      expect(screen.getByText(/select a team first/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /analyze trade/i })).toBeDisabled();
    });

    it('enables form when team is selected', () => {
      renderForm({ selectedTeam: 'yankees' });

      expect(screen.queryByText(/select a team first/i)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /analyze trade/i })).toBeEnabled();
    });

    it('displays selected team information', () => {
      renderForm({ selectedTeam: 'yankees' });

      expect(screen.getByText('New York Yankees')).toBeInTheDocument();
      expect(screen.getByText('NYY')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation error for empty request', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/trade request is required/i)).toBeInTheDocument();
      });

      expect(mockTradeApi.analyzeTradeRequest).not.toHaveBeenCalled();
    });

    it('shows validation error for request that is too short', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'SP');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/request must be at least 10 characters/i)).toBeInTheDocument();
      });
    });

    it('shows validation error for request that is too long', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      const longRequest = 'a'.repeat(1001); // Exceeds 1000 character limit
      await user.type(textarea, longRequest);

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/request must be less than 1000 characters/i)).toBeInTheDocument();
      });
    });

    it('shows character count for request field', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      expect(screen.getByText('21 / 1000')).toBeInTheDocument();
    });

    it('validates budget limit format', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      // Fill required fields first
      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher with good ERA');

      // Test invalid budget
      const budgetInput = screen.getByLabelText(/budget limit/i);
      await user.type(budgetInput, 'invalid-amount');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/budget must be a valid number/i)).toBeInTheDocument();
      });
    });

    it('validates negative budget amounts', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher with good ERA');

      const budgetInput = screen.getByLabelText(/budget limit/i);
      await user.type(budgetInput, '-5000000');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/budget must be positive/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Interactions', () => {
    it('updates urgency level selection', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const urgencySelect = screen.getByDisplayValue('Medium');
      await user.selectOptions(urgencySelect, 'high');

      expect(urgencySelect).toHaveValue('high');
    });

    it('toggles advanced options visibility', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      // Advanced options should be hidden initially
      expect(screen.queryByLabelText(/budget limit/i)).not.toBeInTheDocument();

      // Click to show advanced options
      const advancedToggle = screen.getByText(/advanced options/i);
      await user.click(advancedToggle);

      // Now advanced options should be visible
      expect(screen.getByLabelText(/budget limit/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/include prospects/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/max trade partners/i)).toBeInTheDocument();
    });

    it('handles include prospects checkbox', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      // Show advanced options first
      await user.click(screen.getByText(/advanced options/i));

      const prospectsCheckbox = screen.getByLabelText(/include prospects/i);
      expect(prospectsCheckbox).not.toBeChecked();

      await user.click(prospectsCheckbox);
      expect(prospectsCheckbox).toBeChecked();
    });

    it('validates max trade partners range', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher with good ERA');

      // Show advanced options
      await user.click(screen.getByText(/advanced options/i));

      const maxPartnersInput = screen.getByLabelText(/max trade partners/i);
      await user.clear(maxPartnersInput);
      await user.type(maxPartnersInput, '6'); // Exceeds maximum

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/maximum 5 trade partners allowed/i)).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('submits valid trade request successfully', async () => {
      const user = userEvent.setup();
      const mockAnalysisResponse = {
        analysis_id: 'test-123',
        team: 'yankees',
        original_request: 'Need a starting pitcher',
        status: 'queued',
        created_at: new Date().toISOString(),
        departments_consulted: []
      };

      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher with ERA under 4.0');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockTradeApi.analyzeTradeRequest).toHaveBeenCalledWith({
          team: 'yankees',
          request: 'Need a starting pitcher with ERA under 4.0',
          urgency: 'medium',
          budget_limit: undefined,
          include_prospects: true,
          max_trade_partners: 2
        });
      });

      expect(mockOnAnalysisStart).toHaveBeenCalledWith(mockAnalysisResponse);
    });

    it('submits request with all advanced options', async () => {
      const user = userEvent.setup();
      const mockAnalysisResponse = {
        analysis_id: 'test-456',
        team: 'redsox',
        original_request: 'Complex trade request',
        status: 'queued',
        created_at: new Date().toISOString(),
        departments_consulted: []
      };

      mockTradeApi.analyzeTradeRequest.mockResolvedValue(mockAnalysisResponse);
      
      renderForm({ selectedTeam: 'redsox' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a left-handed starting pitcher under 30 years old');

      // Set urgency
      const urgencySelect = screen.getByDisplayValue('Medium');
      await user.selectOptions(urgencySelect, 'high');

      // Show and fill advanced options
      await user.click(screen.getByText(/advanced options/i));

      const budgetInput = screen.getByLabelText(/budget limit/i);
      await user.type(budgetInput, '25000000');

      const prospectsCheckbox = screen.getByLabelText(/include prospects/i);
      await user.click(prospectsCheckbox); // Uncheck it

      const maxPartnersInput = screen.getByLabelText(/max trade partners/i);
      await user.clear(maxPartnersInput);
      await user.type(maxPartnersInput, '3');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockTradeApi.analyzeTradeRequest).toHaveBeenCalledWith({
          team: 'redsox',
          request: 'Need a left-handed starting pitcher under 30 years old',
          urgency: 'high',
          budget_limit: 25000000,
          include_prospects: false,
          max_trade_partners: 3
        });
      });
    });

    it('handles API validation errors', async () => {
      const user = userEvent.setup();
      const validationError = {
        response: {
          status: 422,
          data: {
            error: 'Validation failed',
            validation_errors: [
              {
                field: 'request',
                message: 'Request is too vague',
                type: 'invalid_content'
              }
            ]
          }
        }
      };

      mockTradeApi.analyzeTradeRequest.mockRejectedValue(validationError);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need player');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/request is too vague/i)).toBeInTheDocument();
      });

      expect(mockOnError).toHaveBeenCalledWith('Request is too vague');
    });

    it('handles team not found errors', async () => {
      const user = userEvent.setup();
      const teamNotFoundError = {
        response: {
          status: 404,
          data: {
            error: "Team 'invalid_team' not found",
            detail: "Check available teams at /api/teams"
          }
        }
      };

      mockTradeApi.analyzeTradeRequest.mockRejectedValue(teamNotFoundError);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/team.*not found/i)).toBeInTheDocument();
      });

      expect(mockOnError).toHaveBeenCalledWith("Team 'invalid_team' not found");
    });

    it('handles rate limiting errors', async () => {
      const user = userEvent.setup();
      const rateLimitError = {
        response: {
          status: 429,
          data: {
            error: 'Rate limit exceeded',
            detail: 'Please wait 60 seconds before submitting another request'
          }
        }
      };

      mockTradeApi.analyzeTradeRequest.mockRejectedValue(rateLimitError);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/rate limit exceeded/i)).toBeInTheDocument();
        expect(screen.getByText(/wait 60 seconds/i)).toBeInTheDocument();
      });

      // Button should be disabled during cooldown
      expect(submitButton).toBeDisabled();
    });

    it('handles network errors gracefully', async () => {
      const user = userEvent.setup();
      const networkError = {
        code: 'ECONNREFUSED',
        message: 'Network Error'
      };

      mockTradeApi.analyzeTradeRequest.mockRejectedValue(networkError);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
        expect(screen.getByText(/please check your connection/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state during submission', async () => {
      const user = userEvent.setup();
      
      // Create a promise that we can resolve manually
      let resolvePromise: (value: any) => void;
      const analysisPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockTradeApi.analyzeTradeRequest.mockReturnValue(analysisPromise);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
        expect(submitButton).toBeDisabled();
      });

      // Resolve the promise
      resolvePromise!({
        analysis_id: 'test-123',
        team: 'yankees',
        status: 'queued'
      });

      // Loading state should disappear
      await waitFor(() => {
        expect(screen.queryByText(/analyzing/i)).not.toBeInTheDocument();
        expect(submitButton).toBeEnabled();
      });
    });

    it('disables form during submission', async () => {
      const user = userEvent.setup();
      
      let resolvePromise: (value: any) => void;
      const analysisPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockTradeApi.analyzeTradeRequest.mockReturnValue(analysisPromise);
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      // All form elements should be disabled
      await waitFor(() => {
        expect(textarea).toBeDisabled();
        expect(submitButton).toBeDisabled();
        const urgencySelect = screen.getByDisplayValue('Medium');
        expect(urgencySelect).toBeDisabled();
      });

      // Resolve and check they're enabled again
      resolvePromise!({ analysis_id: 'test-123', team: 'yankees', status: 'queued' });

      await waitFor(() => {
        expect(textarea).toBeEnabled();
        expect(submitButton).toBeEnabled();
      });
    });
  });

  describe('User Experience', () => {
    it('clears form after successful submission', async () => {
      const user = userEvent.setup();
      mockTradeApi.analyzeTradeRequest.mockResolvedValue({
        analysis_id: 'test-123',
        team: 'yankees',
        status: 'queued'
      });
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });

    it('maintains form state when switching between teams', async () => {
      const user = userEvent.setup();
      const { rerender } = renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      // Switch teams
      rerender(
        <TradeRequestForm
          teams={mockTeams}
          selectedTeam="redsox"
          onAnalysisStart={mockOnAnalysisStart}
          onError={mockOnError}
        />
      );

      // Form content should be preserved
      expect(textarea).toHaveValue('Need a starting pitcher');
      expect(screen.getByText('Boston Red Sox')).toBeInTheDocument();
    });

    it('provides helpful placeholder text', () => {
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      const placeholderText = textarea.getAttribute('placeholder');
      
      expect(placeholderText).toContain('starting pitcher');
      expect(placeholderText).toContain('ERA under');
      expect(placeholderText).toContain('playoff');
    });

    it('shows team-specific context when available', () => {
      renderForm({ selectedTeam: 'yankees' });

      expect(screen.getByText(/yankees.*philosophy/i)).toBeInTheDocument();
      expect(screen.getByText(/win championships/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels and ARIA attributes', () => {
      renderForm({ selectedTeam: 'yankees' });

      // Check that form elements have proper labels
      expect(screen.getByLabelText(/trade request/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/urgency level/i)).toBeInTheDocument();

      // Check ARIA attributes
      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    it('announces validation errors to screen readers', async () => {
      const user = userEvent.setup();
      renderForm({ selectedTeam: 'yankees' });

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/trade request is required/i);
        expect(errorMessage).toHaveAttribute('role', 'alert');
      });
    });

    it('maintains focus management during form submission', async () => {
      const user = userEvent.setup();
      mockTradeApi.analyzeTradeRequest.mockResolvedValue({
        analysis_id: 'test-123',
        team: 'yankees',
        status: 'queued'
      });
      
      renderForm({ selectedTeam: 'yankees' });

      const textarea = screen.getByPlaceholderText(/describe what your team needs/i);
      await user.type(textarea, 'Need a starting pitcher');

      const submitButton = screen.getByRole('button', { name: /analyze trade/i });
      await user.click(submitButton);

      // After successful submission, focus should return to textarea
      await waitFor(() => {
        expect(textarea).toHaveFocus();
      });
    });
  });
});