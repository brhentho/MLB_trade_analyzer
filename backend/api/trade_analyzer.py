"""
Main API endpoint for Baseball Trade AI Front Office simulation
Updated with database persistence, proper error handling, and comprehensive models
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
import logging

# Import our new models and exceptions
from .models import (
    TradeRequest, TradeAnalysisResponse, TradeAnalysisStatus,
    ParsedRequest, AnalysisProgress, DepartmentProgress,
    QuickAnalysisResponse, APIError, SystemStatus,
    UrgencyLevel, AnalysisStatus as Status, TradeRecommendation,
    ServiceHealth, DatabaseHealth
)
from .exceptions import (
    BaseTradeAIException, InvalidTeamException, AnalysisNotFoundException,
    ValidationException, DatabaseException, CrewExecutionException,
    AnalysisInProgressException, wrap_database_error
)

# Import services
from ..services.supabase_service import supabase_service, TradeAnalysisRecord
from ..crews.front_office_crew import FrontOfficeCrew
from ..nlp.trade_parser import TradeRequestParser
from ..agents.team_gms import TeamGMAgents

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Baseball Trade AI - Front Office Simulation",
    description="Complete MLB front office simulation using CrewAI multi-agent system with database persistence",
    version="1.0.0"
)

# Global instances
front_office = FrontOfficeCrew()
parser = TradeRequestParser()

# Database service instance
db_service = supabase_service

# Analysis timeout configuration
ANALYSIS_TIMEOUT_MINUTES = 30
MAX_CONCURRENT_ANALYSES = 10


# ===================
# EXCEPTION HANDLERS
# ===================

@app.exception_handler(BaseTradeAIException)
async def trade_ai_exception_handler(request, exc: BaseTradeAIException):
    """Handle custom Trade AI exceptions"""
    logger.error(f"Trade AI Exception: {exc.message} - {exc.error_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    error = APIError(
        error_type="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details={"error": str(exc)}
    )
    return JSONResponse(
        status_code=500,
        content=error.dict()
    )


# ===================
# UTILITY FUNCTIONS
# ===================

async def validate_team_exists(team_identifier: str) -> Dict[str, Any]:
    """Validate team exists and return team data"""
    team = await db_service.get_team_by_key(team_identifier.lower())
    if not team:
        # Get available teams for error message
        available_teams = await db_service.get_all_teams()
        team_keys = [t['team_key'] for t in available_teams]
        raise InvalidTeamException(team_identifier, team_keys)
    return team


async def get_active_analyses_count() -> int:
    """Get count of currently active analyses"""
    try:
        recent_analyses = await db_service.get_recent_trade_analyses(limit=50)
        active_count = len([
            a for a in recent_analyses 
            if a.get('status') in ['queued', 'initiated', 'analyzing', 'processing']
        ])
        return active_count
    except Exception as e:
        logger.error(f"Error getting active analyses count: {e}")
        return 0


def create_progress_tracker() -> AnalysisProgress:
    """Create initial progress tracker"""
    departments = [
        "Front Office Leadership",
        "Scouting Department",
        "Analytics Department", 
        "Player Development",
        "Business Operations",
        "Team Management",
        "Commissioner Office"
    ]
    
    return AnalysisProgress(
        total_progress=0.0,
        current_department=None,
        departments_completed=[],
        departments_in_progress=[],
        departments_pending=departments,
        department_details=[
            DepartmentProgress(department_name=dept)
            for dept in departments
        ],
        estimated_completion_time=datetime.now() + timedelta(minutes=ANALYSIS_TIMEOUT_MINUTES)
    )


# ===================
# API ENDPOINTS
# ===================

@app.get("/", response_model=SystemStatus)
async def root():
    """Health check and system status endpoint"""
    try:
        # Get database health
        db_health = await db_service.health_check()
        
        # Get available teams
        teams = await db_service.get_all_teams()
        available_teams = [team['team_key'] for team in teams]
        
        system_status = SystemStatus(
            overall_status="healthy" if db_health["status"] == "healthy" else "degraded",
            service_health=ServiceHealth(
                service="Baseball Trade AI - Front Office Simulation",
                version="1.0.0",
                status="healthy",
                uptime_seconds=None  # Could track uptime if needed
            ),
            database_health=DatabaseHealth(
                connected=db_health["status"] == "healthy",
                teams_count=db_health.get("teams_count", 0),
                players_count=db_health.get("players_count", 0),
                recent_analyses_count=db_health.get("recent_analyses_count", 0),
                last_analysis_time=db_health.get("last_analysis"),
                response_time_ms=None  # Could measure response time
            ),
            available_teams=available_teams,
            supported_departments=[
                "Front Office Leadership",
                "Scouting Department", 
                "Analytics Department",
                "Player Development",
                "Business Operations",
                "Team Management",
                "Commissioner Office"
            ],
            features_enabled={
                "natural_language_processing": True,
                "multi_agent_analysis": True,
                "real_time_updates": True,
                "background_processing": True,
                "database_persistence": True
            }
        )
        
        return system_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise DatabaseException("health_check", str(e))


@app.get("/teams")
async def get_available_teams():
    """Get list of available teams with details"""
    try:
        teams = await db_service.get_all_teams()
        return {
            "teams": [
                {
                    "team_key": team['team_key'],
                    "name": team['name'],
                    "abbreviation": team['abbreviation'],
                    "city": team['city'],
                    "division": team['division'],
                    "league": team['league'],
                    "competitive_window": team.get('competitive_window', 'unknown'),
                    "budget_level": team.get('budget_level', 'unknown')
                }
                for team in teams
            ],
            "total_teams": len(teams),
            "note": "Each team has unique organizational characteristics and constraints"
        }
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise DatabaseException("get_teams", str(e))


@app.post("/analyze-trade", response_model=TradeAnalysisResponse)
async def analyze_trade_request(
    request: TradeRequest,
    background_tasks: BackgroundTasks
) -> TradeAnalysisResponse:
    """
    Initiate comprehensive trade analysis using full front office simulation
    
    This endpoint triggers the entire MLB front office to analyze a trade request:
    - Natural language processing to understand the request
    - Scouting department evaluates potential targets
    - Analytics department provides statistical analysis
    - Player development assesses prospects and upside
    - Business operations evaluates financial implications
    - Team GMs provide organizational perspectives
    - Commissioner ensures MLB rule compliance
    """
    try:
        # Validate team
        team_data = await validate_team_exists(request.team)
        
        # Check if we're at max concurrent analyses
        active_count = await get_active_analyses_count()
        if active_count >= MAX_CONCURRENT_ANALYSES:
            raise ValidationException(
                "Maximum concurrent analyses reached. Please try again later.",
                details={"active_count": active_count, "max_allowed": MAX_CONCURRENT_ANALYSES}
            )
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Parse the natural language request
        parsed_request = parser.parse_trade_request(
            request.request,
            team_context=request.team
        )
        
        # Create analysis record for database
        analysis_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=team_data['id'],
            request_text=request.request,
            urgency=request.urgency.value if request.urgency else 'medium'
        )
        
        # Store in database
        created_id = await db_service.create_trade_analysis(analysis_record)
        if not created_id:
            raise DatabaseException("create_analysis", "Failed to create analysis record")
        
        # Create initial progress tracker
        progress = create_progress_tracker()
        
        # Update analysis with initial progress
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='initiated',
            progress=progress.dict()
        )
        
        # Start background analysis
        background_tasks.add_task(
            run_front_office_analysis,
            analysis_id,
            team_data,
            request
        )
        
        return TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=request.team,
            original_request=request.request,
            parsed_request=parsed_request,
            status=Status.PROCESSING,
            progress=progress,
            departments_consulted=[],
            analysis_timestamp=datetime.now(),
            estimated_completion=progress.estimated_completion_time
        )
        
    except BaseTradeAIException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_trade_request: {e}")
        raise DatabaseException("analyze_trade", str(e))


@app.get("/analysis/{analysis_id}", response_model=TradeAnalysisResponse)
async def get_analysis_status(analysis_id: str) -> TradeAnalysisResponse:
    """Get the status and results of a trade analysis"""
    try:
        analysis = await db_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise AnalysisNotFoundException(analysis_id)
        
        # Get team data
        team_data = await db_service.get_team_by_id(analysis['requesting_team_id'])
        team_key = team_data['team_key'] if team_data else 'unknown'
        
        # Parse stored request data
        parsed_request = ParsedRequest()  # Would need to reconstruct from stored data
        
        # Convert progress data
        progress_data = analysis.get('progress', {})
        progress = AnalysisProgress(**progress_data) if progress_data else None
        
        return TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=team_key,
            original_request=analysis['request_text'],
            parsed_request=parsed_request,
            status=Status(analysis['status']),
            progress=progress,
            front_office_analysis=analysis.get('results', {}).get('front_office_analysis'),
            recommendations=analysis.get('results', {}).get('recommendations'),
            departments_consulted=analysis.get('results', {}).get('departments_consulted', []),
            analysis_timestamp=datetime.fromisoformat(analysis['created_at']),
            completed_at=datetime.fromisoformat(analysis['completed_at']) if analysis.get('completed_at') else None,
            cost_info=analysis.get('cost_info'),
            error_message=analysis.get('error_message')
        )
        
    except BaseTradeAIException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}")
        raise DatabaseException("get_analysis", str(e))


@app.get("/analysis/{analysis_id}/status", response_model=TradeAnalysisStatus)
async def get_detailed_status(analysis_id: str) -> TradeAnalysisStatus:
    """Get detailed status of ongoing analysis"""
    try:
        analysis = await db_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise AnalysisNotFoundException(analysis_id)
        
        # Convert progress data
        progress_data = analysis.get('progress', {})
        progress = AnalysisProgress(**progress_data) if progress_data else create_progress_tracker()
        
        # Calculate estimated remaining time
        if analysis['status'] in ['completed', 'error']:
            estimated_remaining_time = 0
        else:
            # Simple estimation based on progress
            remaining_progress = 100.0 - progress.total_progress
            estimated_remaining_time = int((remaining_progress / 100.0) * ANALYSIS_TIMEOUT_MINUTES * 60)
        
        return TradeAnalysisStatus(
            analysis_id=analysis_id,
            status=Status(analysis['status']),
            progress=progress,
            estimated_remaining_time=estimated_remaining_time
        )
        
    except BaseTradeAIException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed status for {analysis_id}: {e}")
        raise DatabaseException("get_status", str(e))


@app.post("/quick-analysis", response_model=QuickAnalysisResponse)
async def quick_trade_analysis(request: TradeRequest) -> QuickAnalysisResponse:
    """
    Simplified synchronous analysis for immediate feedback
    """
    try:
        # Validate team
        await validate_team_exists(request.team)
        
        # Parse the request
        parsed_request = parser.parse_trade_request(request.request, request.team)
        
        # Generate crew prompt
        crew_prompt = parser.generate_crew_prompt(parsed_request)
        
        return QuickAnalysisResponse(
            team=request.team,
            original_request=request.request,
            parsed_analysis=parsed_request,
            crew_prompt=crew_prompt,
            confidence_score=parsed_request.confidence_score,
            recommended_next_steps=[
                "Run full front office analysis for comprehensive recommendations",
                "Consult scouting department for potential targets",
                "Review budget constraints with business operations",
                "Validate trade scenarios with commissioner office"
            ],
            estimated_full_analysis_time=f"{ANALYSIS_TIMEOUT_MINUTES} minutes",
            similar_past_requests=[]  # Could implement similarity search
        )
        
    except BaseTradeAIException:
        raise
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise ValidationException("Quick analysis failed", details={"error": str(e)})


# ===================
# BACKGROUND TASKS
# ===================

async def run_front_office_analysis(analysis_id: str, team_data: Dict[str, Any], request: TradeRequest):
    """
    Background task to run the comprehensive front office analysis with database persistence
    """
    try:
        logger.info(f"Starting analysis {analysis_id} for {team_data['name']}")
        
        # Update status to analyzing
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='analyzing'
        )
        
        # Create progress tracker
        progress = create_progress_tracker()
        progress.current_department = "Front Office Leadership"
        progress.departments_in_progress = ["Front Office Leadership"]
        progress.departments_pending = progress.departments_pending[1:]
        progress.total_progress = 5.0
        
        # Update progress in database
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='analyzing',
            progress=progress.dict()
        )
        
        # Run the full front office crew analysis
        try:
            result = await asyncio.wait_for(
                front_office.analyze_trade_request(team_data['team_key'], request.request),
                timeout=ANALYSIS_TIMEOUT_MINUTES * 60  # Convert to seconds
            )
        except asyncio.TimeoutError:
            raise CrewExecutionException(
                "FrontOfficeCrew", 
                f"Analysis timed out after {ANALYSIS_TIMEOUT_MINUTES} minutes",
                analysis_id
            )
        
        # Process and structure the results
        recommendations = await extract_recommendations(result, analysis_id)
        
        # Final progress update
        progress.total_progress = 100.0
        progress.current_department = None
        progress.departments_completed = progress.departments_pending + progress.departments_in_progress
        progress.departments_in_progress = []
        progress.departments_pending = []
        
        # Update the analysis record with results
        final_results = {
            "front_office_analysis": result,
            "recommendations": recommendations,
            "departments_consulted": result.get("departments_consulted", [])
        }
        
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='completed',
            progress=progress.dict(),
            results=final_results
        )
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except BaseTradeAIException as e:
        # Handle our custom exceptions
        logger.error(f"Analysis {analysis_id} failed: {e.message}")
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='error',
            error_message=e.message
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Analysis {analysis_id} failed with unexpected error: {e}")
        await db_service.update_trade_analysis_status(
            analysis_id=analysis_id,
            status='error',
            error_message=f"Unexpected error: {str(e)}"
        )


async def extract_recommendations(analysis_result: Dict[str, Any], analysis_id: str) -> List[Dict[str, Any]]:
    """
    Extract structured recommendations from the front office analysis
    Replace mock data with real data processing
    """
    recommendations = []
    
    try:
        # Process the actual analysis results
        organizational_recommendation = analysis_result.get("organizational_recommendation", {})
        
        if organizational_recommendation:
            # Extract real recommendations from the analysis
            # This would parse the actual CrewAI output
            
            # For now, create a more realistic structure based on the input
            recommendation = {
                "priority": 1,
                "analysis_id": analysis_id,
                "player_target": "TBD - Based on Analysis",  # Would extract from analysis
                "position": "TBD",  # Would extract from parsed request
                "team": "TBD",  # Would extract from analysis
                "trade_package": [],  # Would extract from analysis
                "organizational_consensus": organizational_recommendation.get("consensus", "Under Review"),
                "key_benefits": organizational_recommendation.get("benefits", [
                    "Analysis in progress",
                    "Detailed evaluation pending"
                ]),
                "risks": organizational_recommendation.get("risks", [
                    "Full risk assessment pending",
                    "Market evaluation ongoing"
                ]),
                "financial_impact": {
                    "salary_added": 0,  # Would calculate from analysis
                    "luxury_tax_impact": 0,  # Would calculate from analysis
                    "total_cost": 0  # Would calculate from analysis
                },
                "implementation_timeline": organizational_recommendation.get("timeline", "2-4 weeks"),
                "confidence_level": organizational_recommendation.get("confidence", 0.7)
            }
            
            recommendations.append(recommendation)
    
    except Exception as e:
        logger.error(f"Error extracting recommendations for {analysis_id}: {e}")
        # Return a default structure if processing fails
        recommendations.append({
            "priority": 1,
            "analysis_id": analysis_id,
            "error": "Failed to process analysis results",
            "raw_analysis": str(analysis_result)[:500]  # Truncated for debugging
        })
    
    return recommendations


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)