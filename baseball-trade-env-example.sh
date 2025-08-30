# Backend Environment Variables (.env)
# Copy this to backend/.env and fill in your values

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL_PRIMARY=gpt-4-turbo-preview  # For complex evaluations
OPENAI_MODEL_SECONDARY=gpt-3.5-turbo     # For simple queries
OPENAI_MODEL_TEMPERATURE=0.3              # Lower = more consistent

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here  # Keep this secret!

# Redis Configuration (for caching and queues)
REDIS_URL=redis://localhost:6379/0
# For production, use Upstash:
# REDIS_URL=redis://default:your-password@your-endpoint.upstash.io:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=true  # Set to false in production

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
RATE_LIMIT_PER_MINUTE=60

# External APIs (optional for enhanced data)
MLB_STATS_API_KEY=  # If MLB requires auth in future
FANGRAPHS_API_KEY=  # If you have premium access
BASEBALL_SAVANT_KEY=  # If scraping requires auth

# Monitoring (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
POSTHOG_API_KEY=your-posthog-key
POSTHOG_HOST=https://app.posthog.com

# Feature Flags
ENABLE_TRADE_HISTORY=true
ENABLE_COMMUNITY_FEATURES=false  # Start with this off
ENABLE_PREMIUM_FEATURES=false
MAX_TRADES_PER_USER_PER_DAY=50

# AI Agent Configuration
CREWAI_MEMORY_ENABLED=true
CREWAI_MAX_ITERATIONS=5
CREWAI_TIMEOUT_SECONDS=120
AGENT_VERBOSE_MODE=true  # Set to false in production

# Development
ENVIRONMENT=development  # development, staging, production
DEBUG=true
LOG_LEVEL=INFO

# Database Connection Pool
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30

# Cache TTL (seconds)
CACHE_TTL_PLAYER_STATS=86400      # 24 hours
CACHE_TTL_TEAM_ROSTERS=43200     # 12 hours  
CACHE_TTL_TRADE_EVALUATION=604800 # 7 days
CACHE_TTL_SEARCH_RESULTS=3600     # 1 hour

# ---------------------------------------------------

# Frontend Environment Variables (.env.local)
# Copy this to frontend/.env.local

# Public Supabase (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Analytics (optional)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=your-posthog-key
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Feature Flags (must match backend)
NEXT_PUBLIC_ENABLE_TRADE_HISTORY=true
NEXT_PUBLIC_ENABLE_COMMUNITY=false
NEXT_PUBLIC_ENABLE_PREMIUM=false

# App Configuration
NEXT_PUBLIC_APP_NAME=Baseball Trade AI
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_SUPPORT_EMAIL=support@baseballtradeai.com

# Development
NEXT_PUBLIC_ENVIRONMENT=development
NEXT_PUBLIC_DEBUG=true

# Social Media (for meta tags)
NEXT_PUBLIC_TWITTER_HANDLE=@baseballtradeai
NEXT_PUBLIC_OG_IMAGE=/og-image.png

# ---------------------------------------------------

# Production Environment Notes:
# 
# 1. Generate secure keys:
#    - SECRET_KEY: openssl rand -hex 32
#    - Database passwords: openssl rand -base64 32
#
# 2. Use environment-specific values:
#    - Different Supabase projects for dev/staging/prod
#    - Separate Redis instances
#    - Production API URLs
#
# 3. Security checklist:
#    - Never commit .env files
#    - Rotate keys regularly
#    - Use least-privilege service keys
#    - Enable CORS only for your domains
#
# 4. Performance tuning:
#    - Adjust worker counts based on server
#    - Tune cache TTLs based on usage
#    - Monitor rate limits
#
# 5. Cost management:
#    - Set OpenAI usage limits
#    - Monitor token usage
#    - Use GPT-3.5 when possible