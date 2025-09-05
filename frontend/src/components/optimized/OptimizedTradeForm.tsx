/**
 * Optimized Trade Request Form
 * Implements form validation, auto-save, and optimized rendering
 */

'use client';

import { useState, memo, useCallback, useMemo, useEffect } from 'react';
import { Send, Lightbulb, DollarSign, Clock, AlertCircle } from 'lucide-react';
import { z } from 'zod';
import { cn, localStorage, debounce } from '@/lib/utils';
import { LoadingButton } from '@/components/ui/loading-states';
import { type Team } from '@/lib/optimized-api';

// Form validation schema
const TradeRequestFormSchema = z.object({
  request: z.string().min(10, 'Request must be at least 10 characters').max(500, 'Request is too long'),
  urgency: z.enum(['low', 'medium', 'high']),
  budget_limit: z.number().min(0).max(1000).optional(),
});

type FormData = z.infer<typeof TradeRequestFormSchema>;

interface OptimizedTradeFormProps {
  onSubmit: (data: {
    request: string;
    urgency: 'low' | 'medium' | 'high';
    budget_limit?: number;
  }) => void;
  loading: boolean;
  selectedTeam: string;
  selectedTeamData: Team | null;
  error?: Error | null;
}

// Memoized example request component
const ExampleRequests = memo(function ExampleRequests({
  onExampleSelect,
  loading,
}: {
  onExampleSelect: (example: string) => void;
  loading: boolean;
}) {
  const examples = useMemo(() => [
    {
      text: "I need a power bat with 30+ home runs",
      category: "Offense",
      urgency: "medium" as const,
    },
    {
      text: "Find me a starting pitcher with ERA under 3.50",
      category: "Pitching",
      urgency: "high" as const,
    },
    {
      text: "Looking for a closer who can handle high leverage situations",
      category: "Bullpen",
      urgency: "high" as const,
    },
    {
      text: "Need a shortstop with good defense and some pop",
      category: "Defense",
      urgency: "medium" as const,
    },
    {
      text: "Want a veteran leader for the clubhouse",
      category: "Leadership",
      urgency: "low" as const,
    },
    {
      text: "Looking for a cost-effective utility player",
      category: "Depth",
      urgency: "low" as const,
    },
  ], []);

  return (
    <div>
      <div className="flex items-center space-x-2 mb-3">
        <Lightbulb className="h-4 w-4 text-yellow-500" />
        <span className="text-sm font-medium text-gray-700">Example Requests</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {examples.map((example, index) => (
          <button
            key={index}
            type="button"
            onClick={() => onExampleSelect(example.text)}
            className={cn(
              "text-left p-3 text-sm rounded-lg border transition-all duration-200",
              "hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500",
              "border-blue-200 text-blue-700 hover:bg-blue-50",
              loading && "opacity-50 cursor-not-allowed"
            )}
            disabled={loading}
          >
            <div className="flex justify-between items-start">
              <span className="flex-1 pr-2">&ldquo;{example.text}&rdquo;</span>
              <span className="text-xs text-blue-500 font-medium bg-blue-100 px-1 rounded">
                {example.category}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
});

// Memoized team context display
const TeamContextDisplay = memo(function TeamContextDisplay({ 
  team 
}: { 
  team: Team 
}) {
  const contextItems = useMemo(() => [
    { label: 'Philosophy', value: team.philosophy },
    { label: 'Window', value: team.competitive_window },
    { label: 'Market', value: team.market_size },
    { label: 'Budget', value: team.budget_level },
  ], [team]);

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <h4 className="font-medium text-gray-900 mb-2">
        {team.name} Context
      </h4>
      <div className="grid grid-cols-2 gap-3 text-sm">
        {contextItems.map((item) => (
          <div key={item.label}>
            <span className="font-medium text-gray-700">{item.label}:</span>
            <p className="text-gray-600 capitalize">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
});

// Main form component
const OptimizedTradeForm = memo(function OptimizedTradeForm({
  onSubmit,
  loading,
  selectedTeam,
  selectedTeamData,
  error,
}: OptimizedTradeFormProps) {
  // Form state
  const [formData, setFormData] = useState<FormData>({
    request: '',
    urgency: 'medium',
    budget_limit: undefined,
  });
  
  // Validation state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [hasInteracted, setHasInteracted] = useState(false);

  // Auto-save to localStorage
  const saveToStorage = useMemo(
    () => debounce((data: FormData) => {
      if (selectedTeam) {
        localStorage.set(`trade_form_${selectedTeam}`, data);
      }
    }, 1000),
    [selectedTeam]
  );

  // Load from localStorage when team changes
  useEffect(() => {
    if (selectedTeam) {
      const saved = localStorage.get<FormData | null>(`trade_form_${selectedTeam}`, null);
      if (saved) {
        setFormData(saved);
      }
    }
  }, [selectedTeam]);

  // Auto-save when form data changes
  useEffect(() => {
    if (hasInteracted) {
      saveToStorage(formData);
    }
  }, [formData, hasInteracted, saveToStorage]);

  // Form validation
  const validateForm = useCallback((data: FormData): Record<string, string> => {
    const errors: Record<string, string> = {};
    
    try {
      TradeRequestFormSchema.parse(data);
    } catch (error) {
      if (error instanceof z.ZodError) {
        error.errors.forEach((err) => {
          if (err.path[0]) {
            errors[err.path[0] as string] = err.message;
          }
        });
      }
    }
    
    return errors;
  }, []);

  // Real-time validation
  useEffect(() => {
    if (hasInteracted) {
      const errors = validateForm(formData);
      setValidationErrors(errors);
    }
  }, [formData, hasInteracted, validateForm]);

  // Form handlers
  const handleInputChange = useCallback(<K extends keyof FormData>(
    field: K,
    value: FormData[K]
  ) => {
    setHasInteracted(true);
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleExampleSelect = useCallback((example: string) => {
    handleInputChange('request', example);
  }, [handleInputChange]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setHasInteracted(true);
    
    const errors = validateForm(formData);
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      return;
    }

    const data = {
      request: formData.request.trim(),
      urgency: formData.urgency,
      budget_limit: formData.budget_limit ? formData.budget_limit * 1000000 : undefined,
    };

    onSubmit(data);
  }, [formData, validateForm, onSubmit]);

  // Form validation status
  const isValid = Object.keys(validationErrors).length === 0;
  const canSubmit = isValid && formData.request.trim() && selectedTeam && !loading;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Request Input */}
      <div>
        <label htmlFor="request" className="block text-sm font-medium text-gray-700 mb-2">
          What type of player are you looking for?
          <span className="text-red-500 ml-1">*</span>
        </label>
        <div className="relative">
          <textarea
            id="request"
            value={formData.request}
            onChange={(e) => handleInputChange('request', e.target.value)}
            placeholder="Describe the player you need in natural language..."
            rows={4}
            maxLength={500}
            className={cn(
              'w-full px-3 py-2 border rounded-lg resize-none transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              validationErrors.request
                ? 'border-red-300 bg-red-50'
                : 'border-gray-300',
              loading && 'opacity-50 cursor-not-allowed'
            )}
            disabled={loading}
          />
          <div className="absolute bottom-2 right-2 text-xs text-gray-500">
            {formData.request.length}/500
          </div>
        </div>
        
        {validationErrors.request && (
          <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
            <AlertCircle className="h-4 w-4" />
            <span>{validationErrors.request}</span>
          </p>
        )}
        
        <p className="mt-1 text-sm text-gray-500">
          Be specific about position, performance metrics, contract situation, or team needs
        </p>
      </div>

      {/* Example Requests */}
      <ExampleRequests
        onExampleSelect={handleExampleSelect}
        loading={loading}
      />

      {/* Advanced Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Urgency */}
        <div>
          <label htmlFor="urgency" className="block text-sm font-medium text-gray-700 mb-2">
            <Clock className="inline h-4 w-4 mr-1" />
            Urgency Level
          </label>
          <select
            id="urgency"
            value={formData.urgency}
            onChange={(e) => handleInputChange('urgency', e.target.value as FormData['urgency'])}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          >
            <option value="low">Low - Exploring options</option>
            <option value="medium">Medium - Active interest</option>
            <option value="high">High - Urgent need</option>
          </select>
        </div>

        {/* Budget Limit */}
        <div>
          <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
            <DollarSign className="inline h-4 w-4 mr-1" />
            Budget Limit (Million $)
          </label>
          <input
            id="budget"
            type="number"
            value={formData.budget_limit || ''}
            onChange={(e) => handleInputChange('budget_limit', e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder="e.g., 25"
            min="0"
            max="1000"
            step="0.1"
            className={cn(
              'w-full px-3 py-2 border rounded-lg transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              validationErrors.budget_limit 
                ? 'border-red-300 bg-red-50' 
                : 'border-gray-300',
              loading && 'opacity-50 cursor-not-allowed'
            )}
            disabled={loading}
          />
          {validationErrors.budget_limit && (
            <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
              <AlertCircle className="h-4 w-4" />
              <span>{validationErrors.budget_limit}</span>
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Optional: Maximum salary you&rsquo;re willing to take on
          </p>
        </div>
      </div>

      {/* Team Context Display */}
      {selectedTeamData && (
        <TeamContextDisplay team={selectedTeamData} />
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span className="font-medium text-red-900">Request Failed</span>
          </div>
          <p className="text-sm text-red-700 mt-1">{error.message}</p>
        </div>
      )}

      {/* Submit Button */}
      <LoadingButton
        type="submit"
        loading={loading}
        loadingText="Analyzing with AI..."
        disabled={!canSubmit}
        className={cn(
          'w-full',
          canSubmit
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        )}
        size="lg"
      >
        <Send className="h-5 w-5 mr-2" />
        Start AI Analysis
      </LoadingButton>

      {/* Validation messages */}
      <div className="text-center space-y-1">
        {!selectedTeam && (
          <p className="text-sm text-red-600">
            Please select a team first
          </p>
        )}
        
        {!isValid && hasInteracted && (
          <p className="text-sm text-orange-600">
            Please fix the errors above
          </p>
        )}
        
        {formData.request && !loading && (
          <p className="text-xs text-gray-500">
            Analysis typically takes 60-90 seconds
          </p>
        )}
      </div>

      {/* Form persistence indicator */}
      {hasInteracted && selectedTeam && (
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Form auto-saved for {selectedTeamData?.name || selectedTeam}
          </p>
        </div>
      )}
    </form>
  );
});

export default OptimizedTradeForm;