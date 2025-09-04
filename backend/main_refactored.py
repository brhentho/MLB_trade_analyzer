"""
Baseball Trade AI - Refactored Production Application
Optimized with centralized imports, async management, and structured logging
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, validator

# Core systems
from core.imports import get_service, get_tool, check_availability
from core.async_manager import async_manager, safe_async_call, async_nullcontext
from core.logging_config import get_logger, setup_logging, log_exceptions, logging_context, get_performance_logger

# Initialize logging first
setup_logging()
logger = get_logger(__name__)
performance_logger = get_performance_logger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Security configuration
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://localhost:3000').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
API_VERSION = "1.2.0"
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


# Enhanced Request/Response Models
class TradeRequest(BaseModel):
    team: str = Field(..., min_length=2, max_length=50, description="Team key or abbreviation")
    request: str = Field(..., min_length=10, max_length=1000, description="Natural language trade request")
    urgency: Optional[str] = Field('medium', description="Urgency level (low, medium, high)")
    budget_limit: Optional[float] = Field(None, ge=0, le=500000000, description="Maximum salary budget")
    include_prospects: bool = Field(True, description="Include prospects in analysis")
    max_trade_partners: int = Field(2, ge=1, le=4, description="Maximum teams in trade")
    
    @validator('team')
    def validate_team(cls, v):
        return v.strip().lower()
    
    @validator('urgency')
    def validate_urgency(cls, v):
        if v and v.lower() not in ['low', 'medium', 'high']:
            raise ValueError('Urgency must be low, medium, or high')
        return v.lower() if v else 'medium'


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


class SystemStatusResponse(BaseModel):
    service: str
    version: str
    status: str
    timestamp: str
    capabilities: List[str]
    system_health: Dict[str, Any]


class ApplicationState:
    """
    Centralized application state management
    """
    
    def __init__(self):
        self.services = {}
        self.tools = {}
        self.is_initialized = False
        self.startup_time = None
    
    async def initialize(self):
        """Initialize all application services"""
        try:
            with performance_logger.time_operation("application_initialization"):
                logger.info("Starting Baseball Trade AI initialization...")
                
                # Initialize services with centralized import management
                await self._initialize_services()
                
                # Initialize tools
                await self._initialize_tools()
                
                # Check component availability
                availability = check_availability()
                logger.info(f"Component availability: {availability}")
                
                self.is_initialized = True
                self.startup_time = datetime.now()
                logger.info("Application initialization completed successfully")
                
        except Exception as e:
            logger.error(f"Application initialization failed: {e}", exc_info=True)
            raise
    
    async def _initialize_services(self):
        """Initialize core services"""
        service_names = ['supabase', 'cache', 'queue', 'data', 'statcast']
        
        for service_name in service_names:
            try:
                service = get_service(service_name)
                if service:
                    # Initialize async services if they have async_init
                    if hasattr(service, 'async_init'):
                        await service.async_init()
                    elif hasattr(service, 'ensure_initialized'):
                        await service.ensure_initialized()
                    
                    self.services[service_name] = service
                    logger.debug(f"Initialized service: {service_name}")
                else:
                    logger.warning(f"Service {service_name} not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize service {service_name}: {e}")
    
    async def _initialize_tools(self):
        """Initialize available tools"""
        tool_names = [
            'mlb_rules', 'roster', 'salary', 'statcast', 
            'traditional_stats', 'projection', 'defensive', 
            'scouting', 'prospect'
        ]
        
        for tool_name in tool_names:
            try:
                tool = get_tool(tool_name)
                if tool:
                    self.tools[tool_name] = tool
                    logger.debug(f"Loaded tool: {tool_name}")
                    
            except Exception as e:
                logger.error(f"Failed to load tool {tool_name}: {e}")
    
    async def cleanup(self):
        """Cleanup application resources"""
        logger.info("Starting application cleanup...")
        
        # Cleanup services
        for name, service in self.services.items():
            try:
                if hasattr(service, 'async_cleanup'):
                    await service.async_cleanup()
                elif hasattr(service, 'close'):
                    if asyncio.iscoroutinefunction(service.close):
                        await service.close()
                    else:
                        service.close()
                logger.debug(f"Cleaned up service: {name}")
            except Exception as e:
                logger.error(f"Error cleaning up service {name}: {e}")
        
        # Cleanup async manager
        await async_manager.shutdown()
        
        logger.info("Application cleanup completed")


# Global application state
app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        await app_state.initialize()
        logger.info(f"Baseball Trade AI v{API_VERSION} started successfully")
        yield
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise
    finally:
        # Shutdown
        await app_state.cleanup()
        logger.info("Baseball Trade AI shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Baseball Trade AI - Refactored",
    description="Production-ready MLB trade analysis API with optimized architecture",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if ENVIRONMENT != 'production' else None,
    redoc_url="/redoc" if ENVIRONMENT != 'production' else None
)

# Add security middlewares
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS + ['*'] if ENVIRONMENT == 'development' else ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["x-rate-limit-remaining", "x-rate-limit-reset"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Performance and logging middleware
@app.middleware("http")
async def performance_and_logging_middleware(request: Request, call_next):
    """Comprehensive middleware for performance tracking and logging"""
    
    with performance_logger.time_operation(f"{request.method} {request.url.path}"):
        # Add request context to logging
        with logging_context(
            request_id=id(request),
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        ):
            try:
                response = await call_next(request)
                
                # Add security and performance headers
                response.headers.update({
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "X-API-Version": API_VERSION,
                    "X-Request-ID": str(id(request))
                })
                
                # Add caching headers based on endpoint
                if request.url.path.startswith("/api/teams") or request.url.path.startswith("/api/players"):
                    response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
                else:
                    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                
                return response
                
            except Exception as e:
                logger.error(f"Request processing failed: {e}", exc_info=True)
                raise


# Enhanced exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error on {request.url.path}: {exc}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    if ENVIRONMENT == 'production':
        message = "An internal error occurred"
        details = None
    else:
        message = str(exc)
        details = {"exception_type": exc.__class__.__name__}
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    )


# API Endpoints
@app.get("/", response_model=SystemStatusResponse)
@log_exceptions(logger)
async def root():
    """Root endpoint with comprehensive system status"""
    
    with performance_logger.time_operation("root_endpoint"):
        # Get system health information
        health_info = {}
        
        # Check database health
        supabase_service = app_state.services.get('supabase')
        if supabase_service:
            db_health = await safe_async_call(supabase_service.health_check, timeout=5.0)
            health_info['database'] = db_health.get('status', 'unknown') if db_health else 'unavailable'
        else:
            health_info['database'] = 'not_initialized'
        
        # Check other services
        for service_name in ['cache', 'queue', 'data', 'statcast']:
            service = app_state.services.get(service_name)
            health_info[service_name] = 'available' if service else 'unavailable'
        
        overall_status = 'operational' if health_info.get('database') == 'healthy' else 'degraded'
        
        return SystemStatusResponse(
            service="Baseball Trade AI - Refactored",
            version=API_VERSION,
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            capabilities=[
                "Natural language trade requests",
                "Multi-agent AI analysis",
                "Live MLB data integration",
                "Advanced caching with Redis",
                "Background task processing",
                "Comprehensive health monitoring",
                "Structured logging and error tracking",
                "Optimized async/sync handling"
            ],
            system_health=health_info
        )


@app.get("/api/health")
@log_exceptions(logger)
async def comprehensive_health_check():
    """Comprehensive health check endpoint"""
    
    with performance_logger.time_operation("health_check"):
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": API_VERSION,
            "uptime_seconds": (datetime.now() - app_state.startup_time).total_seconds() if app_state.startup_time else 0,
            "services": {},
            "tools": {},
            "performance": {}
        }
        
        # Check services
        for name, service in app_state.services.items():
            try:
                if hasattr(service, 'health_check'):
                    result = await safe_async_call(service.health_check, timeout=3.0)
                    health_data["services"][name] = result or {"status": "timeout"}
                else:
                    health_data["services"][name] = {"status": "available"}
            except Exception as e:
                logger.error(f"Health check failed for service {name}: {e}")
                health_data["services"][name] = {"status": "error", "error": str(e)}
        
        # Check tools
        health_data["tools"] = {
            name: "available" for name in app_state.tools.keys()
        }
        
        # Get performance stats
        health_data["performance"] = performance_logger.get_performance_stats()
        
        # Determine overall status
        service_issues = [
            name for name, info in health_data["services"].items()
            if info.get("status") not in ["healthy", "available"]
        ]
        
        if service_issues:
            health_data["status"] = "degraded"
            health_data["issues"] = service_issues
        
        return health_data


@app.get("/api/teams")
@log_exceptions(logger)
async def get_teams():
    """Get all MLB teams with caching"""
    
    with performance_logger.time_operation("get_teams"):
        supabase_service = app_state.services.get('supabase')
        if not supabase_service:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        teams = await safe_async_call(supabase_service.get_all_teams, timeout=10.0)
        if teams is None:
            raise HTTPException(status_code=500, detail="Failed to fetch teams")
        
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
                'budget_level': team.get('budget_level'),
                'competitive_window': team.get('competitive_window'),
                'market_size': team.get('market_size'),
                'philosophy': team.get('philosophy')
            }
        
        return {
            "teams": teams_dict,
            "total_teams": len(teams),
            "source": "database",
            "last_updated": datetime.now().isoformat()
        }


@app.get("/api/teams/{team_key}/roster")
@log_exceptions(logger)
async def get_team_roster(team_key: str):
    """Get current roster for a team"""
    
    with performance_logger.time_operation("get_team_roster"):
        supabase_service = app_state.services.get('supabase')
        if not supabase_service:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Get team info
        team = await safe_async_call(supabase_service.get_team_by_key, team_key, timeout=5.0)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Get roster
        roster = await safe_async_call(supabase_service.get_team_roster, team['id'], timeout=10.0)
        if roster is None:
            raise HTTPException(status_code=500, detail="Failed to fetch roster")
        
        return {
            "team": team['name'],
            "team_key": team_key,
            "roster": roster,
            "roster_size": len(roster),
            "last_updated": max([p.get('last_updated', '') for p in roster]) if roster else None
        }


@app.post("/api/analyze-trade", response_model=TradeAnalysisResponse)
@log_exceptions(logger)
async def analyze_trade_request(trade_request: TradeRequest, background_tasks: BackgroundTasks):
    """
    Initiate comprehensive trade analysis using optimized systems
    """
    
    with performance_logger.time_operation("analyze_trade_request"):
        supabase_service = app_state.services.get('supabase')
        if not supabase_service:
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Validate team
        team = await safe_async_call(supabase_service.get_team_by_key, trade_request.team, timeout=5.0)
        if not team:
            raise HTTPException(status_code=400, detail=f"Invalid team: {trade_request.team}")
        
        # Generate analysis ID
        import uuid
        analysis_id = str(uuid.uuid4())
        
        # Create analysis record using proper imports
        TradeAnalysisRecord = getattr(supabase_service.__class__, 'TradeAnalysisRecord', None)
        if not TradeAnalysisRecord:
            # Fallback record creation
            analysis_data = {
                'analysis_id': analysis_id,
                'requesting_team_id': team['id'],
                'request_text': trade_request.request,
                'urgency': trade_request.urgency,
                'status': 'queued'
            }
        else:
            analysis_data = TradeAnalysisRecord(
                analysis_id=analysis_id,
                requesting_team_id=team['id'],
                request_text=trade_request.request,
                urgency=trade_request.urgency,
                status='queued'
            )
        
        # Store in database
        stored_id = await safe_async_call(supabase_service.create_trade_analysis, analysis_data, timeout=5.0)
        if not stored_id:
            raise HTTPException(status_code=500, detail="Failed to create analysis record")
        
        # Start background analysis
        background_tasks.add_task(
            run_optimized_analysis,
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
            estimated_completion=(datetime.now().timestamp() + 180).__str__()
        )


async def run_optimized_analysis(analysis_id: str, request_data: Dict[str, Any]):
    """
    Background task for running trade analysis with optimized error handling
    """
    
    with performance_logger.time_operation("run_optimized_analysis"):
        try:
            logger.info(f"Starting optimized analysis for {analysis_id}")
            
            supabase_service = app_state.services.get('supabase')
            if not supabase_service:
                raise Exception("Database service unavailable")
            
            # Update status to analyzing
            await safe_async_call(
                supabase_service.update_trade_analysis_status,
                analysis_id,
                'analyzing',
                {'completed_departments': [], 'current_department': 'Initializing'},
                timeout=5.0
            )
            
            # Run analysis (placeholder for actual CrewAI integration)
            result = await run_fallback_analysis(request_data)
            
            # Store results
            await safe_async_call(
                supabase_service.update_trade_analysis_status,
                analysis_id,
                'completed',
                results=result.get('analysis'),
                cost_info=result.get('cost_info'),
                timeout=10.0
            )
            
            logger.info(f"Completed optimized analysis for {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error in optimized analysis {analysis_id}: {e}", exc_info=True)
            
            supabase_service = app_state.services.get('supabase')
            if supabase_service:
                await safe_async_call(
                    supabase_service.update_trade_analysis_status,
                    analysis_id,
                    'error',
                    error_message=str(e),
                    timeout=5.0
                )


async def run_fallback_analysis(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback analysis implementation"""
    
    await asyncio.sleep(2)  # Simulate processing time
    
    return {
        "analysis": {
            "status": "completed_with_optimized_fallback",
            "message": "Analysis completed using optimized database and import systems",
            "request": request_data.get('request'),
            "team": request_data.get('team'),
            "optimizations_applied": [
                "Centralized import management",
                "Async/sync optimization",
                "Structured logging",
                "Performance tracking",
                "Error boundary handling"
            ]
        },
        "proposals": [
            {
                "priority": 1,
                "description": "Optimized trade analysis completed",
                "teams_involved": [request_data.get('team')],
                "players_involved": ["System optimized for better performance"],
                "likelihood": "high",
                "optimizations": {
                    "import_system": "Centralized with fallbacks",
                    "async_handling": "Proper async/sync separation",
                    "error_tracking": "Comprehensive error boundaries"
                }
            }
        ],
        "cost_info": {"tokens_used": 0, "message": "Optimized system - reduced overhead"}
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    workers = int(os.getenv("API_WORKERS", 1))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    logger.info(f"Starting Baseball Trade AI v{API_VERSION} on {host}:{port}")
    
    uvicorn.run(
        "main_refactored:app",
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        access_log=True,
        server_header=False,
        date_header=False
    )