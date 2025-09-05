-- Baseball Trade AI - Seed MLB Teams Data
-- Inserts all 30 MLB teams with their information

INSERT INTO teams (team_key, name, abbreviation, city, division, league, budget_level, competitive_window, market_size, philosophy) VALUES
-- AL East
('yankees', 'New York Yankees', 'NYY', 'New York', 'AL East', 'AL', 'high', 'win-now', 'large', 'Analytics-driven with veteran leadership and championship expectations'),
('red_sox', 'Boston Red Sox', 'BOS', 'Boston', 'AL East', 'AL', 'high', 'retooling', 'large', 'Development-focused with smart financial management'),
('blue_jays', 'Toronto Blue Jays', 'TOR', 'Toronto', 'AL East', 'AL', 'medium', 'win-now', 'medium', 'Young core with aggressive improvement strategy'),
('rays', 'Tampa Bay Rays', 'TB', 'Tampa Bay', 'AL East', 'AL', 'low', 'competitive', 'small', 'Innovation and player development on limited budget'),
('orioles', 'Baltimore Orioles', 'BAL', 'Baltimore', 'AL East', 'AL', 'medium', 'win-now', 'medium', 'Youth movement with sustainable growth model'),

-- AL Central
('guardians', 'Cleveland Guardians', 'CLE', 'Cleveland', 'AL Central', 'AL', 'medium', 'competitive', 'medium', 'Player development and smart acquisitions'),
('white_sox', 'Chicago White Sox', 'CWS', 'Chicago', 'AL Central', 'AL', 'medium', 'rebuilding', 'large', 'Full rebuild focusing on prospect accumulation'),
('twins', 'Minnesota Twins', 'MIN', 'Minneapolis', 'AL Central', 'AL', 'medium', 'competitive', 'medium', 'Balanced approach with homegrown talent'),
('tigers', 'Detroit Tigers', 'DET', 'Detroit', 'AL Central', 'AL', 'medium', 'rebuilding', 'large', 'Youth development with selective veteran additions'),
('royals', 'Kansas City Royals', 'KC', 'Kansas City', 'AL Central', 'AL', 'low', 'rebuilding', 'small', 'Farm system development and smart spending'),

-- AL West
('astros', 'Houston Astros', 'HOU', 'Houston', 'AL West', 'AL', 'high', 'win-now', 'large', 'Championship window maximization with elite analytics'),
('rangers', 'Texas Rangers', 'TEX', 'Arlington', 'AL West', 'AL', 'high', 'win-now', 'large', 'Aggressive spending to maintain championship level'),
('mariners', 'Seattle Mariners', 'SEA', 'Seattle', 'AL West', 'AL', 'medium', 'competitive', 'medium', 'Balanced roster construction with playoff focus'),
('angels', 'Los Angeles Angels', 'LAA', 'Los Angeles', 'AL West', 'AL', 'medium', 'win-now', 'large', 'Star talent with supporting cast development'),
('athletics', 'Oakland Athletics', 'OAK', 'Oakland', 'AL West', 'AL', 'low', 'rebuilding', 'small', 'Complete rebuild with focus on draft and development'),

-- NL East
('braves', 'Atlanta Braves', 'ATL', 'Atlanta', 'NL East', 'NL', 'high', 'win-now', 'large', 'Sustainable excellence through development and retention'),
('phillies', 'Philadelphia Phillies', 'PHI', 'Philadelphia', 'NL East', 'NL', 'high', 'win-now', 'large', 'Championship pursuit with veteran core'),
('mets', 'New York Mets', 'NYM', 'New York', 'NL East', 'NL', 'high', 'competitive', 'large', 'Star acquisitions with depth development'),
('marlins', 'Miami Marlins', 'MIA', 'Miami', 'NL East', 'NL', 'low', 'rebuilding', 'small', 'Youth development and international signings'),
('nationals', 'Washington Nationals', 'WSN', 'Washington', 'NL East', 'NL', 'medium', 'rebuilding', 'large', 'Prospect development with selective veteran leadership'),

-- NL Central
('brewers', 'Milwaukee Brewers', 'MIL', 'Milwaukee', 'NL Central', 'NL', 'medium', 'competitive', 'small', 'Creative roster construction and player development'),
('cubs', 'Chicago Cubs', 'CHC', 'Chicago', 'NL Central', 'NL', 'high', 'competitive', 'large', 'Balanced approach with young talent and veteran experience'),
('reds', 'Cincinnati Reds', 'CIN', 'Cincinnati', 'NL Central', 'NL', 'medium', 'rebuilding', 'medium', 'Youth movement with smart financial decisions'),
('cardinals', 'St. Louis Cardinals', 'STL', 'St. Louis', 'NL Central', 'NL', 'medium', 'competitive', 'medium', 'Sustained excellence through player development'),
('pirates', 'Pittsburgh Pirates', 'PIT', 'Pittsburgh', 'NL Central', 'NL', 'low', 'rebuilding', 'small', 'Long-term development focus with patience'),

-- NL West
('dodgers', 'Los Angeles Dodgers', 'LAD', 'Los Angeles', 'NL West', 'NL', 'high', 'win-now', 'large', 'Championship excellence through elite talent and depth'),
('padres', 'San Diego Padres', 'SD', 'San Diego', 'NL West', 'NL', 'high', 'win-now', 'medium', 'Star talent acquisition with win-now mentality'),
('giants', 'San Francisco Giants', 'SF', 'San Francisco', 'NL West', 'NL', 'high', 'competitive', 'large', 'Smart spending with development and veteran blend'),
('diamondbacks', 'Arizona Diamondbacks', 'ARI', 'Phoenix', 'NL West', 'NL', 'medium', 'competitive', 'medium', 'Young core development with strategic additions'),
('rockies', 'Colorado Rockies', 'COL', 'Denver', 'NL West', 'NL', 'medium', 'rebuilding', 'medium', 'Altitude-adjusted player development and pitching focus');

-- Set budget levels based on market size and philosophy
UPDATE teams SET payroll_budget = CASE
    WHEN budget_level = 'high' THEN 280000000
    WHEN budget_level = 'medium' THEN 180000000
    ELSE 120000000
END;