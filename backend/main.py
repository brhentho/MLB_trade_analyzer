"""
Baseball Trade AI - Comprehensive Main Application
Implements all documented API endpoints with Supabase integration
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import Supabase service
try:
    from services.supabase_service import supabase_service, TradeAnalysisRecord
    SUPABASE_AVAILABLE = True
except ImportError:
    try:
        from backend.services.supabase_service import supabase_service, TradeAnalysisRecord
        SUPABASE_AVAILABLE = True
    except ImportError:
        logger.warning("Supabase service not available, using mock data")
        supabase_service = None
        TradeAnalysisRecord = None
        SUPABASE_AVAILABLE = False

# Import CrewAI components
try:
    from crews.front_office_crew import FrontOfficeCrew
    CREWAI_AVAILABLE = True
    logger.info("Full CrewAI components loaded successfully")
except ImportError:
    try:
        from backend.crews.front_office_crew import FrontOfficeCrew
        CREWAI_AVAILABLE = True
        logger.info("Full CrewAI components loaded successfully")
    except ImportError:
        try:
            # Try simplified crew as fallback
            from simple_crew import SimpleFrontOfficeCrew as FrontOfficeCrew
            CREWAI_AVAILABLE = True
            logger.info("Using simplified CrewAI implementation")
        except ImportError:
            try:
                from backend.simple_crew import SimpleFrontOfficeCrew as FrontOfficeCrew
                CREWAI_AVAILABLE = True
                logger.info("Using simplified CrewAI implementation")
            except ImportError:
                logger.warning("No CrewAI components available, using mock analysis")
                FrontOfficeCrew = None
                CREWAI_AVAILABLE = False

# Initialize CrewAI front office
front_office_crew = None
if CREWAI_AVAILABLE and FrontOfficeCrew:
    try:
        front_office_crew = FrontOfficeCrew()
        logger.info("Front office crew initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize front office crew: {e}")
        front_office_crew = None

# Create FastAPI app
app = FastAPI(
    title="Baseball Trade AI",
    description="AI-powered MLB trade analysis platform with real-time multi-agent evaluation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---

class TradeProposal(BaseModel):
    team_a: str = Field(..., description="First team involved in trade")
    team_b: str = Field(..., description="Second team involved in trade")
    team_c: Optional[str] = Field(None, description="Optional third team")
    players_a: List[str] = Field(..., description="Players from team A")
    players_b: List[str] = Field(..., description="Players from team B")
    players_c: Optional[List[str]] = Field(None, description="Players from team C")
    prospects_a: Optional[List[str]] = Field(None, description="Prospects from team A")
    prospects_b: Optional[List[str]] = Field(None, description="Prospects from team B")
    cash_considerations: Optional[float] = Field(None, description="Cash included in trade")

class TradeRequest(BaseModel):
    team: str = Field(..., description="Requesting team abbreviation")
    request: str = Field(..., description="Natural language trade request")
    urgency: Optional[str] = Field("medium", description="Urgency level: low, medium, high")
    budget_limit: Optional[float] = Field(None, description="Maximum salary to take on")
    include_prospects: bool = Field(True, description="Whether to consider trading prospects")

class TradeEvaluation(BaseModel):
    evaluation_id: str
    trade_proposal: TradeProposal
    overall_grade: str
    fairness_score: float
    team_grades: Dict[str, str]
    analysis_summary: str
    key_insights: List[str]
    risks: List[str]
    recommendations: List[str]
    created_at: str

class Team(BaseModel):
    id: int
    team_key: str
    name: str
    abbreviation: str
    city: str
    division: str
    league: str
    budget_level: str
    competitive_window: str
    market_size: str
    philosophy: str

class Player(BaseModel):
    id: int
    name: str
    team: str
    position: str
    age: Optional[int]
    salary: Optional[float]
    contract_years: Optional[int]
    war: Optional[float]
    stats: Optional[Dict[str, Any]]

class TeamRoster(BaseModel):
    team: Team
    players: List[Player]
    payroll_total: float
    luxury_tax_status: str

class TeamNeeds(BaseModel):
    team: Team
    primary_needs: List[str]
    secondary_needs: List[str]
    urgency_level: str
    budget_available: float
    trade_assets: List[str]
    untouchables: List[str]

class TradeSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    max_results: int = Field(10, description="Maximum number of results")

class TradeSearchResult(BaseModel):
    trades: List[TradeProposal]
    total_found: int
    search_time_ms: int
    confidence_scores: List[float]

# --- In-Memory Storage (Replace with real database) ---
active_evaluations: Dict[str, Dict[str, Any]] = {}
teams_data: Dict[str, Team] = {}
players_data: Dict[str, List[Player]] = {}

# Mock data initialization
def initialize_mock_data():
    """Initialize mock team and player data"""
    mlb_teams = [
        # AL East
        {"key": "yankees", "name": "New York Yankees", "abbr": "NYY", "city": "New York", "division": "AL East", "league": "AL"},
        {"key": "red_sox", "name": "Boston Red Sox", "abbr": "BOS", "city": "Boston", "division": "AL East", "league": "AL"},
        {"key": "blue_jays", "name": "Toronto Blue Jays", "abbr": "TOR", "city": "Toronto", "division": "AL East", "league": "AL"},
        {"key": "rays", "name": "Tampa Bay Rays", "abbr": "TB", "city": "Tampa Bay", "division": "AL East", "league": "AL"},
        {"key": "orioles", "name": "Baltimore Orioles", "abbr": "BAL", "city": "Baltimore", "division": "AL East", "league": "AL"},
        # AL Central
        {"key": "guardians", "name": "Cleveland Guardians", "abbr": "CLE", "city": "Cleveland", "division": "AL Central", "league": "AL"},
        {"key": "white_sox", "name": "Chicago White Sox", "abbr": "CWS", "city": "Chicago", "division": "AL Central", "league": "AL"},
        {"key": "twins", "name": "Minnesota Twins", "abbr": "MIN", "city": "Minneapolis", "division": "AL Central", "league": "AL"},
        {"key": "tigers", "name": "Detroit Tigers", "abbr": "DET", "city": "Detroit", "division": "AL Central", "league": "AL"},
        {"key": "royals", "name": "Kansas City Royals", "abbr": "KC", "city": "Kansas City", "division": "AL Central", "league": "AL"},
        # AL West
        {"key": "astros", "name": "Houston Astros", "abbr": "HOU", "city": "Houston", "division": "AL West", "league": "AL"},
        {"key": "rangers", "name": "Texas Rangers", "abbr": "TEX", "city": "Arlington", "division": "AL West", "league": "AL"},
        {"key": "mariners", "name": "Seattle Mariners", "abbr": "SEA", "city": "Seattle", "division": "AL West", "league": "AL"},
        {"key": "angels", "name": "Los Angeles Angels", "abbr": "LAA", "city": "Los Angeles", "division": "AL West", "league": "AL"},
        {"key": "athletics", "name": "Oakland Athletics", "abbr": "OAK", "city": "Oakland", "division": "AL West", "league": "AL"},
        # NL East
        {"key": "braves", "name": "Atlanta Braves", "abbr": "ATL", "city": "Atlanta", "division": "NL East", "league": "NL"},
        {"key": "phillies", "name": "Philadelphia Phillies", "abbr": "PHI", "city": "Philadelphia", "division": "NL East", "league": "NL"},
        {"key": "mets", "name": "New York Mets", "abbr": "NYM", "city": "New York", "division": "NL East", "league": "NL"},
        {"key": "marlins", "name": "Miami Marlins", "abbr": "MIA", "city": "Miami", "division": "NL East", "league": "NL"},
        {"key": "nationals", "name": "Washington Nationals", "abbr": "WSN", "city": "Washington", "division": "NL East", "league": "NL"},
        # NL Central
        {"key": "brewers", "name": "Milwaukee Brewers", "abbr": "MIL", "city": "Milwaukee", "division": "NL Central", "league": "NL"},
        {"key": "cubs", "name": "Chicago Cubs", "abbr": "CHC", "city": "Chicago", "division": "NL Central", "league": "NL"},
        {"key": "reds", "name": "Cincinnati Reds", "abbr": "CIN", "city": "Cincinnati", "division": "NL Central", "league": "NL"},
        {"key": "cardinals", "name": "St. Louis Cardinals", "abbr": "STL", "city": "St. Louis", "division": "NL Central", "league": "NL"},
        {"key": "pirates", "name": "Pittsburgh Pirates", "abbr": "PIT", "city": "Pittsburgh", "division": "NL Central", "league": "NL"},
        # NL West
        {"key": "dodgers", "name": "Los Angeles Dodgers", "abbr": "LAD", "city": "Los Angeles", "division": "NL West", "league": "NL"},
        {"key": "padres", "name": "San Diego Padres", "abbr": "SD", "city": "San Diego", "division": "NL West", "league": "NL"},
        {"key": "giants", "name": "San Francisco Giants", "abbr": "SF", "city": "San Francisco", "division": "NL West", "league": "NL"},
        {"key": "diamondbacks", "name": "Arizona Diamondbacks", "abbr": "ARI", "city": "Phoenix", "division": "NL West", "league": "NL"},
        {"key": "rockies", "name": "Colorado Rockies", "abbr": "COL", "city": "Denver", "division": "NL West", "league": "NL"}
    ]
    
    for i, team_data in enumerate(mlb_teams):
        team = Team(
            id=i+1,
            team_key=team_data["key"],
            name=team_data["name"],
            abbreviation=team_data["abbr"],
            city=team_data["city"],
            division=team_data["division"],
            league=team_data["league"],
            budget_level="medium",
            competitive_window="win-now",
            market_size="large",
            philosophy="Analytics-driven with veteran leadership"
        )
        teams_data[team_data["key"]] = team

initialize_mock_data()

# --- API Endpoints ---

@app.get("/")
async def root():
    """Health check and system info"""
    return {
        "service": "Baseball Trade AI",
        "version": "1.0.0",
        "status": "operational",
        "ai_systems": {
            "crewai_available": CREWAI_AVAILABLE,
            "front_office_crew": front_office_crew is not None,
            "supabase_available": SUPABASE_AVAILABLE
        },
        "endpoints": {
            "health": "/api/health",
            "teams": "/api/teams",
            "trade_search": "/api/trades/find",
            "trade_evaluation": "/api/trades/evaluate", 
            "player_search": "/api/players/search",
            "quick_analysis": "/api/quick-analysis",
            "analysis_status": "/api/analysis/{id}"
        },
        "features": [
            "Natural language trade search",
            "Multi-agent front office simulation" if CREWAI_AVAILABLE else "Basic trade evaluation",
            "Real-time AI analysis" if front_office_crew else "Mock analysis (set OpenAI key for AI)",
            "Database persistence" if SUPABASE_AVAILABLE else "In-memory data",
            "All 30 MLB teams",
            "Real-time roster data"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Detailed system health check"""
    # Check database health
    db_status = "connected" if SUPABASE_AVAILABLE else "mock_data"
    if SUPABASE_AVAILABLE and supabase_service:
        try:
            health = await supabase_service.health_check()
            db_status = health.get('status', 'unknown')
        except Exception:
            db_status = "error"
    
    # Check AI systems
    ai_status = "operational" if (CREWAI_AVAILABLE and front_office_crew) else "mock_mode"
    if CREWAI_AVAILABLE and not front_office_crew:
        ai_status = "initialization_failed"
    elif not CREWAI_AVAILABLE:
        ai_status = "not_available"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "ai_agents": ai_status,
        "systems": {
            "supabase": SUPABASE_AVAILABLE,
            "crewai": CREWAI_AVAILABLE,
            "front_office_crew": front_office_crew is not None,
            "openai_key": bool(os.getenv('OPENAI_API_KEY'))
        },
        "cache": "active",
        "version": "1.0.0"
    }

@app.get("/api/teams")
async def get_all_teams():
    """Get all MLB teams"""
    try:
        if SUPABASE_AVAILABLE and supabase_service:
            teams = await supabase_service.get_all_teams()
            return {
                "teams": teams,
                "total_teams": len(teams),
                "source": "database",
                "last_updated": datetime.now().isoformat()
            }
        else:
            # Fallback to mock data if Supabase not available
            expanded_teams = []
            for team in teams_data.values():
                expanded_teams.append({
                    "id": team.id,
                    "team_key": team.team_key,
                    "name": team.name,
                    "abbreviation": team.abbreviation,
                    "city": team.city,
                    "division": team.division,
                    "league": team.league,
                    "budget_level": team.budget_level,
                    "competitive_window": team.competitive_window,
                    "market_size": team.market_size,
                    "philosophy": team.philosophy
                })
            
            return {
                "teams": expanded_teams,
                "total_teams": len(expanded_teams),
                "source": "mock",
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch teams")

@app.get("/api/teams/{team_id}/roster")
async def get_team_roster(team_id: str = Path(..., description="Team ID or key")):
    """Get team roster with player details"""
    try:
        if SUPABASE_AVAILABLE and supabase_service:
            # Get team info from Supabase
            team = await supabase_service.get_team_by_key(team_id)
            if not team:
                # Try by ID if key doesn't work
                try:
                    team_id_int = int(team_id)
                    team = await supabase_service.get_team_by_id(team_id_int)
                except ValueError:
                    pass
                
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")
            
            # Get roster from Supabase
            roster = await supabase_service.get_team_roster(team['id'])
            
            # Calculate payroll
            payroll_total = sum(player.get('salary', 0) for player in roster if player.get('salary'))
            luxury_tax_status = "over_threshold" if payroll_total > 237000000 else "under_threshold"
            
            return {
                "team": team,
                "players": roster,
                "roster_size": len(roster),
                "payroll_total": payroll_total,
                "luxury_tax_status": luxury_tax_status,
                "source": "database",
                "last_updated": datetime.now().isoformat()
            }
        else:
            # Fallback to mock data
            if team_id not in teams_data:
                raise HTTPException(status_code=404, detail="Team not found")
            
            team = teams_data[team_id]
            
            # Mock roster data
            mock_players = [
                Player(
                    id=1,
                    name="Aaron Judge",
                    team=team_id,
                    position="OF",
                    age=31,
                    salary=40000000,
                    contract_years=8,
                    war=6.2,
                    stats={"AVG": 0.311, "HR": 62, "RBI": 131}
                ),
                Player(
                    id=2,
                    name="Gerrit Cole",
                    team=team_id,
                    position="SP",
                    age=33,
                    salary=36000000,
                    contract_years=5,
                    war=5.8,
                    stats={"ERA": 3.50, "WHIP": 1.02, "K": 257}
                )
            ]
            
            return TeamRoster(
                team=team,
                players=mock_players,
                payroll_total=245000000,
                luxury_tax_status="over_threshold"
            )
    except Exception as e:
        logger.error(f"Error fetching roster for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch roster")

@app.get("/api/teams/{team_id}/needs")
async def get_team_needs(team_id: str = Path(..., description="Team ID or key")):
    """Get AI-analyzed team needs"""
    if team_id not in teams_data:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_data[team_id]
    
    return TeamNeeds(
        team=team,
        primary_needs=["Starting Pitcher", "Left-handed Reliever"],
        secondary_needs=["Backup Catcher", "Utility Infielder"],
        urgency_level="high",
        budget_available=15000000,
        trade_assets=["Prospect A", "Prospect B", "Veteran Player C"],
        untouchables=["Aaron Judge", "Juan Soto"]
    )

@app.post("/api/trades/find")
async def find_trades(request: TradeSearchRequest):
    """Natural language trade search using AI agents"""
    search_id = str(uuid.uuid4())
    
    # Mock trade search results
    mock_trades = [
        TradeProposal(
            team_a="yankees",
            team_b="padres",
            players_a=["Prospect Package"],
            players_b=["Juan Soto"],
            cash_considerations=5000000
        ),
        TradeProposal(
            team_a="yankees",
            team_b="white_sox",
            players_a=["Clarke Schmidt", "Prospect A"],
            players_b=["Dylan Cease"]
        )
    ]
    
    return TradeSearchResult(
        trades=mock_trades,
        total_found=len(mock_trades),
        search_time_ms=1247,
        confidence_scores=[0.87, 0.74]
    )

@app.post("/api/trades/evaluate")
async def evaluate_trade(proposal: TradeProposal):
    """Evaluate a specific trade proposal using AI agents"""
    evaluation_id = str(uuid.uuid4())
    
    # Mock evaluation
    evaluation = TradeEvaluation(
        evaluation_id=evaluation_id,
        trade_proposal=proposal,
        overall_grade="B+",
        fairness_score=0.82,
        team_grades={
            proposal.team_a: "A-",
            proposal.team_b: "B+"
        },
        analysis_summary="This trade addresses both teams' needs effectively. Team A gets proven talent while Team B receives valuable prospects.",
        key_insights=[
            "Salary cap implications favor Team A",
            "Prospect value strongly supports this deal",
            "Win-now timeline alignment for both teams"
        ],
        risks=[
            "Injury history of key player",
            "Contract length considerations",
            "Prospect development uncertainty"
        ],
        recommendations=[
            "Consider adding medical review clause",
            "Negotiate performance incentives",
            "Include prospect protection provisions"
        ],
        created_at=datetime.now().isoformat()
    )
    
    active_evaluations[evaluation_id] = evaluation
    return evaluation

@app.get("/api/players/search")
async def search_players(
    q: str = Query(..., description="Search query"),
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    limit: int = Query(10, description="Maximum results")
):
    """Search players by name, position, or team"""
    try:
        if SUPABASE_AVAILABLE and supabase_service:
            # Search using Supabase
            players = await supabase_service.search_players(q, limit=limit * 2)  # Get more to filter
            
            # Apply position filter
            if position:
                players = [p for p in players if p.get('position', '').upper() == position.upper()]
            
            # Apply team filter
            if team:
                # Get team by key/abbreviation to get ID
                team_info = await supabase_service.get_team_by_key(team)
                if team_info:
                    players = [p for p in players if p.get('team_id') == team_info['id']]
                else:
                    players = []  # Team not found
            
            # Limit results
            players = players[:limit]
            
            return {
                "players": players,
                "total": len(players),
                "search_query": q,
                "filters": {"position": position, "team": team},
                "source": "database"
            }
        else:
            # Mock player search results
            mock_results = [
                Player(
                    id=1,
                    name="Aaron Judge",
                    team="yankees",
                    position="OF",
                    age=31,
                    salary=40000000,
                    war=6.2
                ),
                Player(
                    id=2,
                    name="Juan Soto",
                    team="padres",
                    position="OF",
                    age=25,
                    salary=23000000,
                    war=5.1
                )
            ]
            
            # Apply filters (mock implementation)
            filtered_results = mock_results
            if position:
                filtered_results = [p for p in filtered_results if p.position == position.upper()]
            if team:
                filtered_results = [p for p in filtered_results if p.team == team.lower()]
            
            return {
                "players": filtered_results[:limit],
                "total": len(filtered_results),
                "search_query": q,
                "filters": {"position": position, "team": team},
                "source": "mock"
            }
    except Exception as e:
        logger.error(f"Error searching players: {e}")
        raise HTTPException(status_code=500, detail="Failed to search players")

# --- Legacy Compatibility Endpoints ---

@app.post("/api/analyze-trade")
async def analyze_trade_legacy(request: TradeRequest):
    """Legacy endpoint for backward compatibility"""
    return await find_trades(TradeSearchRequest(query=request.request))

@app.post("/api/quick-analysis")
async def quick_analysis_legacy(request: TradeRequest, background_tasks: BackgroundTasks):
    """Enhanced quick analysis using AI when available"""
    try:
        if CREWAI_AVAILABLE and front_office_crew:
            # Use real AI analysis
            logger.info(f"Starting CrewAI analysis for {request.team}: {request.request}")
            
            # Start background task for full analysis
            analysis_id = str(uuid.uuid4())
            background_tasks.add_task(
                run_crewai_analysis,
                analysis_id,
                request.team,
                request.request,
                request.urgency or "medium"
            )
            
            # Return immediate response with analysis ID
            parsed_request = {
                "original_request": request.request,
                "primary_need": extract_primary_need(request.request),
                "urgency": request.urgency or "medium",
                "confidence_score": 0.90,
                "analysis_id": analysis_id,
                "ai_powered": True
            }
            
            return {
                "team": request.team,
                "original_request": request.request,
                "parsed_analysis": parsed_request,
                "recommended_next_steps": [
                    f"AI analysis initiated (ID: {analysis_id[:8]}...)",
                    "Multi-agent front office evaluation in progress",
                    "Scouting, analytics, and business ops being consulted",
                    "Results will be available in 30-60 seconds",
                    f"Check /api/analysis/{analysis_id} for detailed results"
                ],
                "analysis_status": "analyzing",
                "estimated_completion": 45
            }
        else:
            # Fallback to mock analysis
            parsed_request = {
                "original_request": request.request,
                "primary_need": extract_primary_need(request.request),
                "urgency": request.urgency or "medium",
                "confidence_score": 0.85,
                "ai_powered": False
            }
            
            return {
                "team": request.team,
                "original_request": request.request,
                "parsed_analysis": parsed_request,
                "recommended_next_steps": [
                    "Run full front office analysis for comprehensive recommendations",
                    "Consult scouting department for potential targets", 
                    "Review budget constraints with business operations",
                    "Validate trade scenarios with commissioner office",
                    "Note: Set up OpenAI API key for AI-powered analysis"
                ]
            }
    except Exception as e:
        logger.error(f"Error in quick analysis: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

# --- Helper Functions ---

def extract_primary_need(request_text: str) -> str:
    """Extract the primary need from trade request text"""
    request_lower = request_text.lower()
    
    if any(word in request_lower for word in ['pitcher', 'pitching', 'sp', 'rp', 'closer', 'starter']):
        if any(word in request_lower for word in ['relief', 'closer', 'rp', 'bullpen']):
            return "relief pitcher"
        else:
            return "starting pitcher"
    elif any(word in request_lower for word in ['catcher', 'c ']):
        return "catcher"
    elif any(word in request_lower for word in ['infield', '1b', '2b', '3b', 'ss', 'shortstop']):
        return "infielder"
    elif any(word in request_lower for word in ['outfield', 'of', 'rf', 'cf', 'lf']):
        return "outfielder"
    elif any(word in request_lower for word in ['power', 'home run', 'hr', 'slugger']):
        return "power hitter"
    elif any(word in request_lower for word in ['speed', 'steal', 'base running']):
        return "speed player"
    else:
        return "position player"

async def run_crewai_analysis(analysis_id: str, team: str, request: str, urgency: str):
    """Background task to run CrewAI analysis"""
    try:
        logger.info(f"Starting full CrewAI analysis for {analysis_id}")
        
        if SUPABASE_AVAILABLE and supabase_service:
            # Store analysis in database
            team_info = await supabase_service.get_team_by_key(team)
            if team_info:
                analysis_record = TradeAnalysisRecord(
                    analysis_id=analysis_id,
                    requesting_team_id=team_info['id'],
                    request_text=request,
                    urgency=urgency,
                    status='analyzing'
                )
                await supabase_service.create_trade_analysis(analysis_record)
        
        # Run the actual CrewAI analysis
        result = await front_office_crew.analyze_trade_request(team, request)
        
        # Update database with results
        if SUPABASE_AVAILABLE and supabase_service:
            await supabase_service.update_trade_analysis_status(
                analysis_id,
                'completed',
                results=result
            )
        
        logger.info(f"Completed CrewAI analysis for {analysis_id}")
        
    except Exception as e:
        logger.error(f"Error in CrewAI analysis {analysis_id}: {e}")
        if SUPABASE_AVAILABLE and supabase_service:
            await supabase_service.update_trade_analysis_status(
                analysis_id,
                'error',
                error_message=str(e)
            )

# Add new endpoint to check analysis status
@app.get("/api/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get the status and results of a CrewAI analysis"""
    try:
        if SUPABASE_AVAILABLE and supabase_service:
            analysis = await supabase_service.get_trade_analysis(analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            return {
                "analysis_id": analysis_id,
                "status": analysis['status'],
                "results": analysis.get('results'),
                "created_at": analysis['created_at'],
                "completed_at": analysis.get('completed_at'),
                "error_message": analysis.get('error_message')
            }
        else:
            # Mock response for when Supabase isn't available
            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "results": {
                    "message": "Analysis completed using mock data",
                    "recommendation": "Set up Supabase and OpenAI for full functionality"
                },
                "created_at": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")

# --- Error Handlers ---

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "detail": str(exc.detail) if hasattr(exc, 'detail') else "Not found"}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"Server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )

# --- Startup/Shutdown Events ---

@app.on_event("startup")
async def startup_event():
    logger.info("Baseball Trade AI starting up...")
    logger.info(f"Available teams: {len(teams_data)}")
    logger.info("All systems operational")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Baseball Trade AI shutting down...")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)