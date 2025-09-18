/**
 * Optimized API types and utilities
 */

export interface Team {
  id: number;
  team_key: string;
  name: string;
  abbreviation: string;
  city: string;
  division: string;
  league: string;
  primary_color?: string;
  secondary_color?: string;
  budget_level?: 'low' | 'medium' | 'high';
  competitive_window?: 'rebuild' | 'retool' | 'win-now';
  market_size?: 'small' | 'medium' | 'large';
  philosophy?: string;
}

export interface Player {
  id: number;
  name: string;
  team_id: number;
  position: string;
  age?: number;
  salary?: number;
  contract_years?: number;
  war?: number;
  stats?: any;
}

export interface TradeAnalysis {
  id: string;
  analysis_id: string;
  requesting_team_id: number;
  request_text: string;
  urgency: 'low' | 'medium' | 'high';
  status: 'queued' | 'analyzing' | 'completed' | 'error';
  progress?: any;
  results?: any;
  cost_info?: any;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  team?: string;
  original_request?: string;
}

export interface TradeProposal {
  id: number;
  analysis_id: number;
  proposal_rank: number;
  teams_involved: any;
  players_involved: any;
  likelihood: 'low' | 'medium' | 'high';
  financial_impact?: any;
  risk_assessment?: any;
}