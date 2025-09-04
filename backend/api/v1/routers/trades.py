"""
Trade Analysis API Endpoints - V1
Consolidated and optimized trade analysis functionality
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse

from ...exceptions import (
    TradeAIException, InvalidTeamException, AnalysisNotFoundException,
    ValidationException, DatabaseException, CrewExecutionException
)
from ...models import (
    TradeRequestCreate, TradeAnalysisResponse, TradeAnalysisStatus,
    QuickAnalysisRequest, QuickAnalysisResponse, AnalysisStatus,
    TradeProposal, CostInfo, UrgencyLevel
)
from ....services.supabase_service import supabase_service, TradeAnalysisRecord
from ....services.cache_service import CacheService
from ....services.queue_service import QueueService
from ....crews.front_office_crew import FrontOfficeCrew
from ....nlp.trade_parser import TradeRequestParser

# Initialize services
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trades", tags=["Trade Analysis"])
cache_service = CacheService()
queue_service = QueueService()
front_office_crew = FrontOfficeCrew()
parser = TradeRequestParser()

# Configuration
MAX_CONCURRENT_ANALYSES = 10
ANALYSIS_TIMEOUT_MINUTES = 30


async def get_team_or_404(team_key: str) -> Dict:
    """Get team data or raise 404 if not found"""
    team = await supabase_service.get_team_by_key(team_key)
    if not team:
        available_teams = await supabase_service.get_all_teams()
        team_keys = [t['team_key'] for t in available_teams]
        raise InvalidTeamException(team_key, team_keys)
    return team


async def check_analysis_capacity() -> None:
    """Check if system can handle new analysis requests"""
    active_count = await get_active_analyses_count()
    if active_count >= MAX_CONCURRENT_ANALYSES:
        raise ValidationException(
            "System at capacity. Please try again later.",
            details={
                "active_analyses": active_count,
                "max_capacity": MAX_CONCURRENT_ANALYSES,
                "retry_after": 300  # 5 minutes
            }
        )


async def get_active_analyses_count() -> int:
    """Get count of currently active analyses"""
    try:
        recent_analyses = await supabase_service.get_recent_trade_analyses(limit=100)
        active_statuses = ['queued', 'analyzing', 'processing']
        return len([a for a in recent_analyses if a.get('status') in active_statuses])
    except Exception as e:
        logger.error(f"Error getting active analyses count: {e}")
        return 0


@router.post("/analyze", response_model=TradeAnalysisResponse)
async def create_trade_analysis(
    request: TradeRequestCreate,
    background_tasks: BackgroundTasks
) -> TradeAnalysisResponse:
    """
    Create comprehensive trade analysis using AI agents
    
    This endpoint initiates a full front office simulation including:
    - Natural language processing of trade request
    - Multi-agent analysis across all departments
    - Real-time progress tracking
    - Database persistence with caching
    """
    # Validate system capacity
    await check_analysis_capacity()
    
    # Validate team exists
    team_data = await get_team_or_404(request.team)
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        # Parse the natural language request
        parsed_request = await parser.parse_trade_request_async(
            request.request,
            team_context=request.team,
            urgency=request.urgency
        )
        
        # Create database record
        analysis_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=team_data['id'],
            request_text=request.request,
            urgency=request.urgency.value,
            status=AnalysisStatus.QUEUED.value
        )
        
        # Store in database
        created_id = await supabase_service.create_trade_analysis(analysis_record)
        if not created_id:
            raise DatabaseException("Failed to create analysis record")
        
        # Queue analysis for background processing
        await queue_service.enqueue_analysis(
            analysis_id=analysis_id,
            team_data=team_data,
            request_data=request.dict(),
            parsed_request=parsed_request
        )
        
        # Start background processing
        background_tasks.add_task(
            process_trade_analysis,
            analysis_id,
            team_data,
            request,
            parsed_request
        )
        
        # Cache initial response
        response = TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=request.team,
            original_request=request.request,
            status=AnalysisStatus.QUEUED,
            departments_consulted=[],
            created_at=datetime.now()
        )
        
        await cache_service.set_analysis_response(analysis_id, response, ttl=300)
        
        logger.info(f"Created analysis {analysis_id} for team {request.team}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to create analysis: {e}")
        # Clean up any partial data
        try:
            await supabase_service.update_trade_analysis_status(
                analysis_id, AnalysisStatus.ERROR.value, error_message=str(e)
            )
        except:
            pass
        
        if isinstance(e, TradeAIException):
            raise
        raise DatabaseException(f"Analysis creation failed: {str(e)}")


@router.get("/analyze/{analysis_id}", response_model=TradeAnalysisResponse)
async def get_trade_analysis(analysis_id: str) -> TradeAnalysisResponse:
    """
    Get trade analysis results and status
    Uses caching for improved performance
    """
    # Check cache first
    cached_response = await cache_service.get_analysis_response(analysis_id)
    if cached_response and cached_response.status != AnalysisStatus.ERROR:
        return cached_response
    
    try:
        # Get from database
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise AnalysisNotFoundException(analysis_id)
        
        # Get team data
        team_data = await supabase_service.get_team_by_id(analysis['requesting_team_id'])
        team_key = team_data['team_key'] if team_data else 'unknown'
        
        # Get proposals if completed
        proposals = []
        if analysis['status'] == AnalysisStatus.COMPLETED.value:
            proposal_data = await supabase_service.get_trade_proposals(analysis_id)
            proposals = [TradeProposal(**p) for p in proposal_data] if proposal_data else []
        
        # Build response
        response = TradeAnalysisResponse(
            analysis_id=analysis_id,
            team=team_key,
            original_request=analysis['request_text'],
            status=AnalysisStatus(analysis['status']),
            results=analysis.get('results'),
            proposals=proposals,
            cost_info=CostInfo(**analysis['cost_info']) if analysis.get('cost_info') else None,
            created_at=datetime.fromisoformat(analysis['created_at']),
            completed_at=datetime.fromisoformat(analysis['completed_at']) if analysis.get('completed_at') else None,
            error_message=analysis.get('error_message'),
            departments_consulted=analysis.get('progress', {}).get('departments_completed', [])
        )
        
        # Cache successful responses
        if response.status in [AnalysisStatus.COMPLETED, AnalysisStatus.ERROR]:
            await cache_service.set_analysis_response(analysis_id, response, ttl=1800)  # 30 minutes
        else:
            await cache_service.set_analysis_response(analysis_id, response, ttl=60)   # 1 minute for active
        
        return response
        
    except TradeAIException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}")
        raise DatabaseException(f"Failed to retrieve analysis: {str(e)}")


@router.get("/analyze/{analysis_id}/status", response_model=TradeAnalysisStatus)
async def get_analysis_status(analysis_id: str) -> TradeAnalysisStatus:
    """
    Get detailed analysis status and progress
    Lightweight endpoint for progress polling
    """
    try:
        analysis = await supabase_service.get_trade_analysis(analysis_id)
        if not analysis:
            raise AnalysisNotFoundException(analysis_id)
        
        # Extract progress information
        progress_data = analysis.get('progress', {})
        estimated_completion = None
        
        if analysis['status'] == AnalysisStatus.ANALYZING.value:
            # Calculate estimated completion based on progress
            progress_pct = progress_data.get('progress_percentage', 0)
            remaining_time = max(0, int((100 - progress_pct) / 100 * ANALYSIS_TIMEOUT_MINUTES * 60))
            estimated_completion = datetime.now() + timedelta(seconds=remaining_time)
        
        return TradeAnalysisStatus(
            analysis_id=analysis_id,
            status=AnalysisStatus(analysis['status']),
            estimated_completion=estimated_completion
        )
        
    except TradeAIException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for {analysis_id}: {e}")
        raise DatabaseException(f"Failed to get analysis status: {str(e)}")


@router.post("/quick-analyze", response_model=QuickAnalysisResponse)
async def quick_trade_analysis(request: QuickAnalysisRequest) -> QuickAnalysisResponse:
    """
    Fast synchronous trade analysis for immediate feedback
    Does not use AI agents - pure NLP parsing and basic recommendations
    """
    # Validate team
    await get_team_or_404(request.team)
    
    try:
        # Parse request using NLP
        parsed_request = await parser.parse_trade_request_async(
            request.request, 
            request.team
        )
        
        # Generate basic recommendations without full crew analysis
        recommendations = await generate_quick_recommendations(
            request.team, 
            parsed_request
        )
        
        return QuickAnalysisResponse(
            team=request.team,
            original_request=request.request,
            parsed_request=parsed_request.dict(),
            confidence_score=parsed_request.confidence_score,
            initial_assessment=f"Identified {parsed_request.primary_need} need for {request.team}",
            recommended_next_steps=[
                "Run full analysis for detailed AI recommendations",
                "Review current roster composition and salary constraints",
                "Identify potential trade partners with surplus talent",
                "Consider prospect cost vs immediate impact"
            ]
        )
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {e}")
        raise ValidationException(f"Quick analysis failed: {str(e)}")


@router.get("/recent", response_model=List[TradeAnalysisResponse])
async def get_recent_analyses(
    team: Optional[str] = Query(None, description="Filter by team"),
    limit: int = Query(10, ge=1, le=50, description="Number of analyses to return"),
    status: Optional[AnalysisStatus] = Query(None, description="Filter by status")
) -> List[TradeAnalysisResponse]:
    """
    Get recent trade analyses with optional filtering
    Supports pagination and team/status filtering
    """
    try:
        # Get team ID if filtering by team
        team_id = None
        if team:
            team_data = await get_team_or_404(team)
            team_id = team_data['id']
        
        # Get analyses from database
        analyses = await supabase_service.get_recent_trade_analyses(
            team_id=team_id,
            limit=limit
        )
        
        # Filter by status if specified
        if status:
            analyses = [a for a in analyses if a.get('status') == status.value]
        
        # Convert to response models
        responses = []
        for analysis in analyses:
            team_data = await supabase_service.get_team_by_id(analysis['requesting_team_id'])
            team_key = team_data['team_key'] if team_data else 'unknown'
            
            response = TradeAnalysisResponse(
                analysis_id=analysis['analysis_id'],
                team=team_key,
                original_request=analysis['request_text'],
                status=AnalysisStatus(analysis['status']),
                created_at=datetime.fromisoformat(analysis['created_at']),
                completed_at=datetime.fromisoformat(analysis['completed_at']) if analysis.get('completed_at') else None,
                departments_consulted=analysis.get('progress', {}).get('departments_completed', [])
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error getting recent analyses: {e}")
        raise DatabaseException(f"Failed to get recent analyses: {str(e)}")


async def process_trade_analysis(
    analysis_id: str,
    team_data: Dict,
    request: TradeRequestCreate,
    parsed_request: Dict
):
    """
    Background task for processing trade analysis with full AI crew
    Includes proper error handling and progress tracking
    """
    try:
        logger.info(f"Starting analysis {analysis_id} for {team_data['name']}")
        
        # Update status to analyzing
        await supabase_service.update_trade_analysis_status(
            analysis_id, AnalysisStatus.ANALYZING.value,
            progress={'started_at': datetime.now().isoformat(), 'progress_percentage': 0}
        )
        
        # Run the crew analysis with timeout
        try:
            result = await asyncio.wait_for(
                front_office_crew.analyze_trade_request_with_progress(
                    team_data['team_key'],
                    request.request,
                    urgency=request.urgency.value,
                    budget_limit=request.budget_limit,
                    include_prospects=request.include_prospects,
                    analysis_id=analysis_id
                ),
                timeout=ANALYSIS_TIMEOUT_MINUTES * 60
            )
        except asyncio.TimeoutError:
            raise CrewExecutionException(
                f"Analysis timed out after {ANALYSIS_TIMEOUT_MINUTES} minutes"
            )
        
        # Process results and extract proposals
        proposals = extract_proposals_from_result(result)
        cost_info = extract_cost_info_from_result(result)
        
        # Update database with completion
        await supabase_service.update_trade_analysis_status(
            analysis_id, AnalysisStatus.COMPLETED.value,
            results=result,
            cost_info=cost_info,
            progress={
                'completed_at': datetime.now().isoformat(),
                'progress_percentage': 100,
                'departments_completed': result.get('departments_consulted', [])
            }
        )
        
        # Store trade proposals
        if proposals:
            await supabase_service.create_trade_proposals(analysis_id, proposals)
        
        # Clear cache to force refresh
        await cache_service.delete_analysis_response(analysis_id)
        
        logger.info(f"Completed analysis {analysis_id}")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        
        # Update with error status
        await supabase_service.update_trade_analysis_status(
            analysis_id, AnalysisStatus.ERROR.value,
            error_message=str(e),
            progress={'error_at': datetime.now().isoformat()}
        )
        
        # Clear cache
        await cache_service.delete_analysis_response(analysis_id)


def extract_proposals_from_result(result: Dict) -> List[Dict]:
    """Extract structured trade proposals from AI analysis result"""
    proposals = []
    
    if result.get("trade_recommendations"):
        for i, rec in enumerate(result["trade_recommendations"][:5]):  # Limit to top 5
            proposal = {
                "proposal_rank": i + 1,
                "teams_involved": rec.get("teams_involved", []),
                "players_involved": rec.get("players_involved", []),
                "likelihood": rec.get("likelihood", "medium"),
                "financial_impact": rec.get("financial_impact", {}),
                "risk_assessment": rec.get("risk_assessment", {}),
                "summary": rec.get("summary", "")
            }
            proposals.append(proposal)
    
    return proposals


def extract_cost_info_from_result(result: Dict) -> Dict:
    """Extract cost information from AI analysis result"""
    return {
        "total_tokens_used": result.get("token_usage", 0),
        "cost_usd": result.get("estimated_cost", 0.0),
        "model_used": result.get("model_used", "gpt-4"),
        "analysis_duration_seconds": result.get("duration_seconds", 0)
    }


async def generate_quick_recommendations(team: str, parsed_request: Dict) -> List[str]:
    """Generate quick recommendations without full AI analysis"""
    recommendations = [
        f"Consider trading for {parsed_request.get('primary_need', 'needed position')}",
        "Review salary cap implications before proceeding",
        "Identify teams with surplus talent at target position",
        "Evaluate prospect cost vs immediate impact"
    ]
    
    # Add urgency-based recommendations
    urgency = parsed_request.get('urgency', 'medium')
    if urgency == 'high':
        recommendations.insert(0, "Prioritize immediate impact players over prospects")
    elif urgency == 'low':
        recommendations.insert(0, "Consider long-term value and prospect development")
    
    return recommendations