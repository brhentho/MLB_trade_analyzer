-- Baseball Trade AI - Optimized Database Schema
-- Production-ready schema with performance optimizations

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set optimized configuration
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Teams table with optimizations
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
    payroll_budget DECIMAL(12, 2) DEFAULT 0,
    luxury_tax_threshold DECIMAL(12, 2) DEFAULT 233000000,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players table with enhanced structure
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    mlb_id INTEGER UNIQUE,
    name VARCHAR(100) NOT NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    position VARCHAR(10) NOT NULL,
    jersey_number INTEGER,
    age INTEGER,
    height_inches INTEGER,
    weight_lbs INTEGER,
    bats VARCHAR(1) CHECK (bats IN ('L', 'R', 'S')),
    throws VARCHAR(1) CHECK (throws IN ('L', 'R')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'il-10', 'il-15', 'il-60', 'restricted', 'suspended', 'retired')),
    debut_date DATE,
    years_service DECIMAL(3, 1),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contracts table for salary information
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    salary DECIMAL(12, 2) NOT NULL DEFAULT 0,
    years_remaining INTEGER DEFAULT 0,
    contract_type VARCHAR(20) DEFAULT 'major_league' CHECK (contract_type IN ('major_league', 'minor_league', 'amateur')),
    has_no_trade_clause BOOLEAN DEFAULT false,
    has_player_option BOOLEAN DEFAULT false,
    has_team_option BOOLEAN DEFAULT false,
    signing_bonus DECIMAL(12, 2) DEFAULT 0,
    incentives DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, season)
);

-- Statistics cache table
CREATE TABLE stats_cache (
    id SERIAL PRIMARY KEY,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    season INTEGER NOT NULL,
    games_played INTEGER DEFAULT 0,
    at_bats INTEGER DEFAULT 0,
    hits INTEGER DEFAULT 0,
    doubles INTEGER DEFAULT 0,
    triples INTEGER DEFAULT 0,
    home_runs INTEGER DEFAULT 0,
    rbis INTEGER DEFAULT 0,
    walks INTEGER DEFAULT 0,
    strikeouts INTEGER DEFAULT 0,
    batting_avg DECIMAL(4, 3) DEFAULT 0,
    on_base_pct DECIMAL(4, 3) DEFAULT 0,
    slugging_pct DECIMAL(4, 3) DEFAULT 0,
    ops DECIMAL(4, 3) DEFAULT 0,
    war DECIMAL(5, 2) DEFAULT 0,
    -- Pitching stats
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    innings_pitched DECIMAL(5, 1) DEFAULT 0,
    hits_allowed INTEGER DEFAULT 0,
    runs_allowed INTEGER DEFAULT 0,
    earned_runs INTEGER DEFAULT 0,
    walks_allowed INTEGER DEFAULT 0,
    strikeouts_pitched INTEGER DEFAULT 0,
    era DECIMAL(4, 2) DEFAULT 0,
    whip DECIMAL(4, 3) DEFAULT 0,
    fip DECIMAL(4, 2) DEFAULT 0,
    -- Advanced metrics
    wrc_plus INTEGER DEFAULT 0,
    def_runs_saved INTEGER DEFAULT 0,
    base_running_runs DECIMAL(5, 1) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, season)
);

-- Trade analyses table with enhanced tracking
CREATE TABLE trade_analyses (
    id SERIAL PRIMARY KEY,
    analysis_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    requesting_team_id INTEGER REFERENCES teams(id),
    request_text TEXT NOT NULL,
    urgency VARCHAR(10) CHECK (urgency IN ('low', 'medium', 'high')) DEFAULT 'medium',
    status VARCHAR(20) CHECK (status IN ('queued', 'processing', 'analyzing', 'completed', 'error', 'cancelled')) DEFAULT 'queued',
    priority INTEGER DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
    progress JSONB DEFAULT '{}',
    results JSONB,
    cost_info JSONB,
    configuration JSONB DEFAULT '{}',
    error_message TEXT,
    timeout_seconds INTEGER DEFAULT 1800,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days'
);

-- Trade proposals table
CREATE TABLE trade_proposals (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES trade_analyses(id) ON DELETE CASCADE,
    proposal_rank INTEGER NOT NULL,
    proposal_uuid UUID DEFAULT uuid_generate_v4(),
    teams_involved JSONB NOT NULL DEFAULT '[]',
    players_involved JSONB NOT NULL DEFAULT '[]',
    prospects_involved JSONB DEFAULT '[]',
    draft_picks_involved JSONB DEFAULT '[]',
    likelihood VARCHAR(10) CHECK (likelihood IN ('very_low', 'low', 'medium', 'high', 'very_high')) DEFAULT 'medium',
    confidence_score DECIMAL(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    financial_impact JSONB DEFAULT '{}',
    roster_impact JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    timeline_estimate VARCHAR(50),
    summary TEXT,
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(analysis_id, proposal_rank)
);

-- Materialized view for team statistics
CREATE MATERIALIZED VIEW team_stats_summary AS
SELECT 
    t.id as team_id,
    t.team_key,
    t.name as team_name,
    COUNT(p.id) as total_players,
    AVG(p.age) as avg_age,
    SUM(COALESCE(c.salary, 0)) as total_payroll,
    AVG(COALESCE(sc.war, 0)) as avg_war,
    SUM(COALESCE(sc.war, 0)) as total_war,
    COUNT(CASE WHEN sc.war > 3.0 THEN 1 END) as star_players,
    COUNT(CASE WHEN sc.war > 1.0 THEN 1 END) as above_avg_players,
    COUNT(CASE WHEN sc.war < 0 THEN 1 END) as below_replacement,
    -- Position breakdown
    COUNT(CASE WHEN p.position = 'SP' THEN 1 END) as starting_pitchers,
    COUNT(CASE WHEN p.position = 'RP' THEN 1 END) as relief_pitchers,
    COUNT(CASE WHEN p.position = 'C' THEN 1 END) as catchers,
    COUNT(CASE WHEN p.position IN ('1B', '2B', '3B', 'SS') THEN 1 END) as infielders,
    COUNT(CASE WHEN p.position IN ('LF', 'CF', 'RF', 'OF') THEN 1 END) as outfielders,
    -- Financial metrics
    (SUM(COALESCE(c.salary, 0)) / NULLIF(t.luxury_tax_threshold, 0) * 100) as luxury_tax_percentage,
    -- Performance metrics by position
    AVG(CASE WHEN p.position = 'SP' THEN sc.war END) as sp_avg_war,
    AVG(CASE WHEN p.position = 'C' THEN sc.war END) as c_avg_war,
    AVG(CASE WHEN p.position IN ('1B', '2B', '3B', 'SS') THEN sc.war END) as if_avg_war,
    AVG(CASE WHEN p.position IN ('LF', 'CF', 'RF', 'OF') THEN sc.war END) as of_avg_war,
    NOW() as last_updated
FROM teams t
LEFT JOIN players p ON t.id = p.team_id AND p.active = true
LEFT JOIN contracts c ON p.id = c.player_id AND c.season = EXTRACT(YEAR FROM NOW())
LEFT JOIN stats_cache sc ON p.id = sc.player_id AND sc.season = EXTRACT(YEAR FROM NOW())
WHERE t.active = true
GROUP BY t.id, t.team_key, t.name, t.luxury_tax_threshold;

-- Materialized view for player rankings
CREATE MATERIALIZED VIEW player_rankings AS
SELECT 
    p.id,
    p.mlb_id,
    p.name,
    p.team_id,
    t.team_key,
    t.name as team_name,
    p.position,
    p.age,
    COALESCE(c.salary, 0) as salary,
    COALESCE(sc.war, 0) as war,
    COALESCE(sc.batting_avg, 0) as batting_avg,
    COALESCE(sc.home_runs, 0) as home_runs,
    COALESCE(sc.rbis, 0) as rbis,
    COALESCE(sc.era, 0) as era,
    COALESCE(sc.strikeouts_pitched, 0) as strikeouts,
    -- Rankings within position
    RANK() OVER (PARTITION BY p.position ORDER BY COALESCE(sc.war, 0) DESC) as position_war_rank,
    RANK() OVER (PARTITION BY p.position ORDER BY COALESCE(c.salary, 0) DESC) as position_salary_rank,
    -- Overall rankings
    RANK() OVER (ORDER BY COALESCE(sc.war, 0) DESC) as overall_war_rank,
    -- Value metrics
    CASE 
        WHEN COALESCE(c.salary, 0) > 0 THEN COALESCE(sc.war, 0) / (COALESCE(c.salary, 1) / 1000000)
        ELSE COALESCE(sc.war, 0)
    END as war_per_million,
    NOW() as last_updated
FROM players p
JOIN teams t ON p.team_id = t.id
LEFT JOIN contracts c ON p.id = c.player_id AND c.season = EXTRACT(YEAR FROM NOW())
LEFT JOIN stats_cache sc ON p.id = sc.player_id AND sc.season = EXTRACT(YEAR FROM NOW())
WHERE p.active = true AND t.active = true;

-- Performance optimization indexes
CREATE INDEX CONCURRENTLY idx_teams_team_key ON teams(team_key);
CREATE INDEX CONCURRENTLY idx_teams_league_division ON teams(league, division);
CREATE INDEX CONCURRENTLY idx_teams_competitive_window ON teams(competitive_window);

CREATE INDEX CONCURRENTLY idx_players_team_id ON players(team_id);
CREATE INDEX CONCURRENTLY idx_players_name_trgm ON players USING gin(name gin_trgm_ops);
CREATE INDEX CONCURRENTLY idx_players_position ON players(position);
CREATE INDEX CONCURRENTLY idx_players_active ON players(active) WHERE active = true;
CREATE INDEX CONCURRENTLY idx_players_mlb_id ON players(mlb_id) WHERE mlb_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_contracts_player_season ON contracts(player_id, season);
CREATE INDEX CONCURRENTLY idx_contracts_salary ON contracts(salary) WHERE salary > 0;

CREATE INDEX CONCURRENTLY idx_stats_cache_player_season ON stats_cache(player_id, season);
CREATE INDEX CONCURRENTLY idx_stats_cache_war ON stats_cache(war) WHERE war IS NOT NULL;
CREATE INDEX CONCURRENTLY idx_stats_cache_position_war ON stats_cache((SELECT position FROM players WHERE players.id = stats_cache.player_id), war);

CREATE INDEX CONCURRENTLY idx_trade_analyses_analysis_id ON trade_analyses(analysis_id);
CREATE INDEX CONCURRENTLY idx_trade_analyses_status ON trade_analyses(status);
CREATE INDEX CONCURRENTLY idx_trade_analyses_team_status ON trade_analyses(requesting_team_id, status);
CREATE INDEX CONCURRENTLY idx_trade_analyses_created_at ON trade_analyses(created_at);
CREATE INDEX CONCURRENTLY idx_trade_analyses_priority_status ON trade_analyses(priority DESC, status) WHERE status IN ('queued', 'processing');

CREATE INDEX CONCURRENTLY idx_trade_proposals_analysis_id ON trade_proposals(analysis_id);
CREATE INDEX CONCURRENTLY idx_trade_proposals_rank ON trade_proposals(analysis_id, proposal_rank);
CREATE INDEX CONCURRENTLY idx_trade_proposals_likelihood ON trade_proposals(likelihood);

-- GIN indexes for JSONB columns
CREATE INDEX CONCURRENTLY idx_trade_analyses_progress ON trade_analyses USING gin(progress);
CREATE INDEX CONCURRENTLY idx_trade_analyses_results ON trade_analyses USING gin(results);
CREATE INDEX CONCURRENTLY idx_trade_proposals_teams ON trade_proposals USING gin(teams_involved);
CREATE INDEX CONCURRENTLY idx_trade_proposals_players ON trade_proposals USING gin(players_involved);

-- Partial indexes for active records
CREATE INDEX CONCURRENTLY idx_active_players_team ON players(team_id) WHERE active = true;
CREATE INDEX CONCURRENTLY idx_active_players_position ON players(position) WHERE active = true;
CREATE INDEX CONCURRENTLY idx_pending_analyses ON trade_analyses(created_at) WHERE status IN ('queued', 'processing');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stats_cache_updated_at BEFORE UPDATE ON stats_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY team_stats_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_rankings;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old trade analyses
CREATE OR REPLACE FUNCTION cleanup_old_analyses(days_old INTEGER DEFAULT 7)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    WITH deleted AS (
        DELETE FROM trade_analyses 
        WHERE status IN ('completed', 'error', 'cancelled') 
        AND completed_at < NOW() - (days_old || ' days')::INTERVAL
        RETURNING 1
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE stats_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_proposals ENABLE ROW LEVEL SECURITY;

-- RLS Policies for public read access
CREATE POLICY "Teams are publicly readable" ON teams FOR SELECT USING (active = true);
CREATE POLICY "Players are publicly readable" ON players FOR SELECT USING (active = true);
CREATE POLICY "Contracts are publicly readable" ON contracts FOR SELECT USING (true);
CREATE POLICY "Stats cache is publicly readable" ON stats_cache FOR SELECT USING (true);
CREATE POLICY "Trade analyses are publicly readable" ON trade_analyses FOR SELECT USING (true);
CREATE POLICY "Trade proposals are publicly readable" ON trade_proposals FOR SELECT USING (true);

-- RLS Policies for service role operations
CREATE POLICY "Service role can manage trade analyses" ON trade_analyses 
    FOR ALL USING (true);
CREATE POLICY "Service role can manage trade proposals" ON trade_proposals 
    FOR ALL USING (true);
CREATE POLICY "Service role can manage players" ON players 
    FOR ALL USING (true);
CREATE POLICY "Service role can manage contracts" ON contracts 
    FOR ALL USING (true);
CREATE POLICY "Service role can manage stats" ON stats_cache 
    FOR ALL USING (true);

-- Insert all 30 MLB teams with enhanced data
INSERT INTO teams (team_key, name, abbreviation, city, division, league, primary_color, secondary_color, budget_level, competitive_window, market_size, philosophy, payroll_budget, luxury_tax_threshold) VALUES
('angels', 'Los Angeles Angels', 'LAA', 'Los Angeles', 'AL West', 'American League', '#BA0021', '#003263', 'medium', 'retool', 'large', 'Star-driven approach', 180000000, 233000000),
('astros', 'Houston Astros', 'HOU', 'Houston', 'AL West', 'American League', '#002D62', '#EB6E1F', 'high', 'win-now', 'large', 'Analytics and development', 220000000, 233000000),
('athletics', 'Oakland Athletics', 'OAK', 'Oakland', 'AL West', 'American League', '#003831', '#EFB21E', 'low', 'rebuild', 'small', 'Moneyball efficiency', 80000000, 233000000),
('mariners', 'Seattle Mariners', 'SEA', 'Seattle', 'AL West', 'American League', '#0C2C56', '#005C5C', 'medium', 'win-now', 'medium', 'Player development focus', 140000000, 233000000),
('rangers', 'Texas Rangers', 'TEX', 'Texas', 'AL West', 'American League', '#003278', '#C0111F', 'medium', 'win-now', 'large', 'Balanced approach', 170000000, 233000000),
('braves', 'Atlanta Braves', 'ATL', 'Atlanta', 'NL East', 'National League', '#CE1141', '#13274F', 'high', 'win-now', 'large', 'Sustainable excellence', 200000000, 233000000),
('marlins', 'Miami Marlins', 'MIA', 'Miami', 'NL East', 'National League', '#00A3E0', '#EF3340', 'low', 'rebuild', 'medium', 'Youth movement', 90000000, 233000000),
('mets', 'New York Mets', 'NYM', 'New York', 'NL East', 'National League', '#002D72', '#FF5910', 'high', 'win-now', 'large', 'Aggressive spending', 280000000, 233000000),
('phillies', 'Philadelphia Phillies', 'PHI', 'Philadelphia', 'NL East', 'National League', '#E81828', '#002D72', 'high', 'win-now', 'large', 'Win-now mentality', 245000000, 233000000),
('nationals', 'Washington Nationals', 'WSN', 'Washington', 'NL East', 'National League', '#AB0003', '#14225A', 'medium', 'retool', 'large', 'Development and patience', 130000000, 233000000),
('cubs', 'Chicago Cubs', 'CHC', 'Chicago', 'NL Central', 'National League', '#0E3386', '#CC3433', 'medium', 'retool', 'large', 'Analytics-driven', 150000000, 233000000),
('reds', 'Cincinnati Reds', 'CIN', 'Cincinnati', 'NL Central', 'National League', '#C6011F', '#000000', 'low', 'rebuild', 'medium', 'Cost-conscious building', 95000000, 233000000),
('brewers', 'Milwaukee Brewers', 'MIL', 'Milwaukee', 'NL Central', 'National League', '#FFC52F', '#12284B', 'medium', 'win-now', 'small', 'Smart acquisitions', 120000000, 233000000),
('pirates', 'Pittsburgh Pirates', 'PIT', 'Pittsburgh', 'NL Central', 'National League', '#FDB827', '#27251F', 'low', 'rebuild', 'medium', 'Development focused', 85000000, 233000000),
('cardinals', 'St. Louis Cardinals', 'STL', 'St. Louis', 'NL Central', 'National League', '#C41E3A', '#000066', 'medium', 'win-now', 'medium', 'Cardinal Way tradition', 160000000, 233000000),
('diamondbacks', 'Arizona Diamondbacks', 'ARI', 'Arizona', 'NL West', 'National League', '#A71930', '#E3D4A3', 'medium', 'retool', 'medium', 'Balanced approach', 125000000, 233000000),
('rockies', 'Colorado Rockies', 'COL', 'Colorado', 'NL West', 'National League', '#33006F', '#C4CED4', 'low', 'rebuild', 'medium', 'Pitching challenges', 100000000, 233000000),
('dodgers', 'Los Angeles Dodgers', 'LAD', 'Los Angeles', 'NL West', 'National League', '#005A9C', '#EF3E42', 'high', 'win-now', 'large', 'Best-in-class development', 290000000, 233000000),
('padres', 'San Diego Padres', 'SD', 'San Diego', 'NL West', 'National League', '#2F241D', '#FFC425', 'high', 'win-now', 'large', 'Aggressive moves', 250000000, 233000000),
('giants', 'San Francisco Giants', 'SF', 'San Francisco', 'NL West', 'National League', '#FD5A1E', '#27251F', 'medium', 'retool', 'large', 'Even year magic', 135000000, 233000000),
('orioles', 'Baltimore Orioles', 'BAL', 'Baltimore', 'AL East', 'American League', '#DF4601', '#000000', 'medium', 'win-now', 'medium', 'Prospect development', 145000000, 233000000),
('redsox', 'Boston Red Sox', 'BOS', 'Boston', 'AL East', 'American League', '#BD3039', '#0C2340', 'high', 'win-now', 'large', 'Aggressive when needed', 210000000, 233000000),
('yankees', 'New York Yankees', 'NYY', 'New York', 'AL East', 'American League', '#132448', '#C4CED4', 'high', 'win-now', 'large', 'Win-now with proven veterans', 275000000, 233000000),
('rays', 'Tampa Bay Rays', 'TB', 'Tampa Bay', 'AL East', 'American League', '#092C5C', '#8FBCE6', 'low', 'retool', 'small', 'Analytics-driven efficiency', 90000000, 233000000),
('bluejays', 'Toronto Blue Jays', 'TOR', 'Toronto', 'AL East', 'American League', '#134A8E', '#1D2D5C', 'medium', 'retool', 'large', 'International talent', 155000000, 233000000),
('whitesox', 'Chicago White Sox', 'CWS', 'Chicago', 'AL Central', 'American League', '#27251F', '#C4CED4', 'low', 'rebuild', 'large', 'Complete rebuild', 75000000, 233000000),
('guardians', 'Cleveland Guardians', 'CLE', 'Cleveland', 'AL Central', 'American League', '#E31937', '#0C2340', 'low', 'retool', 'medium', 'Smart spending', 110000000, 233000000),
('tigers', 'Detroit Tigers', 'DET', 'Detroit', 'AL Central', 'American League', '#0C2340', '#FA4616', 'medium', 'retool', 'large', 'Young core building', 130000000, 233000000),
('royals', 'Kansas City Royals', 'KC', 'Kansas City', 'AL Central', 'American League', '#004687', '#BD9B60', 'low', 'rebuild', 'small', 'Patience and development', 85000000, 233000000),
('twins', 'Minnesota Twins', 'MIN', 'Minneapolis', 'AL Central', 'American League', '#002B5C', '#D31145', 'medium', 'win-now', 'medium', 'Balanced competitive approach', 140000000, 233000000);

-- Schedule automatic materialized view refresh
-- This would be set up as a cron job or scheduled task
-- SELECT cron.schedule('refresh-views', '0 */6 * * *', 'SELECT refresh_materialized_views();');

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Create unique indexes on materialized views for concurrent refresh
CREATE UNIQUE INDEX team_stats_summary_team_id_idx ON team_stats_summary(team_id);
CREATE UNIQUE INDEX player_rankings_id_idx ON player_rankings(id);