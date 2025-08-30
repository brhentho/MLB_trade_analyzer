"""
Baseball Trade AI - Simplified Demo Version
Main application entry point without CrewAI dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Baseball Trade AI - Demo Version",
    description="Simplified MLB front office simulation for demonstration",
    version="1.0.0-demo"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class TradeRequest(BaseModel):
    team: str = Field(..., description="Requesting team abbreviation")
    request: str = Field(..., description="Natural language trade request")
    urgency: Optional[str] = Field(None, description="Urgency level")
    budget_limit: Optional[float] = Field(None, description="Maximum salary to take on")
    include_prospects: bool = Field(True, description="Whether to consider trading prospects")

class TradeRecommendation(BaseModel):
    priority: int
    player_target: str
    position: str
    current_team: str
    trade_package: List[str]
    organizational_consensus: str
    key_benefits: List[str]
    risks: List[str]
    financial_impact: Dict[str, Any]
    implementation_timeline: str

class TradeAnalysisResponse(BaseModel):
    analysis_id: str
    team: str
    original_request: str
    parsed_request: Dict[str, Any]
    status: str
    front_office_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[TradeRecommendation]] = None
    departments_consulted: List[str]
    analysis_timestamp: str

class TradeAnalysisStatus(BaseModel):
    analysis_id: str
    status: str
    progress: float
    current_department: Optional[str] = None
    completed_departments: List[str]
    estimated_remaining_time: Optional[int] = None

# In-memory storage for demo
active_analyses: Dict[str, Dict[str, Any]] = {}

# Mock team data
TEAMS = [
    'yankees', 'red_sox', 'orioles', 'rays', 'blue_jays',
    'guardians', 'white_sox', 'twins', 'tigers', 'royals',
    'astros', 'rangers', 'mariners', 'angels', 'athletics',
    'dodgers', 'padres', 'giants', 'rockies', 'diamondbacks',
    'braves', 'phillies', 'mets', 'nationals', 'marlins',
    'brewers', 'cardinals', 'cubs', 'reds', 'pirates'
]

DEPARTMENTS = [
    "Front Office Leadership",
    "Scouting Department", 
    "Analytics Department",
    "Player Development",
    "Business Operations",
    "Team Management",
    "Commissioner Office"
]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Baseball Trade AI - Demo Version",
        "version": "1.0.0-demo",
        "status": "operational",
        "available_teams": len(TEAMS),
        "departments": DEPARTMENTS,
        "note": "This is a simplified demo version for testing the frontend"
    }

@app.get("/api/teams")
async def get_teams():
    """Get list of available teams"""
    return {
        "teams": TEAMS,
        "total_teams": len(TEAMS),
        "note": "Demo version - each team has simulated characteristics"
    }

@app.post("/api/analyze-trade", response_model=TradeAnalysisResponse)
async def analyze_trade_request(request: TradeRequest):
    """
    Initiate trade analysis (demo version with simulated processing)
    """
    
    # Validate team
    if request.team.lower() not in TEAMS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid team: {request.team}. Available teams: {TEAMS}"
        )
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    # Mock parsed request
    parsed_request = {
        "original_request": request.request,
        "primary_need": extract_primary_need(request.request),
        "position_type": "hitter",  # Mock
        "specific_positions": ["outfield"],
        "player_attributes": {"power": True},
        "urgency": request.urgency or "exploratory",
        "confidence_score": 0.85
    }
    
    # Create analysis record
    analysis_record = {
        "analysis_id": analysis_id,
        "team": request.team,
        "original_request": request.request,
        "parsed_request": parsed_request,
        "status": "processing",
        "departments_consulted": [],
        "created_at": datetime.now(),
        "current_department_index": 0
    }
    
    active_analyses[analysis_id] = analysis_record
    
    # Start background processing
    asyncio.create_task(simulate_analysis(analysis_id))
    
    return TradeAnalysisResponse(
        analysis_id=analysis_id,
        team=request.team,
        original_request=request.request,
        parsed_request=parsed_request,
        status="processing",
        departments_consulted=[],
        analysis_timestamp=datetime.now().isoformat()
    )

@app.get("/api/analysis/{analysis_id}", response_model=TradeAnalysisResponse)
async def get_analysis_status(analysis_id: str):
    """Get the status and results of a trade analysis"""
    
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = active_analyses[analysis_id]
    
    return TradeAnalysisResponse(
        analysis_id=analysis_id,
        team=analysis["team"],
        original_request=analysis["original_request"],
        parsed_request=analysis["parsed_request"],
        status=analysis["status"],
        front_office_analysis=analysis.get("front_office_analysis"),
        recommendations=analysis.get("recommendations"),
        departments_consulted=analysis.get("departments_consulted", []),
        analysis_timestamp=analysis["created_at"].isoformat()
    )

@app.get("/api/analysis/{analysis_id}/status", response_model=TradeAnalysisStatus)
async def get_detailed_status(analysis_id: str):
    """Get detailed status of ongoing analysis"""
    
    if analysis_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = active_analyses[analysis_id]
    
    # Calculate progress
    completed_count = len(analysis.get("departments_consulted", []))
    progress = min(completed_count / len(DEPARTMENTS), 1.0)
    
    current_dept_index = analysis.get("current_department_index", 0)
    current_department = DEPARTMENTS[current_dept_index] if current_dept_index < len(DEPARTMENTS) else None
    
    return TradeAnalysisStatus(
        analysis_id=analysis_id,
        status=analysis["status"],
        progress=progress,
        current_department=current_department,
        completed_departments=analysis.get("departments_consulted", []),
        estimated_remaining_time=max(0, (len(DEPARTMENTS) - completed_count) * 10)  # 10 sec per dept
    )

@app.post("/api/quick-analysis")
async def quick_trade_analysis(request: TradeRequest):
    """
    Simplified synchronous analysis for immediate feedback
    """
    
    parsed_request = {
        "original_request": request.request,
        "primary_need": extract_primary_need(request.request),
        "position_type": "hitter",
        "specific_positions": ["outfield"],
        "player_attributes": {"power": True},
        "urgency": request.urgency or "exploratory",
        "confidence_score": 0.85
    }
    
    crew_prompt = f"""
    TRADE REQUEST: {request.request}
    
    PARSED ANALYSIS:
    - Primary Need: {parsed_request['primary_need']}
    - Team: {request.team}
    - Urgency: {parsed_request['urgency']}
    
    INSTRUCTIONS FOR FRONT OFFICE:
    1. Use all departments to identify suitable trade targets
    2. Consider organizational impact and constraints
    3. Structure realistic trade proposals
    4. Ensure MLB rule compliance
    """
    
    return {
        "team": request.team,
        "original_request": request.request,
        "parsed_analysis": parsed_request,
        "crew_prompt": crew_prompt,
        "confidence_score": parsed_request["confidence_score"],
        "recommended_next_steps": [
            "Run full front office analysis for comprehensive recommendations",
            "Consult scouting department for potential targets",
            "Review budget constraints with business operations",
            "Validate trade scenarios with commissioner office"
        ]
    }

async def simulate_analysis(analysis_id: str):
    """
    Simulate the front office analysis process
    """
    try:
        analysis = active_analyses[analysis_id]
        
        # Simulate each department working
        for i, department in enumerate(DEPARTMENTS):
            await asyncio.sleep(8)  # Simulate processing time
            
            analysis["current_department_index"] = i
            analysis["departments_consulted"].append(department)
            
            if department == "Commissioner Office":  # Last department
                # Generate mock recommendations
                recommendations = generate_mock_recommendations(analysis["original_request"], analysis["team"])
                
                analysis["status"] = "completed"
                analysis["front_office_analysis"] = {
                    "organizational_recommendation": "Trade analysis complete",
                    "departments_consulted": DEPARTMENTS
                }
                analysis["recommendations"] = recommendations
                analysis["completed_at"] = datetime.now()
                break
        
    except Exception as e:
        analysis["status"] = "error"
        analysis["error"] = str(e)
        analysis["completed_at"] = datetime.now()

def extract_primary_need(request: str) -> str:
    """Extract primary need from request"""
    request_lower = request.lower()
    
    if any(word in request_lower for word in ['power', 'bat', 'hitting', 'slugger']):
        return "power hitter"
    elif any(word in request_lower for word in ['pitcher', 'starting', 'rotation']):
        return "starting pitcher"
    elif any(word in request_lower for word in ['reliever', 'closer', 'bullpen']):
        return "relief pitcher"
    elif any(word in request_lower for word in ['shortstop', 'ss']):
        return "shortstop"
    elif any(word in request_lower for word in ['catcher']):
        return "catcher"
    else:
        return "position player"

def generate_mock_recommendations(request: str, team: str) -> List[Dict[str, Any]]:
    """Generate mock trade recommendations"""
    
    # Mock recommendations based on request
    mock_players = ["Pete Alonso", "Juan Soto", "Mookie Betts", "Freddie Freeman", "Aaron Judge"]
    mock_teams = ["Mets", "Padres", "Dodgers", "Braves", "Yankees"]
    
    recommendations = []
    
    for i in range(min(3, len(mock_players))):
        rec = {
            "priority": i + 1,
            "player_target": mock_players[i],
            "position": "First Base" if i == 0 else "Outfield",
            "current_team": mock_teams[i],
            "trade_package": [
                f"{team.title()} Prospect A",
                f"{team.title()} Prospect B", 
                "$5M cash considerations"
            ],
            "organizational_consensus": "Strong support from all departments",
            "key_benefits": [
                "Immediate impact player",
                "Proven track record",
                "Team control through 2025"
            ],
            "risks": [
                "High acquisition cost",
                "Injury history concerns",
                "Age considerations"
            ],
            "financial_impact": {
                "salary_added": 20000000 + (i * 5000000),
                "luxury_tax_impact": 22000000 + (i * 5500000),
                "playoff_revenue_upside": 15000000
            },
            "implementation_timeline": f"{2 + i}-{3 + i} weeks"
        }
        recommendations.append(rec)
    
    return recommendations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)