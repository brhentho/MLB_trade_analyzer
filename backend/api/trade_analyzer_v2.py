"""
Enhanced Baseball Trade AI FastAPI Application
Database-backed, production-ready API with proper error handling
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import uuid
import logging

from ..crews.front_office_crew import FrontOfficeCrew
from ..nlp.trade_parser import TradeRequestParser
from ..agents.team_gms import TeamGMAgents
from ..services.supabase_service import supabase_service, TradeAnalysisRecord
from .models import (
    TradeRequestCreate, TradeAnalysisResponse, TradeAnalysisStatus,
    SystemHealth, TeamsResponse, AnalysisStatus, QuickAnalysisRequest,
    QuickAnalysisResponse, TeamInfo, TradeAnalysisProgress
)
from .exceptions import (
    BaseTradeAIException, base_exception_handler, validation_exception_handler,
    http_exception_handler, general_exception_handler, raise_team_not_found,
    raise_analysis_not_found, raise_database_error, raise_crew_ai_error
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Baseball Trade AI - Front Office Simulation",
    description="Complete MLB front office simulation using CrewAI multi-agent system",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(BaseTradeAIException, base_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Global instances
front_office = FrontOfficeCrew()
parser = TradeRequestParser()

@app.get("/", response_model=SystemHealth)
async def root():
    """System health check endpoint with database connectivity"""
    try:
        # Check database connectivity
        db_health = await supabase_service.health_check()
        teams = await supabase_service.get_all_teams()
        team_keys = [team['team_key'] for team in teams]
        
        # Count active analyses
        recent_analyses = await supabase_service.get_recent_trade_analyses(limit=100)
        active_count = len([a for a in recent_analyses if a['status'] in ['queued', 'analyzing']])
        
        return SystemHealth(
            service="Baseball Trade AI - Front Office Simulation",
            version="2.0.0",
            status="operational" if db_health['status'] == 'healthy' else "degraded",
            timestamp=datetime.now(),
            available_teams=team_keys,
            departments=[
                "Front Office Leadership",
                "Scouting Department", 
                "Analytics Department",
                "Player Development",
                "Business Operations",
                "Team Management",
                "Commissioner Office"
            ],
            database_status=db_health['status'],
            active_analyses=active_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise_database_error("health_check", str(e))

@app.get("/api/teams", response_model=TeamsResponse)
async def get_available_teams():
    """Get list of available teams from database"""
    try:
        teams_data = await supabase_service.get_all_teams()
        teams_info = [
            TeamInfo(
                id=team['id'],
                team_key=team['team_key'],
                name=team['name'],
                abbreviation=team['abbreviation'],
                city=team['city'],
                division=team['division'],
                league=team['league'],
                primary_color=team.get('primary_color'),
                secondary_color=team.get('secondary_color'),
                budget_level=team['budget_level'],
                competitive_window=team['competitive_window'],
                market_size=team['market_size'],
                philosophy=team.get('philosophy')
            )
            for team in teams_data
        ]
        
        return TeamsResponse(
            teams=teams_info,
            total_teams=len(teams_info),
            source="database"
        )
    except Exception as e:
        logger.error(f"Failed to get teams: {e}")
        raise_database_error("get_teams", str(e))

@app.post("/api/analyze-trade", response_model=TradeAnalysisResponse)
async def analyze_trade_request(
    request: TradeRequestCreate,
    background_tasks: BackgroundTasks
) -> TradeAnalysisResponse:
    """
    Initiate comprehensive trade analysis using full front office simulation
    
    This endpoint triggers the entire MLB front office to analyze a trade request:
    - Natural language processing to understand the request
    - Database persistence for all analysis data
    - Multi-agent CrewAI system for comprehensive analysis
    - Real-time progress tracking
    """
    
    # Validate team exists in database
    team = await supabase_service.get_team_by_key(request.team.lower())
    if not team:
        raise_team_not_found(request.team)

    try:
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Parse the natural language request
        parsed_request = parser.parse_trade_request(
            request.request,
            team_context=request.team
        )
        
        # Create database record
        analysis_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=team['id'],
            request_text=request.request,
            urgency=request.urgency.value,
            status=AnalysisStatus.QUEUED.value
        )
        
        # Store in database
        stored_id = await supabase_service.create_trade_analysis(analysis_record)
        if not stored_id:
            raise_database_error("create_analysis", "Failed to store analysis record")
            
    except Exception as e:
        logger.error(f"Failed to create analysis: {e}")
        if isinstance(e, BaseTradeAIException):
            raise
        raise_database_error("create_analysis", str(e))

    # Start background analysis with database updates
    background_tasks.add_task(
        run_front_office_analysis_db,
        analysis_id,
        team['id'],
        request.team,
        request.request
    )

    return TradeAnalysisResponse(
        analysis_id=analysis_id,
        team=request.team,
        original_request=request.request,
        status=AnalysisStatus.QUEUED,
        departments_consulted=[],
        created_at=datetime.now()
    )

@app.get("/api/analysis/{analysis_id}", response_model=TradeAnalysisResponse)
async def get_analysis_status(analysis_id: str) -> TradeAnalysisResponse:
    """Get the status and results of a trade analysis from database"""
    
    try:
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise_analysis_not_found(analysis_id)
        
        # Get team info
        team = await supabase_service.get_team_by_id(analysis['requesting_team_id'])
        team_key = team['team_key'] if team else 'unknown'
        
        # Get proposals if analysis is completed
        proposals = None
        if analysis['status'] == AnalysisStatus.COMPLETED.value:
            proposal_data = await supabase_service.get_trade_proposals(analysis_id)
            proposals = proposal_data if proposal_data else []
        
        return TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=team_key,
            original_request=analysis['request_text'],
            status=AnalysisStatus(analysis['status']),
            results=analysis.get('results'),
            proposals=proposals,
            cost_info=analysis.get('cost_info'),
            created_at=analysis['created_at'],
            completed_at=analysis.get('completed_at'),
            error_message=analysis.get('error_message'),
            departments_consulted=analysis.get('progress', {}).get('departments_completed', [])
        )
        
    except Exception as e:
        logger.error(f"Failed to get analysis {analysis_id}: {e}")
        if isinstance(e, BaseTradeAIException):
            raise
        raise_database_error("get_analysis", str(e))

@app.get("/api/analysis/{analysis_id}/status", response_model=TradeAnalysisStatus)
async def get_detailed_status(analysis_id: str) -> TradeAnalysisStatus:
    """Get detailed status of ongoing analysis"""
    
    try:
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise_analysis_not_found(analysis_id)
        
        # Extract progress information
        progress_data = analysis.get('progress', {})
        completed_departments = progress_data.get('departments_completed', [])
        current_department = progress_data.get('current_department')
        
        # Calculate progress based on departments completed
        total_departments = 7  # Front Office, Scouting, Analytics, Development, Business, Team, Commissioner
        progress_percentage = len(completed_departments) / total_departments
        
        progress = None
        if analysis['status'] in ['analyzing', 'completed']:
            progress = TradeAnalysisProgress(
                current_step=current_department or "Initializing",
                completed_steps=completed_departments,
                total_steps=total_departments,
                progress_percentage=progress_percentage * 100,
                estimated_remaining_time=max(0, int((total_departments - len(completed_departments)) * 30)),
                current_department=current_department
            )
        
        return TradeAnalysisStatus(
            analysis_id=analysis_id,
            status=AnalysisStatus(analysis['status']),
            progress=progress,
            estimated_completion=analysis.get('completed_at')
        )
        
    except Exception as e:
        logger.error(f"Failed to get detailed status for {analysis_id}: {e}")
        if isinstance(e, BaseTradeAIException):
            raise
        raise_database_error("get_status", str(e))

@app.post("/api/quick-analysis", response_model=QuickAnalysisResponse)
async def quick_trade_analysis(request: QuickAnalysisRequest) -> QuickAnalysisResponse:
    """
    Simplified synchronous analysis for immediate feedback
    """
    
    # Validate team
    team = await supabase_service.get_team_by_key(request.team.lower())
    if not team:
        raise_team_not_found(request.team)
    
    try:
        # Parse the request
        parsed_request = parser.parse_trade_request(request.request, request.team)
        
        # Generate crew prompt
        crew_prompt = parser.generate_crew_prompt(parsed_request)
        
        return QuickAnalysisResponse(
            team=request.team,
            original_request=request.request,
            parsed_request=parsed_request.__dict__,
            confidence_score=parsed_request.confidence_score,
            initial_assessment=f"Parsed trade request for {request.team}: {parsed_request.primary_need}",
            recommended_next_steps=[
                "Run full front office analysis for comprehensive recommendations",
                "Consult scouting department for potential targets",
                "Review budget constraints with business operations",
                "Validate trade scenarios with commissioner office"
            ],
            crew_prompt=crew_prompt
        )
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise_crew_ai_error("quick_analysis", str(e))

async def run_front_office_analysis_db(
    analysis_id: str, 
    team_id: int, 
    team_key: str, 
    trade_request: str
):
    """
    Background task to run the comprehensive front office analysis with database persistence
    """
    try:
        # Update status to analyzing
        await supabase_service.update_trade_analysis_status(
            analysis_id, 
            AnalysisStatus.ANALYZING.value,
            progress={
                'current_department': 'Front Office Leadership',
                'departments_completed': [],
                'started_at': datetime.now().isoformat()
            }
        )
        
        # Run the full front office crew analysis
        result = await front_office.analyze_trade_request(team_key, trade_request)
        
        # Process and store results
        proposals = extract_proposals_from_result(result)
        cost_info = extract_cost_info_from_result(result)
        
        # Update the analysis record with completion
        await supabase_service.update_trade_analysis_status(
            analysis_id,
            AnalysisStatus.COMPLETED.value,
            results=result,
            cost_info=cost_info,
            progress={
                'current_department': None,
                'departments_completed': result.get("departments_consulted", []),
                'completed_at': datetime.now().isoformat()
            }
        )
        
        # Store trade proposals if any
        if proposals:
            await supabase_service.create_trade_proposals(analysis_id, proposals)
            
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        
        # Update with error status
        await supabase_service.update_trade_analysis_status(
            analysis_id,
            AnalysisStatus.ERROR.value,
            error_message=str(e),
            progress={
                'current_department': None,
                'error_at': datetime.now().isoformat()
            }
        )

def extract_proposals_from_result(analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract structured trade proposals from the CrewAI analysis result
    """
    proposals = []
    
    # Parse the actual CrewAI result for trade proposals
    if analysis_result.get("organizational_recommendation"):
        # This would be replaced with actual parsing of CrewAI results
        proposal = {
            "proposal_rank": 1,
            "teams_involved": [{"team": "mock_team", "role": "trading_partner"}],
            "players_involved": [{"player": "mock_player", "position": "SP"}],
            "likelihood": "medium",
            "financial_impact": {"salary_added": 15000000},
            "risk_assessment": {"risk_level": "medium", "concerns": ["injury_history"]},
            "summary": "Mock proposal based on analysis results"
        }
        proposals.append(proposal)
    
    return proposals

def extract_cost_info_from_result(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract cost information from the analysis result
    """
    return {
        "total_tokens_used": analysis_result.get("token_usage", 0),
        "cost_usd": analysis_result.get("estimated_cost", 0.0),
        "model_used": "gpt-4",
        "analysis_duration_seconds": analysis_result.get("duration_seconds", 0)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)