-- Create prospects table that was missing from the database
-- Run this in Supabase SQL Editor

-- Create prospects table
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

-- Create indexes for prospects table
CREATE INDEX IF NOT EXISTS idx_prospects_team_id ON prospects(team_id);
CREATE INDEX IF NOT EXISTS idx_prospects_ranking ON prospects(ranking);
CREATE INDEX IF NOT EXISTS idx_prospects_future_value ON prospects(future_value DESC);
CREATE INDEX IF NOT EXISTS idx_prospects_eta ON prospects(eta);

-- Enable Row Level Security
ALTER TABLE prospects ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for public read access
CREATE POLICY "Prospects are publicly readable" ON prospects FOR SELECT USING (true);

-- Create update trigger for updated_at
CREATE TRIGGER update_prospects_updated_at BEFORE UPDATE ON prospects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Verify table creation
SELECT 'Prospects table created successfully' as status;