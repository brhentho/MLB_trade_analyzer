/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalysisProgress from '../../components/AnalysisProgress';
import { tradeApi } from '../../lib/api';

// Mock the API
jest.mock('../../lib/api');
const mockTradeApi = tradeApi as jest.Mocked<typeof tradeApi>;

// Mock timers for testing intervals
jest.useFakeTimers();

describe('AnalysisProgress Component', () => {
  const mockAnalysisId = 'test-analysis-123';
  const mockOnComplete = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockTradeApi.getAnalysisProgress.mockClear();
  });

  afterEach(() => {
    act(() => {
      jest.clearAllTimers();
    });
  });

  const renderProgress = (props = {}) => {
    const defaultProps = {
      analysisId: mockAnalysisId,
      onComplete: mockOnComplete,
      onError: mockOnError,
      ...props
    };

    return render(<AnalysisProgress {...defaultProps} />);
  };

  describe('Initial Render', () => {
    it('renders progress container with analysis ID', () => {
      renderProgress();

      expect(screen.getByText(/analysis.*progress/i)).toBeInTheDocument();
      expect(screen.getByText(mockAnalysisId)).toBeInTheDocument();
    });

    it('shows loading state initially', () => {
      renderProgress();

      expect(screen.getByText(/fetching.*progress/i)).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('displays all department stages', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'in_progress',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        },
        current_department: 'Scouting Department',
        estimated_remaining_time: 120
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/front office coordination/i)).toBeInTheDocument();
        expect(screen.getByText(/scouting evaluation/i)).toBeInTheDocument();
        expect(screen.getByText(/analytics review/i)).toBeInTheDocument();
        expect(screen.getByText(/business operations/i)).toBeInTheDocument();
        expect(screen.getByText(/player development/i)).toBeInTheDocument();
      });
    });
  });

  describe('Progress States', () => {
    it('shows queued status', async () => {
      const mockProgressData = {
        success: true,
        status: 'queued',
        progress: {
          coordination: 'pending',
          scouting: 'pending',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        },
        queue_position: 3,
        estimated_start_time: 45
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/queued for analysis/i)).toBeInTheDocument();
        expect(screen.getByText(/position.*3/i)).toBeInTheDocument();
        expect(screen.getByText(/estimated start.*45/i)).toBeInTheDocument();
      });
    });

    it('shows analyzing status with current department', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'in_progress',
          business: 'pending',
          development: 'pending'
        },
        current_department: 'Analytics Department',
        estimated_remaining_time: 180,
        current_task: 'Evaluating player performance metrics'
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
        expect(screen.getByText(/analytics department/i)).toBeInTheDocument();
        expect(screen.getByText(/evaluating player performance/i)).toBeInTheDocument();
        expect(screen.getByText(/3 minutes remaining/i)).toBeInTheDocument();
      });
    });

    it('shows completed status', async () => {
      const mockProgressData = {
        success: true,
        status: 'completed',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'completed',
          business: 'completed',
          development: 'completed'
        },
        completion_time: '2024-03-15T14:30:00Z',
        total_duration: 287
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/analysis complete/i)).toBeInTheDocument();
        expect(screen.getByText(/completed in.*4.*minutes/i)).toBeInTheDocument();
      });

      expect(mockOnComplete).toHaveBeenCalled();
    });

    it('shows failed status with error information', async () => {
      const mockProgressData = {
        success: true,
        status: 'failed',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'failed',
          business: 'pending',
          development: 'pending'
        },
        error_message: 'Analysis timeout in Analytics Department',
        failed_at: '2024-03-15T14:25:00Z',
        retry_available: true
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/analysis failed/i)).toBeInTheDocument();
        expect(screen.getByText(/analytics department/i)).toBeInTheDocument();
        expect(screen.getByText(/timeout/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });

  describe('Visual Progress Indicators', () => {
    it('displays progress bar with correct percentage', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'in_progress',
          business: 'pending',
          development: 'pending'
        }
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', '50'); // 2.5/5 departments = 50%
      });
    });

    it('shows step indicators with correct states', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'in_progress',
          business: 'pending',
          development: 'pending'
        }
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        // Check that completed steps are marked
        const completedSteps = screen.getAllByTestId('step-completed');
        expect(completedSteps).toHaveLength(2);

        // Check that current step is highlighted
        const currentStep = screen.getByTestId('step-in-progress');
        expect(currentStep).toBeInTheDocument();

        // Check that pending steps are shown
        const pendingSteps = screen.getAllByTestId('step-pending');
        expect(pendingSteps).toHaveLength(2);
      });
    });

    it('displays department icons correctly', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'in_progress',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        }
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByTestId('icon-coordination')).toBeInTheDocument();
        expect(screen.getByTestId('icon-scouting')).toBeInTheDocument();
        expect(screen.getByTestId('icon-analytics')).toBeInTheDocument();
        expect(screen.getByTestId('icon-business')).toBeInTheDocument();
        expect(screen.getByTestId('icon-development')).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    it('polls for progress updates automatically', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'in_progress',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        }
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      // Initial call
      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(1);
      });

      // Advance timer to trigger next poll
      act(() => {
        jest.advanceTimersByTime(5000); // 5 second polling interval
      });

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(2);
      });
    });

    it('updates progress when status changes', async () => {
      // First call - scouting in progress
      const initialProgress = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'in_progress',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        }
      };

      // Second call - analytics in progress
      const updatedProgress = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'in_progress',
          business: 'pending',
          development: 'pending'
        }
      };

      mockTradeApi.getAnalysisProgress
        .mockResolvedValueOnce(initialProgress)
        .mockResolvedValueOnce(updatedProgress);

      renderProgress();

      // Check initial state
      await waitFor(() => {
        expect(screen.getByTestId('step-in-progress')).toHaveAttribute('data-department', 'scouting');
      });

      // Advance timer
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      // Check updated state
      await waitFor(() => {
        expect(screen.getByTestId('step-in-progress')).toHaveAttribute('data-department', 'analytics');
      });
    });

    it('stops polling when analysis is complete', async () => {
      const mockProgressData = {
        success: true,
        status: 'completed',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'completed',
          business: 'completed',
          development: 'completed'
        }
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(1);
      });

      // Advance timer multiple times
      act(() => {
        jest.advanceTimersByTime(15000); // 3 polling intervals
      });

      // Should not have made additional calls since analysis is complete
      expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(1);
    });

    it('handles polling errors gracefully', async () => {
      mockTradeApi.getAnalysisProgress
        .mockResolvedValueOnce({
          success: true,
          status: 'analyzing',
          progress: { coordination: 'in_progress', scouting: 'pending', analytics: 'pending', business: 'pending', development: 'pending' }
        })
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          success: true,
          status: 'analyzing',
          progress: { coordination: 'completed', scouting: 'in_progress', analytics: 'pending', business: 'pending', development: 'pending' }
        });

      renderProgress();

      // Initial successful call
      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(1);
      });

      // First polling attempt fails
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      // Should show error state briefly
      await waitFor(() => {
        expect(screen.getByText(/connection issue/i)).toBeInTheDocument();
      });

      // Second polling attempt succeeds
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(3);
        expect(screen.queryByText(/connection issue/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors', async () => {
      const apiError = {
        response: {
          status: 404,
          data: {
            error: 'Analysis not found'
          }
        }
      };

      mockTradeApi.getAnalysisProgress.mockRejectedValue(apiError);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/analysis not found/i)).toBeInTheDocument();
      });

      expect(mockOnError).toHaveBeenCalledWith('Analysis not found');
    });

    it('handles network errors', async () => {
      const networkError = new Error('Network Error');
      networkError.code = 'ECONNREFUSED';

      mockTradeApi.getAnalysisProgress.mockRejectedValue(networkError);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/connection problem/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('shows retry button on persistent errors', async () => {
      const error = new Error('Persistent error');
      mockTradeApi.getAnalysisProgress.mockRejectedValue(error);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      // Test retry functionality
      mockTradeApi.getAnalysisProgress.mockResolvedValue({
        success: true,
        status: 'analyzing',
        progress: { coordination: 'in_progress', scouting: 'pending', analytics: 'pending', business: 'pending', development: 'pending' }
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await act(async () => {
        retryButton.click();
      });

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(2);
        expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Time Estimates', () => {
    it('displays accurate time remaining estimates', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'in_progress',
          analytics: 'pending',
          business: 'pending',
          development: 'pending'
        },
        estimated_remaining_time: 240 // 4 minutes
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/4 minutes remaining/i)).toBeInTheDocument();
      });
    });

    it('updates time estimates in real-time', async () => {
      mockTradeApi.getAnalysisProgress
        .mockResolvedValueOnce({
          success: true,
          status: 'analyzing',
          progress: { coordination: 'completed', scouting: 'in_progress', analytics: 'pending', business: 'pending', development: 'pending' },
          estimated_remaining_time: 300
        })
        .mockResolvedValueOnce({
          success: true,
          status: 'analyzing',
          progress: { coordination: 'completed', scouting: 'in_progress', analytics: 'pending', business: 'pending', development: 'pending' },
          estimated_remaining_time: 240
        });

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/5 minutes remaining/i)).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(screen.getByText(/4 minutes remaining/i)).toBeInTheDocument();
      });
    });

    it('handles very short time estimates', async () => {
      const mockProgressData = {
        success: true,
        status: 'analyzing',
        progress: {
          coordination: 'completed',
          scouting: 'completed',
          analytics: 'completed',
          business: 'completed',
          development: 'in_progress'
        },
        estimated_remaining_time: 15 // 15 seconds
      };

      mockTradeApi.getAnalysisProgress.mockResolvedValue(mockProgressData);

      renderProgress();

      await waitFor(() => {
        expect(screen.getByText(/less than a minute/i)).toBeInTheDocument();
      });
    });
  });

  describe('Component Lifecycle', () => {
    it('cleans up polling interval on unmount', () => {
      const { unmount } = renderProgress();
      
      // Start polling
      expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalled();

      // Unmount component
      unmount();

      // Advance timers - should not make additional API calls
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledTimes(1);
    });

    it('updates when analysisId prop changes', async () => {
      const { rerender } = renderProgress();

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledWith(mockAnalysisId);
      });

      // Change analysis ID
      const newAnalysisId = 'new-analysis-456';
      rerender(
        <AnalysisProgress
          analysisId={newAnalysisId}
          onComplete={mockOnComplete}
          onError={mockOnError}
        />
      );

      await waitFor(() => {
        expect(mockTradeApi.getAnalysisProgress).toHaveBeenCalledWith(newAnalysisId);
      });
    });
  });
});