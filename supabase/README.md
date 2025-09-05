# Baseball Trade AI - Supabase Database Setup

This directory contains the database schema and setup files for the Baseball Trade AI application using Supabase.

## Quick Setup

1. **Create a Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and service role key

2. **Configure Environment Variables**
   ```bash
   # Copy the example file
   cp backend/.env.example backend/.env
   
   # Edit backend/.env and add your Supabase credentials:
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key
   SUPABASE_SECRET_KEY=your-service-role-key
   SUPABASE_ANON_KEY=your-anon-key
   ```

3. **Run Database Migrations**
   
   Option A: Using Supabase Dashboard
   - Go to your Supabase project dashboard
   - Navigate to SQL Editor
   - Copy and paste each migration file in order:
     1. `migrations/20241205000001_initial_schema.sql`
     2. `migrations/20241205000002_seed_teams.sql`
   - Execute each one

   Option B: Using Supabase CLI
   ```bash
   # Install Supabase CLI
   npm install -g supabase
   
   # Link to your project
   supabase link --project-ref your-project-ref
   
   # Run migrations
   supabase db push
   ```

4. **Verify Setup**
   ```bash
   # Run the setup script
   python setup_supabase.py
   ```

## Database Schema

### Core Tables

- **teams** - All 30 MLB teams with details
- **players** - Current MLB players with stats and contracts  
- **prospects** - Minor league prospects with rankings
- **trade_analyses** - User-submitted trade analysis requests
- **trade_proposals** - AI-generated trade proposals
- **player_stats_cache** - Cached player statistics for performance
- **team_needs** - AI-analyzed team needs and priorities

### Key Features

- ✅ Row Level Security (RLS) enabled
- ✅ Proper indexing for performance
- ✅ JSON columns for flexible data storage
- ✅ Automated timestamp tracking
- ✅ Foreign key relationships
- ✅ Check constraints for data validation

## Data Population

The seed migration includes:
- All 30 MLB teams with accurate information
- Team philosophies and competitive windows
- Budget levels and market sizes
- Division and league assignments

Player data should be populated through:
1. Manual import from MLB APIs
2. Data ingestion services
3. Regular updates from external sources

## Security

- Public read access to teams, players, and stats
- Authenticated users can create trade analyses
- Row Level Security protects sensitive data
- Service role key required for admin operations

## Performance

- Indexes on frequently queried columns
- JSON columns for flexible stats storage
- Caching layers in application code
- Connection pooling through Supabase

## Maintenance

Regular tasks:
- Clean up old trade analyses (automated)
- Update player statistics (automated)
- Refresh team needs analysis (automated)
- Monitor database performance

## Troubleshooting

**Connection Issues:**
- Verify SUPABASE_URL and keys are correct
- Check if your IP is allowed (if using restrictions)
- Ensure service role key has proper permissions

**Missing Data:**
- Run migrations in correct order
- Check Supabase logs for errors
- Verify RLS policies allow your operations

**Performance Issues:**
- Check query performance in Supabase dashboard
- Review index usage
- Monitor connection pool usage

## Migration Files

- `20241205000001_initial_schema.sql` - Creates all tables, indexes, and policies
- `20241205000002_seed_teams.sql` - Populates teams table with all MLB teams

## Next Steps

After setup:
1. Populate player data
2. Set up automated data updates
3. Configure CrewAI integration
4. Enable real-time features
5. Set up monitoring and alerts