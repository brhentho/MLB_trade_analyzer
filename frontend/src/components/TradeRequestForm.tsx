'use client';

import { useState } from 'react';
import { Send, Lightbulb, DollarSign, Clock } from 'lucide-react';
import { type Team } from '@/lib/api';

interface TradeRequestFormProps {
  onSubmit: (data: {
    request: string;
    urgency: 'low' | 'medium' | 'high';
    budget_limit?: number;
  }) => void;
  loading: boolean;
  selectedTeam: string;
  selectedTeamData: Team | null;
}

export default function TradeRequestForm({ 
  onSubmit, 
  loading, 
  selectedTeam, 
  selectedTeamData 
}: TradeRequestFormProps) {
  const [request, setRequest] = useState('');
  const [urgency, setUrgency] = useState<'low' | 'medium' | 'high'>('medium');
  const [budgetLimit, setBudgetLimit] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!request.trim()) {
      return;
    }

    const data = {
      request: request.trim(),
      urgency,
      budget_limit: budgetLimit ? parseFloat(budgetLimit) * 1000000 : undefined, // Convert to dollars
    };

    onSubmit(data);
  };

  const exampleRequests = [
    "I need a power bat with 30+ home runs",
    "Find me a starting pitcher with ERA under 3.50",
    "Looking for a closer who can handle high leverage situations",
    "Need a shortstop with good defense and some pop",
    "Want a veteran leader for the clubhouse",
    "Looking for a cost-effective utility player",
    "Need bullpen depth for the playoff push",
    "Find me a left-handed reliever"
  ];

  const handleExampleClick = (example: string) => {
    setRequest(example);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Request Input */}
      <div>
        <label htmlFor="request" className="block text-sm font-medium text-statslugger-text-primary mb-2">
          What type of player are you looking for?
        </label>
        <textarea
          id="request"
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          placeholder="Describe the player you need in natural language..."
          rows={4}
          className="w-full px-3 py-2 border border-statslugger-navy-border bg-statslugger-navy-deep text-statslugger-text-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:border-statslugger-orange-primary resize-none placeholder:text-statslugger-text-muted"
          disabled={loading}
        />
        <p className="mt-1 text-sm text-statslugger-text-muted">
          Be specific about position, performance metrics, contract situation, or team needs
        </p>
      </div>

      {/* Example Requests */}
      <div>
        <div className="flex items-center space-x-2 mb-3">
          <Lightbulb className="h-4 w-4 text-yellow-500" />
          <span className="text-sm font-medium text-statslugger-text-primary">Example Requests</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {exampleRequests.slice(0, 6).map((example, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleExampleClick(example)}
              className="text-left p-2 text-sm text-statslugger-orange-primary hover:text-statslugger-orange-secondary hover:bg-statslugger-orange-primary/10 rounded border border-statslugger-orange-primary/30 transition-colors"
              disabled={loading}
            >
              &ldquo;{example}&rdquo;
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Urgency */}
        <div>
          <label htmlFor="urgency" className="block text-sm font-medium text-statslugger-text-primary mb-2">
            <Clock className="inline h-4 w-4 mr-1" />
            Urgency Level
          </label>
          <select
            id="urgency"
            value={urgency}
            onChange={(e) => setUrgency(e.target.value as 'low' | 'medium' | 'high')}
            className="w-full px-3 py-2 border border-statslugger-navy-border bg-statslugger-navy-deep text-statslugger-text-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:border-statslugger-orange-primary"
            disabled={loading}
          >
            <option value="low">Low - Exploring options</option>
            <option value="medium">Medium - Active interest</option>
            <option value="high">High - Urgent need</option>
          </select>
        </div>

        {/* Budget Limit */}
        <div>
          <label htmlFor="budget" className="block text-sm font-medium text-statslugger-text-primary mb-2">
            <DollarSign className="inline h-4 w-4 mr-1" />
            Budget Limit (Million $)
          </label>
          <input
            id="budget"
            type="number"
            value={budgetLimit}
            onChange={(e) => setBudgetLimit(e.target.value)}
            placeholder="e.g., 25"
            min="0"
            step="0.1"
            className="w-full px-3 py-2 border border-statslugger-navy-border bg-statslugger-navy-deep text-statslugger-text-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:border-statslugger-orange-primary placeholder:text-statslugger-text-muted"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-statslugger-text-muted">
            Optional: Maximum salary you&rsquo;re willing to take on
          </p>
        </div>
      </div>

      {/* Team Context */}
      {selectedTeamData && (
        <div className="p-4 bg-statslugger-navy-primary rounded-lg border border-statslugger-navy-border">
          <h4 className="text-sm font-medium text-statslugger-text-primary mb-2">
            {selectedTeamData.name} Context
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Philosophy:</span>
              <p className="text-statslugger-text-secondary">{selectedTeamData.philosophy}</p>
            </div>
            <div>
              <span className="font-medium">Window:</span>
              <p className="text-statslugger-text-secondary capitalize">{selectedTeamData.competitive_window}</p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || !request.trim() || !selectedTeam}
        className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
          loading || !request.trim() || !selectedTeam
            ? 'bg-statslugger-navy-border text-statslugger-text-muted cursor-not-allowed'
            : 'bg-gradient-to-r from-statslugger-orange-primary to-statslugger-orange-secondary text-white hover:from-statslugger-orange-secondary hover:to-statslugger-orange-dark hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-statslugger-orange-primary focus:ring-offset-2 focus:ring-offset-statslugger-navy-primary'
        }`}
      >
        {loading ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Analyzing with AI...</span>
          </>
        ) : (
          <>
            <Send className="h-5 w-5" />
            <span>Start AI Analysis</span>
          </>
        )}
      </button>

      {!selectedTeam && (
        <p className="text-center text-sm text-red-400">
          Please select a team first
        </p>
      )}
    </form>
  );
}