"""
Baseball Trade AI - Main Application
Full CrewAI integration with live MLB data from Supabase
"""

import asyncio
import logging
import os
import uuid
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import time

# Optional security imports with fallbacks
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False

# Load environment variables and configure logging first
load_dotenv()

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://localhost:3000').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
API_KEY_HEADER = os.getenv('API_KEY_HEADER', 'X-API-Key')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize rate limiter (if available)
if RATE_LIMITING_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address)
else:
    limiter = None

# Security helper functions
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS attacks"""
    if not isinstance(text, str):
        return str(text)
    
    if BLEACH_AVAILABLE:
        return bleach.clean(text, tags=[], strip=True)
    else:
        # Fallback sanitization
        import html
        # Remove potential script tags and encode HTML entities
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = html.escape(text)
        return text.strip()

def validate_team_key(team_key: str) -> str:
    """Validate team key format"""
    if not re.match(r'^[a-zA-Z0-9_-]+$', team_key):
        raise HTTPException(status_code=400, detail="Invalid team key format")
    return team_key.lower()

# Security dependency for optional authentication
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Optional authentication - returns None if no auth provided"""
    if credentials is None:
        return None
    
    # For now, just validate the token format
    # In production, validate against your auth service
    if len(credentials.credentials) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": "authenticated_user", "token": credentials.credentials}

# Import our services
try:
    from backend.services.supabase_service import supabase_service, TradeAnalysisRecord
    from backend.services.data_ingestion import data_service
    from backend.services.statcast_service import statcast_service
    from backend.performance_config import cache, monitor, PerformanceTracker, cached_response
except ImportError:
    from services.supabase_service import supabase_service, TradeAnalysisRecord
    from services.data_ingestion import data_service
    from services.statcast_service import statcast_service
    try:
        from performance_config import cache, monitor, PerformanceTracker, cached_response
    except ImportError:
        # Fallback when performance config is not available
        cache = None
        monitor = None
        PerformanceTracker = None
        cached_response = lambda key, ttl=None: lambda func: func

# Try to import CrewAI components (optional for initial setup)
try:
    from backend.crews.front_office_crew import FrontOfficeCrew
    from backend.api.trade_analyzer import TradeAnalyzer
    CREWAI_AVAILABLE = True
except ImportError as e:
    try:
        # Try relative imports as fallback
        from .crews.front_office_crew import FrontOfficeCrew
        from .api.trade_analyzer import TradeAnalyzer
        CREWAI_AVAILABLE = True
    except ImportError:
        logger.warning(f"CrewAI components not available: {e}")
        FrontOfficeCrew = None
        TradeAnalyzer = None
        CREWAI_AVAILABLE = False

# Create FastAPI app with security headers
app = FastAPI(
    title="Baseball Trade AI - Production",
    description="AI-powered MLB trade analysis with live data and CrewAI agents",
    version="2.0.0",
    docs_url="/docs" if os.getenv('ENVIRONMENT') == 'development' else None,
    redoc_url="/redoc" if os.getenv('ENVIRONMENT') == 'development' else None
)

# Add rate limiting (if available)
if RATE_LIMITING_AVAILABLE and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middlewares in order of importance
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS + ['*'] if os.getenv('ENVIRONMENT') == 'development' else ALLOWED_HOSTS
)

# Properly configured CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "accept",
        "accept-language", 
        "content-language",
        "content-type",
        "authorization",
        API_KEY_HEADER,
        "x-requested-with"
    ],
    expose_headers=["x-rate-limit-remaining", "x-rate-limit-reset"]
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time"] = str(process_time)
    
    # Add cache control headers for static content
    if request.url.path.startswith("/api/teams") or request.url.path == "/":
        response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response

# Global exception handler for security
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal error details in production
    if os.getenv('ENVIRONMENT') == 'production':
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.now().isoformat()
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "timestamp": datetime.now().isoformat()
            }
        )

# Enhanced Request/Response Models with validation
class TradeRequest(BaseModel):
    team: str = Field(..., min_length=2, max_length=50, description="Requesting team key or abbreviation")
    request: str = Field(..., min_length=10, max_length=1000, description="Natural language trade request")
    urgency: Optional[str] = Field('medium', description="Urgency level")
    budget_limit: Optional[float] = Field(None, ge=0, le=500000000, description="Maximum salary to take on")
    include_prospects: bool = Field(True, description="Whether to consider trading prospects")
    max_trade_partners: int = Field(2, ge=1, le=4, description="Maximum number of teams in trade")
    
    @validator('team')
    def validate_team(cls, v):
        return validate_team_key(v)
    
    @validator('request')
    def sanitize_request(cls, v):
        return sanitize_input(v)
    
    @validator('urgency')
    def validate_urgency(cls, v):
        if v and v not in ['low', 'medium', 'high']:
            raise ValueError('Urgency must be low, medium, or high')
        return v

class TradeAnalysisResponse(BaseModel):
    analysis_id: str
    team: str
    original_request: str
    status: str
    front_office_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    departments_consulted: List[str]
    analysis_timestamp: str
    estimated_completion: Optional[str] = None

class TradeAnalysisStatus(BaseModel):
    analysis_id: str
    status: str
    progress: float
    current_department: Optional[str] = None
    completed_departments: List[str]
    estimated_remaining_time: Optional[int] = None
    cost_info: Optional[Dict[str, Any]] = None

# Global instances (only if CrewAI is available)
if CREWAI_AVAILABLE:
    trade_analyzer = TradeAnalyzer() if TradeAnalyzer else None
    front_office_crew = FrontOfficeCrew() if FrontOfficeCrew else None
else:
    trade_analyzer = None
    front_office_crew = None

@app.get("/")
async def root():
    """Root endpoint with system status"""
    async with PerformanceTracker('root_endpoint') if PerformanceTracker else asyncio.nullcontext():
        health = await supabase_service.health_check()
    
    return {
        "service": "Baseball Trade AI - Production",
        "version": "2.0.0",
        "status": "operational",
        "features": {
            "live_data": True,
            "crewai_agents": True,
            "statcast_integration": True,
            "multi_team_trades": True
        },
        "database": health,
        "capabilities": [
            "Natural language trade requests",
            "Multi-agent trade analysis", 
            "Live MLB data integration",
            "Advanced Statcast metrics",
            "Real-time roster updates",
            "Financial impact analysis"
        ]
    }

@app.get("/api/performance")
async def get_performance_stats():
    """Get system performance statistics"""
    if not monitor:
        return {
            "message": "Performance monitoring not available",
            "cache_enabled": cache is not None
        }
    
    stats = monitor.get_performance_stats()
    stats['cache_info'] = {
        'enabled': cache is not None,
        'type': 'redis' if cache and cache.redis_client else 'memory'
    }
    
    return stats

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check database
        db_health = await supabase_service.health_check()
        
        # Check if we can access teams
        teams = await supabase_service.get_all_teams()
        
        # Check CrewAI availability
        if not CREWAI_AVAILABLE:
            crewai_status = "not_installed"
        elif not os.getenv('OPENAI_API_KEY'):
            crewai_status = "missing_api_key"
        else:
            crewai_status = "operational"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_health,
            "teams_available": len(teams),
            "crewai_status": crewai_status,
            "data_services": {
                "supabase": db_health['status'],
                "data_ingestion": "available",
                "statcast": "available"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.get("/api/teams")
async def get_teams():
    """Get all MLB teams with current data - cached"""
    async with PerformanceTracker('get_teams') if PerformanceTracker else asyncio.nullcontext():
        try:
            # Check cache first
            if cache:
                cached_teams = await cache.get('all_teams')
                if cached_teams:
                    logger.debug("Returning cached teams data")
                    return cached_teams
            
            teams = await supabase_service.get_all_teams()
        
        # Format teams for frontend
        teams_dict = {}
        for team in teams:
            teams_dict[team['team_key']] = {
                'id': team['id'],
                'name': team['name'],
                'abbreviation': team['abbreviation'],
                'city': team['city'],
                'division': team['division'],
                'league': team['league'],
                'budget_level': team['budget_level'],
                'competitive_window': team['competitive_window'],
                'market_size': team['market_size'],
                'philosophy': team['philosophy']
            }
        
        result = {
            "teams": teams_dict,
            "total_teams": len(teams),
            "source": "database",
            "last_updated": datetime.now().isoformat()
        }
        
        # Cache the result
        if cache:
            await cache.set('all_teams', result, 300)  # Cache for 5 minutes
        
        return result
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch teams")

@app.get("/api/teams/{team_key}/roster")
async def get_team_roster(team_key: str):
    """Get current roster for a team"""
    try:
        # Get team info
        team = await supabase_service.get_team_by_key(team_key)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get roster
        roster = await supabase_service.get_team_roster(team['id'])
        
        return {
            "team": team['name'],
            "team_key": team_key,
            "roster": roster,
            "roster_size": len(roster),
            "last_updated": max([p.get('last_updated', '') for p in roster]) if roster else None
        }
    except Exception as e:
        logger.error(f"Error fetching roster for {team_key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch roster")

if RATE_LIMITING_AVAILABLE and limiter:
    @app.post("/api/analyze-trade", response_model=TradeAnalysisResponse)
    @limiter.limit("10/minute")
    async def analyze_trade_request(request: TradeRequest, background_tasks: BackgroundTasks, http_request: Request = None):
        return await _analyze_trade_request(request, background_tasks)
else:
    @app.post("/api/analyze-trade", response_model=TradeAnalysisResponse)
    async def analyze_trade_request(request: TradeRequest, background_tasks: BackgroundTasks):
        return await _analyze_trade_request(request, background_tasks)

async def _analyze_trade_request(trade_request: TradeRequest, background_tasks: BackgroundTasks):
    """
    Initiate comprehensive trade analysis using CrewAI agents and live data
    """
    try:
        # Validate team
        team = await supabase_service.get_team_by_key(trade_request.team)
        if not team:
            raise HTTPException(status_code=400, detail=f"Invalid team: {trade_request.team}")
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create analysis record
        analysis_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=team['id'],
            request_text=trade_request.request,
            urgency=trade_request.urgency or 'medium',
            status='queued'
        )
        
        # Store in database
        stored_id = await supabase_service.create_trade_analysis(analysis_record)
        if not stored_id:
            raise HTTPException(status_code=500, detail="Failed to create analysis record")
        
        # Start background analysis
        background_tasks.add_task(
            run_crew_analysis,
            analysis_id,
            trade_request.dict()
        )
        
        logger.info(f"Started trade analysis {analysis_id} for {trade_request.team}")
        
        return TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=trade_request.team,
            original_request=trade_request.request,
            status="queued",
            departments_consulted=[],
            analysis_timestamp=datetime.now().isoformat(),
            estimated_completion=datetime.fromtimestamp(datetime.now().timestamp() + 180).isoformat()  # 3 minutes estimate
        )
        
    except Exception as e:
        logger.error(f"Error creating trade analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}", response_model=TradeAnalysisResponse)
async def get_analysis_status(analysis_id: str):
    """Get the status and results of a trade analysis"""
    try:
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get team info
        team = await supabase_service.get_team_by_id(analysis['requesting_team_id'])
        team_key = team['team_key'] if team else 'unknown'
        
        # Get proposals if completed
        proposals = []
        if analysis['status'] == 'completed':
            proposals = await supabase_service.get_trade_proposals(analysis_id)
        
        return TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=team_key,
            original_request=analysis['request_text'],
            status=analysis['status'],
            front_office_analysis=analysis.get('results'),
            recommendations=proposals,
            departments_consulted=analysis.get('progress', {}).get('completed_departments', []),
            analysis_timestamp=analysis['created_at']
        )
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")

@app.get("/api/analysis/{analysis_id}/status", response_model=TradeAnalysisStatus)
async def get_detailed_analysis_status(analysis_id: str):
    """Get detailed status of ongoing analysis"""
    try:
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        progress_data = analysis.get('progress', {})
        completed_departments = progress_data.get('completed_departments', [])
        current_department = progress_data.get('current_department', None)
        
        # Calculate progress
        total_departments = 7  # Based on our agent structure
        progress = min(len(completed_departments) / total_departments, 1.0)
        
        # Estimate remaining time
        remaining_depts = total_departments - len(completed_departments)
        estimated_time = remaining_depts * 25  # 25 seconds per department
        
        return TradeAnalysisStatus(
            analysis_id=analysis_id,
            status=analysis['status'],
            progress=progress,
            current_department=current_department,
            completed_departments=completed_departments,
            estimated_remaining_time=estimated_time if analysis['status'] == 'analyzing' else None,
            cost_info=analysis.get('cost_info')
        )
    except Exception as e:
        logger.error(f"Error fetching detailed status for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch status")

@app.post("/api/data/update")
async def trigger_data_update(background_tasks: BackgroundTasks):
    """Manually trigger data update (admin endpoint)"""
    try:
        background_tasks.add_task(data_service.run_daily_update)
        
        return {
            "message": "Data update initiated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering data update: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger update")

@app.get("/api/player/{player_name}/statcast")
async def get_player_statcast(player_name: str):
    """Get Statcast profile for a player"""
    try:
        profile = await statcast_service.fetch_player_statcast_profile(player_name)
        if not profile:
            raise HTTPException(status_code=404, detail="Player not found or no Statcast data")
        
        # Convert to dict for JSON response
        profile_dict = {
            'player_name': profile.player_name,
            'mlb_id': profile.mlb_id,
            'position': profile.position,
            'hitting_metrics': {
                'avg_exit_velocity': profile.avg_exit_velocity,
                'max_exit_velocity': profile.max_exit_velocity,
                'barrel_percentage': profile.barrel_percentage,
                'hard_hit_percentage': profile.hard_hit_percentage,
                'expected_woba': profile.expected_woba,
                'sprint_speed': profile.sprint_speed
            },
            'pitching_metrics': {
                'avg_fastball_velocity': profile.avg_fastball_velocity,
                'fastball_spin_rate': profile.fastball_spin_rate,
                'release_extension': profile.release_extension
            },
            'last_updated': profile.last_updated.isoformat()
        }
        
        return profile_dict
    except Exception as e:
        logger.error(f"Error fetching Statcast data for {player_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Statcast data")

async def run_crew_analysis(analysis_id: str, request_data: Dict[str, Any]):
    """
    Background task to run CrewAI analysis
    """
    try:
        logger.info(f"Starting crew analysis for {analysis_id}")
        
        # Update status to analyzing
        await supabase_service.update_trade_analysis_status(
            analysis_id,
            'analyzing',
            progress={'completed_departments': [], 'current_department': 'Initializing'}
        )
        
        if not CREWAI_AVAILABLE or not front_office_crew:
            # Fallback analysis without CrewAI
            result = await run_fallback_analysis(request_data)
        else:
            # Run the actual CrewAI analysis
            result = await front_office_crew.analyze_trade_request(
                team_key=request_data['team'],
                request_text=request_data['request'],
                urgency=request_data.get('urgency', 'medium'),
                budget_limit=request_data.get('budget_limit'),
                include_prospects=request_data.get('include_prospects', True),
                analysis_id=analysis_id  # Pass for progress updates
            )
        
        # Store results
        await supabase_service.update_trade_analysis_status(
            analysis_id,
            'completed',
            results=result.get('analysis'),
            cost_info=result.get('cost_info')
        )
        
        # Create trade proposals
        if result.get('proposals'):
            await supabase_service.create_trade_proposals(analysis_id, result['proposals'])
        
        logger.info(f"Completed crew analysis for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error in crew analysis {analysis_id}: {e}")
        await supabase_service.update_trade_analysis_status(
            analysis_id,
            'error',
            error_message=str(e)
        )

async def run_fallback_analysis(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback analysis when CrewAI is not available
    """
    logger.info("Running fallback analysis without CrewAI")
    
    # Simulate analysis steps
    await asyncio.sleep(2)
    
    return {
        "analysis": {
            "status": "completed_with_fallback",
            "message": "Analysis completed using database tools (CrewAI not available)",
            "request": request_data.get('request'),
            "team": request_data.get('team'),
            "suggestions": [
                "Install CrewAI dependencies for full AI analysis",
                "Configure OpenAI API key for enhanced recommendations",
                "Current analysis used database queries only"
            ]
        },
        "proposals": [
            {
                "priority": 1,
                "description": "Basic trade analysis completed",
                "teams_involved": [request_data.get('team')],
                "players_involved": ["Analysis requires full AI system"],
                "likelihood": "medium",
                "financial_impact": {"message": "Requires CrewAI for full analysis"},
                "risk_assessment": {"message": "Install dependencies for complete evaluation"}
            }
        ],
        "cost_info": {"tokens_used": 0, "message": "No AI tokens used in fallback mode"}
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Baseball Trade AI - Production Version")
    
    # Check database connectivity
    health = await supabase_service.health_check()
    if health['status'] != 'healthy':
        logger.warning("Database health check failed")
    
    # Initialize data services
    logger.info("Services initialized successfully")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Baseball Trade AI")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        reload=os.getenv("API_RELOAD", "true").lower() == "true"
    )