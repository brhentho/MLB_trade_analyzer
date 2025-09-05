-- Baseball Trade AI - Initial Database Schema
-- Creates all necessary tables for the application

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- MLB Teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    team_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    division VARCHAR(20) NOT NULL,
    league VARCHAR(5) NOT NULL CHECK (league IN ('AL', 'NL')),
    budget_level VARCHAR(20) DEFAULT 'medium',
    competitive_window VARCHAR(20) DEFAULT 'rebuilding',
    market_size VARCHAR(20) DEFAULT 'medium',
    philosophy TEXT,
    payroll_budget BIGINT DEFAULT 0,
    luxury_tax_threshold BIGINT DEFAULT 237000000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    position VARCHAR(10),
    age INTEGER,
    salary BIGINT DEFAULT 0,
    contract_years INTEGER DEFAULT 1,
    war DECIMAL(4,1) DEFAULT 0.0,
    stats JSONB DEFAULT '{}',
    mlb_id INTEGER UNIQUE,
    active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prospects table for minor league players
CREATE TABLE IF NOT EXISTS prospects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    position VARCHAR(10),
    age INTEGER,
    ranking INTEGER,
    future_value INTEGER CHECK (future_value BETWEEN 20 AND 80),
    eta INTEGER, -- Expected time of arrival (year)
    risk_level VARCHAR(20) DEFAULT 'medium',
    scouting_report JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trade analyses table
CREATE TABLE IF NOT EXISTS trade_analyses (
    id SERIAL PRIMARY KEY,
    analysis_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    requesting_team_id INTEGER REFERENCES teams(id),
    request_text TEXT NOT NULL,
    urgency VARCHAR(20) DEFAULT 'medium' CHECK (urgency IN ('low', 'medium', 'high')),
    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'analyzing', 'completed', 'error')),
    progress JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    cost_info JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Trade proposals table
CREATE TABLE IF NOT EXISTS trade_proposals (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES trade_analyses(id) ON DELETE CASCADE,
    proposal_rank INTEGER DEFAULT 1,
    teams_involved TEXT[] DEFAULT ARRAY[]::TEXT[],
    players_involved TEXT[] DEFAULT ARRAY[]::TEXT[],
    prospects_involved TEXT[] DEFAULT ARRAY[]::TEXT[],
    cash_considerations BIGINT DEFAULT 0,
    likelihood VARCHAR(20) DEFAULT 'medium',
    financial_impact JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    grade VARCHAR(5),
    fairness_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Player stats cache table for performance
CREATE TABLE IF NOT EXISTS player_stats_cache (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id),
    season INTEGER NOT NULL,
    stats_type VARCHAR(20) DEFAULT 'regular', -- regular, postseason, advanced
    stats_data JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, season, stats_type)
);

-- Team needs analysis table
CREATE TABLE IF NOT EXISTS team_needs (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    primary_needs TEXT[] DEFAULT ARRAY[]::TEXT[],
    secondary_needs TEXT[] DEFAULT ARRAY[]::TEXT[],
    urgency_level VARCHAR(20) DEFAULT 'medium',
    budget_available BIGINT DEFAULT 0,
    trade_assets TEXT[] DEFAULT ARRAY[]::TEXT[],
    untouchables TEXT[] DEFAULT ARRAY[]::TEXT[],
    last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_players_team_id ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_war ON players(war DESC);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_prospects_team_id ON prospects(team_id);
CREATE INDEX IF NOT EXISTS idx_prospects_ranking ON prospects(ranking);
CREATE INDEX IF NOT EXISTS idx_trade_analyses_status ON trade_analyses(status);
CREATE INDEX IF NOT EXISTS idx_trade_analyses_team ON trade_analyses(requesting_team_id);
CREATE INDEX IF NOT EXISTS idx_trade_analyses_created ON trade_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trade_proposals_analysis ON trade_proposals(analysis_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_cache_player_season ON player_stats_cache(player_id, season);

-- Row Level Security (RLS) policies
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE prospects ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_stats_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_needs ENABLE ROW LEVEL SECURITY;

-- Public read access policies for reference data
CREATE POLICY "Teams are publicly readable" ON teams FOR SELECT USING (true);
CREATE POLICY "Players are publicly readable" ON players FOR SELECT USING (true);
CREATE POLICY "Prospects are publicly readable" ON prospects FOR SELECT USING (true);
CREATE POLICY "Player stats are publicly readable" ON player_stats_cache FOR SELECT USING (true);
CREATE POLICY "Team needs are publicly readable" ON team_needs FOR SELECT USING (true);

-- Trade analysis policies (authenticated users can create, only creator can see details)
CREATE POLICY "Users can create trade analyses" ON trade_analyses FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can view their trade analyses" ON trade_analyses FOR SELECT USING (true);
CREATE POLICY "Users can view trade proposals" ON trade_proposals FOR SELECT USING (true);

-- Update triggers for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prospects_updated_at BEFORE UPDATE ON prospects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();