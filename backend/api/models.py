"""
Pydantic models for Baseball Trade AI API
Defines request/response models with proper validation
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class AnalysisStatus(str, Enum):
    """Trade analysis status enumeration"""
    QUEUED = "queued"
    ANALYZING = "analyzing" 
    COMPLETED = "completed"
    ERROR = "error"

class UrgencyLevel(str, Enum):
    """Trade urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CompetitiveWindow(str, Enum):
    """Team competitive window status"""
    REBUILD = "rebuild"
    RETOOL = "retool"
    WIN_NOW = "win-now"

class BudgetLevel(str, Enum):
    """Team budget levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class MarketSize(str, Enum):
    """Market size categories"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

# Request Models
class TradeRequestCreate(BaseModel):
    """Request model for creating a trade analysis"""
    team: str = Field(..., description="Requesting team key (e.g., 'yankees', 'dodgers')")
    request: str = Field(..., min_length=10, max_length=1000, description="Natural language trade request")
    urgency: UrgencyLevel = Field(UrgencyLevel.MEDIUM, description="Trade urgency level")
    budget_limit: Optional[float] = Field(None, gt=0, description="Maximum additional salary to take on")
    include_prospects: bool = Field(True, description="Whether to consider trading prospects")
    max_trade_partners: int = Field(2, ge=1, le=4, description="Maximum number of teams in trade")
    additional_context: Optional[str] = Field(None, max_length=500, description="Additional context for analysis")

    @validator('team')
    def validate_team_format(cls, v):
        """Ensure team is in proper format"""
        return v.lower().strip()

    @validator('request')
    def validate_request_content(cls, v):
        """Validate trade request has meaningful content"""
        if len(v.strip()) < 10:
            raise ValueError("Trade request must be at least 10 characters")
        return v.strip()

class QuickAnalysisRequest(BaseModel):
    """Request model for quick trade analysis"""
    team: str = Field(..., description="Requesting team key")
    request: str = Field(..., min_length=5, description="Trade request")

# Response Models  
class TeamInfo(BaseModel):
    """Team information response model"""
    id: int
    team_key: str
    name: str
    abbreviation: str
    city: str
    division: str
    league: str
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    budget_level: BudgetLevel
    competitive_window: CompetitiveWindow
    market_size: MarketSize
    philosophy: Optional[str] = None

class PlayerInfo(BaseModel):
    """Player information model"""
    id: int
    name: str
    team_id: int
    position: Optional[str] = None
    age: Optional[int] = None
    salary: Optional[float] = None
    contract_years: Optional[int] = None
    war: Optional[float] = None
    stats: Optional[Dict[str, Any]] = None

class TradeAnalysisProgress(BaseModel):
    """Progress tracking for trade analysis"""
    current_step: str
    completed_steps: List[str]
    total_steps: int
    progress_percentage: float
    estimated_remaining_time: Optional[int] = None  # seconds
    current_department: Optional[str] = None

class TradeProposal(BaseModel):
    """Individual trade proposal model"""
    id: Optional[int] = None
    proposal_rank: int
    teams_involved: List[Dict[str, Any]]
    players_involved: List[Dict[str, Any]]
    likelihood: str
    financial_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    summary: Optional[str] = None

class CostInfo(BaseModel):
    """Cost tracking for AI analysis"""
    total_tokens_used: int
    cost_usd: float
    model_used: str
    analysis_duration_seconds: float

class TradeAnalysisResponse(BaseModel):
    """Complete trade analysis response"""
    analysis_id: str
    team: str
    original_request: str
    status: AnalysisStatus
    progress: Optional[TradeAnalysisProgress] = None
    results: Optional[Dict[str, Any]] = None
    proposals: Optional[List[TradeProposal]] = None
    cost_info: Optional[CostInfo] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    departments_consulted: List[str] = []

class TradeAnalysisStatus(BaseModel):
    """Status-only response for analysis tracking"""
    analysis_id: str
    status: AnalysisStatus
    progress: Optional[TradeAnalysisProgress] = None
    estimated_completion: Optional[datetime] = None

class QuickAnalysisResponse(BaseModel):
    """Quick analysis response with basic insights"""
    team: str
    original_request: str
    parsed_request: Dict[str, Any]
    confidence_score: float
    initial_assessment: str
    recommended_next_steps: List[str]
    crew_prompt: Optional[str] = None

# System Models
class SystemHealth(BaseModel):
    """System health check response"""
    service: str
    version: str
    status: str
    timestamp: datetime
    available_teams: List[str]
    departments: List[str]
    database_status: str
    cache_status: Optional[str] = None
    active_analyses: int

class TeamsResponse(BaseModel):
    """Response for teams endpoint"""
    teams: List[TeamInfo]
    total_teams: int
    source: str = "database"

class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    detail: str
    request_id: Optional[str] = None
    timestamp: datetime
    path: Optional[str] = None

# Analysis Progress Models
class DepartmentProgress(BaseModel):
    """Progress for individual department"""
    name: str
    status: str  # 'pending', 'in_progress', 'completed', 'error'
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    findings: List[str] = []
    recommendations: List[str] = []

class AnalysisProgressDetailed(BaseModel):
    """Detailed progress tracking"""
    analysis_id: str
    status: AnalysisStatus
    overall_progress: float
    departments: List[DepartmentProgress]
    current_department: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    total_runtime_seconds: Optional[float] = None

# Configuration Models
class AnalysisConfiguration(BaseModel):
    """Configuration options for trade analysis"""
    max_analysis_time_seconds: int = 300
    include_international_prospects: bool = True
    salary_flexibility_percentage: float = 10.0
    risk_tolerance: str = "medium"  # low, medium, high
    focus_areas: List[str] = []  # e.g., ['pitching', 'offense', 'defense']
    exclude_no_trade_clauses: bool = True

# Validation Models
class TradeValidation(BaseModel):
    """Trade proposal validation results"""
    is_valid: bool
    violations: List[str] = []
    warnings: List[str] = []
    salary_impact: Dict[str, float]
    roster_impact: Dict[str, Any]
    luxury_tax_implications: Dict[str, Any]

# Database Models (for internal use)
class TradeAnalysisDB(BaseModel):
    """Database model for trade analyses"""
    id: Optional[int] = None
    analysis_id: str
    requesting_team_id: int
    request_text: str
    urgency: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    cost_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class TradeProposalDB(BaseModel):
    """Database model for trade proposals"""
    id: Optional[int] = None
    analysis_id: int
    proposal_rank: int
    teams_involved: List[Dict[str, Any]]
    players_involved: List[Dict[str, Any]]
    likelihood: str
    financial_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True