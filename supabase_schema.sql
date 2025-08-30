-- Baseball Trade AI Database Schema
-- Run this in your Supabase SQL Editor

-- Enable Row Level Security (JWT secret will be auto-configured by Supabase)
-- ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret'; -- Not needed, Supabase handles this

-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    team_key VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    abbreviation VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    division VARCHAR(20) NOT NULL,
    league VARCHAR(20) NOT NULL,
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    budget_level VARCHAR(10) CHECK (budget_level IN ('low', 'medium', 'high')),
    competitive_window VARCHAR(15) CHECK (competitive_window IN ('rebuild', 'retool', 'win-now')),
    market_size VARCHAR(10) CHECK (market_size IN ('small', 'medium', 'large')),
    philosophy TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    position VARCHAR(10),
    age INTEGER,
    salary DECIMAL(12, 2),
    contract_years INTEGER,
    war DECIMAL(5, 2),
    stats JSONB, -- Store batting/pitching stats as JSON
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trade analyses table
CREATE TABLE trade_analyses (
    id SERIAL PRIMARY KEY,
    analysis_id VARCHAR(100) UNIQUE NOT NULL,
    requesting_team_id INTEGER REFERENCES teams(id),
    request_text TEXT NOT NULL,
    urgency VARCHAR(10) CHECK (urgency IN ('low', 'medium', 'high')),
    status VARCHAR(20) CHECK (status IN ('queued', 'analyzing', 'completed', 'error')) DEFAULT 'queued',
    progress JSONB, -- Store analysis progress as JSON
    results JSONB, -- Store analysis results as JSON
    cost_info JSONB, -- Store token usage and costs
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Trade proposals table  
CREATE TABLE trade_proposals (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES trade_analyses(id),
    proposal_rank INTEGER,
    teams_involved JSONB, -- Array of team data
    players_involved JSONB, -- Array of player data
    likelihood VARCHAR(10) CHECK (likelihood IN ('low', 'medium', 'high')),
    financial_impact JSONB,
    risk_assessment JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User sessions (optional - for future user auth)
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid(),
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert all 30 MLB teams
INSERT INTO teams (team_key, name, abbreviation, city, division, league, primary_color, secondary_color, budget_level, competitive_window, market_size, philosophy) VALUES
('angels', 'Los Angeles Angels', 'LAA', 'Los Angeles', 'AL West', 'American League', '#BA0021', '#003263', 'medium', 'retool', 'large', 'Star-driven approach'),
('astros', 'Houston Astros', 'HOU', 'Houston', 'AL West', 'American League', '#002D62', '#EB6E1F', 'high', 'win-now', 'large', 'Analytics and development'),
('athletics', 'Oakland Athletics', 'OAK', 'Oakland', 'AL West', 'American League', '#003831', '#EFB21E', 'low', 'rebuild', 'small', 'Moneyball efficiency'),
('mariners', 'Seattle Mariners', 'SEA', 'Seattle', 'AL West', 'American League', '#0C2C56', '#005C5C', 'medium', 'win-now', 'medium', 'Player development focus'),
('rangers', 'Texas Rangers', 'TEX', 'Texas', 'AL West', 'American League', '#003278', '#C0111F', 'medium', 'win-now', 'large', 'Balanced approach'),
('braves', 'Atlanta Braves', 'ATL', 'Atlanta', 'NL East', 'National League', '#CE1141', '#13274F', 'high', 'win-now', 'large', 'Sustainable excellence'),
('marlins', 'Miami Marlins', 'MIA', 'Miami', 'NL East', 'National League', '#00A3E0', '#EF3340', 'low', 'rebuild', 'medium', 'Youth movement'),
('mets', 'New York Mets', 'NYM', 'New York', 'NL East', 'National League', '#002D72', '#FF5910', 'high', 'win-now', 'large', 'Aggressive spending'),
('phillies', 'Philadelphia Phillies', 'PHI', 'Philadelphia', 'NL East', 'National League', '#E81828', '#002D72', 'high', 'win-now', 'large', 'Win-now mentality'),
('nationals', 'Washington Nationals', 'WSN', 'Washington', 'NL East', 'National League', '#AB0003', '#14225A', 'medium', 'retool', 'large', 'Development and patience'),
('cubs', 'Chicago Cubs', 'CHC', 'Chicago', 'NL Central', 'National League', '#0E3386', '#CC3433', 'medium', 'retool', 'large', 'Analytics-driven'),
('reds', 'Cincinnati Reds', 'CIN', 'Cincinnati', 'NL Central', 'National League', '#C6011F', '#000000', 'low', 'rebuild', 'medium', 'Cost-conscious building'),
('brewers', 'Milwaukee Brewers', 'MIL', 'Milwaukee', 'NL Central', 'National League', '#FFC52F', '#12284B', 'medium', 'win-now', 'small', 'Smart acquisitions'),
('pirates', 'Pittsburgh Pirates', 'PIT', 'Pittsburgh', 'NL Central', 'National League', '#FDB827', '#27251F', 'low', 'rebuild', 'medium', 'Development focused'),
('cardinals', 'St. Louis Cardinals', 'STL', 'St. Louis', 'NL Central', 'National League', '#C41E3A', '#000066', 'medium', 'win-now', 'medium', 'Cardinal Way tradition'),
('diamondbacks', 'Arizona Diamondbacks', 'ARI', 'Arizona', 'NL West', 'National League', '#A71930', '#E3D4A3', 'medium', 'retool', 'medium', 'Balanced approach'),
('rockies', 'Colorado Rockies', 'COL', 'Colorado', 'NL West', 'National League', '#33006F', '#C4CED4', 'low', 'rebuild', 'medium', 'Pitching challenges'),
('dodgers', 'Los Angeles Dodgers', 'LAD', 'Los Angeles', 'NL West', 'National League', '#005A9C', '#EF3E42', 'high', 'win-now', 'large', 'Best-in-class development'),
('padres', 'San Diego Padres', 'SD', 'San Diego', 'NL West', 'National League', '#2F241D', '#FFC425', 'high', 'win-now', 'large', 'Aggressive moves'),
('giants', 'San Francisco Giants', 'SF', 'San Francisco', 'NL West', 'National League', '#FD5A1E', '#27251F', 'medium', 'retool', 'large', 'Even year magic'),
('orioles', 'Baltimore Orioles', 'BAL', 'Baltimore', 'AL East', 'American League', '#DF4601', '#000000', 'medium', 'win-now', 'medium', 'Prospect development'),
('redsox', 'Boston Red Sox', 'BOS', 'Boston', 'AL East', 'American League', '#BD3039', '#0C2340', 'high', 'win-now', 'large', 'Aggressive when needed'),
('yankees', 'New York Yankees', 'NYY', 'New York', 'AL East', 'American League', '#132448', '#C4CED4', 'high', 'win-now', 'large', 'Win-now with proven veterans'),
('rays', 'Tampa Bay Rays', 'TB', 'Tampa Bay', 'AL East', 'American League', '#092C5C', '#8FBCE6', 'low', 'retool', 'small', 'Analytics-driven efficiency'),
('bluejays', 'Toronto Blue Jays', 'TOR', 'Toronto', 'AL East', 'American League', '#134A8E', '#1D2D5C', 'medium', 'retool', 'large', 'International talent'),
('whitesox', 'Chicago White Sox', 'CWS', 'Chicago', 'AL Central', 'American League', '#27251F', '#C4CED4', 'low', 'rebuild', 'large', 'Complete rebuild'),
('guardians', 'Cleveland Guardians', 'CLE', 'Cleveland', 'AL Central', 'American League', '#E31937', '#0C2340', 'low', 'retool', 'medium', 'Smart spending'),
('tigers', 'Detroit Tigers', 'DET', 'Detroit', 'AL Central', 'American League', '#0C2340', '#FA4616', 'medium', 'retool', 'large', 'Young core building'),
('royals', 'Kansas City Royals', 'KC', 'Kansas City', 'AL Central', 'American League', '#004687', '#BD9B60', 'low', 'rebuild', 'small', 'Patience and development'),
('twins', 'Minnesota Twins', 'MIN', 'Minneapolis', 'AL Central', 'American League', '#002B5C', '#D31145', 'medium', 'win-now', 'medium', 'Balanced competitive approach');

-- Create indexes for better performance
CREATE INDEX idx_teams_team_key ON teams(team_key);
CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_trade_analyses_analysis_id ON trade_analyses(analysis_id);
CREATE INDEX idx_trade_analyses_status ON trade_analyses(status);
CREATE INDEX idx_trade_analyses_created_at ON trade_analyses(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (since this is a demo)
CREATE POLICY "Teams are publicly readable" ON teams FOR SELECT USING (true);
CREATE POLICY "Players are publicly readable" ON players FOR SELECT USING (true);
CREATE POLICY "Trade analyses are publicly readable" ON trade_analyses FOR SELECT USING (true);
CREATE POLICY "Trade proposals are publicly readable" ON trade_proposals FOR SELECT USING (true);

-- Create policies for inserting data (service role only)
CREATE POLICY "Service role can insert trade analyses" ON trade_analyses FOR INSERT USING (true);
CREATE POLICY "Service role can update trade analyses" ON trade_analyses FOR UPDATE USING (true);
CREATE POLICY "Service role can insert trade proposals" ON trade_proposals FOR INSERT USING (true);
CREATE POLICY "Service role can insert user sessions" ON user_sessions FOR INSERT USING (true);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at timestamps
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();