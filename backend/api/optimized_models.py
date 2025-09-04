"""
Optimized Pydantic Models for Baseball Trade AI
Advanced validation, serialization optimizations, and performance enhancements
"""

import re
import json
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from enum import Enum

from pydantic import (
    BaseModel, Field, validator, root_validator, 
    EmailStr, HttpUrl, constr, conint, confloat
)
from pydantic.config import BaseConfig


# Custom configuration for optimal performance
class OptimizedConfig(BaseConfig):
    """Optimized Pydantic configuration for production"""
    # Performance optimizations
    allow_reuse=True  # Enable model reuse for better performance
    validate_assignment=True  # Validate on assignment
    use_enum_values=True  # Use enum values in output
    allow_population_by_field_name=True  # Allow field name population
    
    # Serialization optimizations
    json_encoders = {
        datetime: lambda v: v.isoformat(),
        date: lambda v: v.isoformat(),
        Decimal: lambda v: float(v),
        set: list  # Convert sets to lists in JSON
    }
    
    # Schema customization
    schema_extra = {
        "example": "See individual model examples"
    }


# Enhanced Enum classes with validation
class AnalysisStatus(str, Enum):
    """Trade analysis status with validation"""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    @classmethod
    def active_statuses(cls) -> Set[str]:
        """Get statuses that indicate active processing"""
        return {cls.QUEUED.value, cls.ANALYZING.value, cls.PROCESSING.value}

    @classmethod
    def terminal_statuses(cls) -> Set[str]:
        """Get statuses that indicate completion"""
        return {cls.COMPLETED.value, cls.ERROR.value, cls.CANCELLED.value, cls.EXPIRED.value}


class UrgencyLevel(str, Enum):
    """Trade urgency levels with priority mapping"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

    def get_priority_score(self) -> int:
        """Get numeric priority for sorting"""
        priority_map = {
            self.LOW: 1,
            self.MEDIUM: 2, 
            self.HIGH: 3,
            self.CRITICAL: 4
        }
        return priority_map.get(self, 2)


class PlayerPosition(str, Enum):
    """Baseball positions with validation"""
    # Pitchers
    SP = "SP"  # Starting Pitcher
    RP = "RP"  # Relief Pitcher
    CL = "CL"  # Closer
    
    # Position Players
    C = "C"    # Catcher
    FB = "1B"  # First Base
    SB = "2B"  # Second Base
    TB = "3B"  # Third Base
    SS = "SS"  # Shortstop
    LF = "LF"  # Left Field
    CF = "CF"  # Center Field
    RF = "RF"  # Right Field
    DH = "DH"  # Designated Hitter
    
    # Utility
    IF = "IF"  # Infielder
    OF = "OF"  # Outfielder
    UTIL = "UTIL"  # Utility Player

    @classmethod
    def infield_positions(cls) -> Set[str]:
        """Get infield positions"""
        return {cls.FB.value, cls.SB.value, cls.TB.value, cls.SS.value, cls.C.value}

    @classmethod
    def outfield_positions(cls) -> Set[str]:
        """Get outfield positions"""
        return {cls.LF.value, cls.CF.value, cls.RF.value}

    @classmethod
    def pitching_positions(cls) -> Set[str]:
        """Get pitching positions"""
        return {cls.SP.value, cls.RP.value, cls.CL.value}


# Custom validators and field types
def validate_team_key(v: str) -> str:
    """Validate and normalize team key"""
    if not v:
        raise ValueError("Team key cannot be empty")
    
    # Normalize to lowercase, remove spaces and special chars
    normalized = re.sub(r'[^a-zA-Z0-9_-]', '', v.lower().strip())
    
    if len(normalized) < 2:
        raise ValueError("Team key must be at least 2 characters")
    
    if len(normalized) > 20:
        raise ValueError("Team key must be less than 20 characters")
    
    return normalized


def validate_salary(v: Optional[float]) -> Optional[float]:
    """Validate salary values"""
    if v is None:
        return None
    
    if v < 0:
        raise ValueError("Salary cannot be negative")
    
    if v > 1_000_000_000:  # $1B cap for sanity
        raise ValueError("Salary exceeds maximum allowed value")
    
    return round(v, 2)  # Round to cents


def validate_player_name(v: str) -> str:
    """Validate and clean player names"""
    if not v or not v.strip():
        raise ValueError("Player name cannot be empty")
    
    # Clean name - remove extra spaces, special chars except common ones
    cleaned = re.sub(r'[^\w\s\'-.]', '', v.strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
    
    if len(cleaned) < 2:
        raise ValueError("Player name must be at least 2 characters")
    
    if len(cleaned) > 50:
        raise ValueError("Player name too long")
    
    return cleaned.title()  # Title case


# Optimized Request Models
class TradeRequestCreate(BaseModel):
    """Optimized trade analysis request model"""
    team: constr(min_length=2, max_length=20) = Field(
        ...,
        description="Requesting team key",
        example="dodgers"
    )
    request: constr(min_length=10, max_length=2000) = Field(
        ...,
        description="Natural language trade request",
        example="Need a starting pitcher with ERA under 3.50 and at least 2 years of control"
    )
    urgency: UrgencyLevel = Field(
        UrgencyLevel.MEDIUM,
        description="Trade urgency level"
    )
    budget_limit: Optional[confloat(gt=0, le=500_000_000)] = Field(
        None,
        description="Maximum additional salary to take on (USD)"
    )
    include_prospects: bool = Field(
        True,
        description="Whether to consider trading prospects"
    )
    max_trade_partners: conint(ge=1, le=4) = Field(
        2,
        description="Maximum number of teams in trade"
    )
    additional_context: Optional[constr(max_length=1000)] = Field(
        None,
        description="Additional context for analysis"
    )
    preferred_positions: Optional[List[PlayerPosition]] = Field(
        None,
        description="Preferred positions if targeting position players"
    )
    max_contract_years: Optional[conint(ge=1, le=10)] = Field(
        None,
        description="Maximum contract years for acquired players"
    )
    
    # Custom validators
    @validator('team')
    def validate_team_format(cls, v):
        return validate_team_key(v)
    
    @validator('request')
    def validate_request_content(cls, v):
        """Enhanced request validation"""
        v = v.strip()
        
        # Check for minimum meaningful content
        words = v.split()
        if len(words) < 3:
            raise ValueError("Trade request must contain at least 3 words")
        
        # Check for prohibited content (basic)
        prohibited_words = ['hack', 'exploit', 'script', '<script', 'javascript:']
        if any(word.lower() in v.lower() for word in prohibited_words):
            raise ValueError("Request contains prohibited content")
        
        return v
    
    @root_validator
    def validate_position_context(cls, values):
        """Validate position-specific context"""
        positions = values.get('preferred_positions', [])
        request_text = values.get('request', '').lower()
        
        # If requesting pitchers, validate pitcher-specific logic
        if any(pos in PlayerPosition.pitching_positions() for pos in positions):
            if 'batting' in request_text or 'hitting' in request_text:
                raise ValueError("Conflicting request: requesting pitcher but mentioning hitting stats")
        
        return values

    class Config(OptimizedConfig):
        schema_extra = {
            "example": {
                "team": "dodgers",
                "request": "Need a starting pitcher with ERA under 3.50 for playoff push",
                "urgency": "high",
                "budget_limit": 25000000,
                "include_prospects": True,
                "max_trade_partners": 2,
                "preferred_positions": ["SP"],
                "max_contract_years": 3
            }
        }


class QuickAnalysisRequest(BaseModel):
    """Lightweight request for quick analysis"""
    team: constr(min_length=2, max_length=20) = Field(..., description="Team key")
    request: constr(min_length=5, max_length=500) = Field(..., description="Quick request")
    
    @validator('team')
    def validate_team_format(cls, v):
        return validate_team_key(v)

    class Config(OptimizedConfig):
        pass


# Enhanced Response Models
class PlayerInfo(BaseModel):
    """Optimized player information model"""
    id: int = Field(..., description="Player database ID")
    name: str = Field(..., description="Player full name")
    position: Optional[PlayerPosition] = Field(None, description="Primary position")
    team_id: int = Field(..., description="Current team ID")
    age: Optional[conint(ge=16, le=50)] = Field(None, description="Player age")
    salary: Optional[confloat(ge=0)] = Field(None, description="Current salary (USD)")
    contract_years: Optional[conint(ge=0, le=15)] = Field(None, description="Years remaining on contract")
    war: Optional[confloat(ge=-10, le=15)] = Field(None, description="Wins Above Replacement")
    is_prospect: bool = Field(False, description="Whether player is a prospect")
    no_trade_clause: bool = Field(False, description="Has no-trade clause")
    
    # Advanced stats (optional)
    stats_current_season: Optional[Dict[str, Union[float, int]]] = Field(
        None,
        description="Current season statistics"
    )
    stats_career: Optional[Dict[str, Union[float, int]]] = Field(
        None,
        description="Career statistics"
    )
    
    @validator('name')
    def validate_name(cls, v):
        return validate_player_name(v)
    
    @validator('salary')
    def validate_salary_amount(cls, v):
        return validate_salary(v)

    class Config(OptimizedConfig):
        schema_extra = {
            "example": {
                "id": 12345,
                "name": "Mike Trout",
                "position": "CF",
                "team_id": 1,
                "age": 31,
                "salary": 37116666,
                "contract_years": 8,
                "war": 8.3,
                "is_prospect": False,
                "no_trade_clause": True
            }
        }


class TeamInfo(BaseModel):
    """Enhanced team information model"""
    id: int = Field(..., description="Team database ID")
    team_key: str = Field(..., description="Team key identifier")
    name: str = Field(..., description="Team full name")
    abbreviation: constr(min_length=2, max_length=5) = Field(..., description="Team abbreviation")
    city: str = Field(..., description="Team city")
    division: str = Field(..., description="Division")
    league: str = Field(..., description="League (AL/NL)")
    
    # Team characteristics
    budget_level: str = Field(..., description="Budget level (low/medium/high)")
    competitive_window: str = Field(..., description="Competitive status")
    market_size: str = Field(..., description="Market size category")
    philosophy: Optional[str] = Field(None, description="Team philosophy")
    
    # Colors for UI
    primary_color: Optional[str] = Field(None, description="Primary team color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary team color (hex)")
    
    # Advanced team metrics
    payroll_total: Optional[confloat(ge=0)] = Field(None, description="Total payroll (USD)")
    luxury_tax_status: Optional[str] = Field(None, description="Luxury tax status")
    farm_system_ranking: Optional[conint(ge=1, le=30)] = Field(None, description="Farm system rank")
    
    @validator('team_key')
    def validate_key(cls, v):
        return validate_team_key(v)
    
    @validator('abbreviation')
    def validate_abbreviation(cls, v):
        return v.upper()
    
    @validator('league') 
    def validate_league(cls, v):
        if v.upper() not in ['AL', 'NL']:
            raise ValueError("League must be AL or NL")
        return v.upper()

    class Config(OptimizedConfig):
        schema_extra = {
            "example": {
                "id": 1,
                "team_key": "dodgers",
                "name": "Los Angeles Dodgers",
                "abbreviation": "LAD",
                "city": "Los Angeles",
                "division": "NL West",
                "league": "NL",
                "budget_level": "high",
                "competitive_window": "win-now",
                "market_size": "large",
                "payroll_total": 285000000
            }
        }


class TradeProposal(BaseModel):
    """Optimized trade proposal model"""
    id: Optional[int] = Field(None, description="Proposal ID")
    proposal_rank: conint(ge=1, le=10) = Field(..., description="Proposal ranking")
    
    # Teams and players involved
    teams_involved: List[Dict[str, Any]] = Field(
        ...,
        description="Teams participating in trade",
        min_items=2,
        max_items=4
    )
    players_involved: List[Dict[str, Any]] = Field(
        ...,
        description="Players in the trade",
        min_items=1
    )
    
    # Analysis results
    likelihood: str = Field(..., description="Trade likelihood (low/medium/high)")
    confidence_score: confloat(ge=0, le=1) = Field(
        ...,
        description="AI confidence in the proposal"
    )
    
    # Impact assessments
    financial_impact: Dict[str, Any] = Field(..., description="Financial implications")
    competitive_impact: Dict[str, Any] = Field(..., description="Competitive impact")
    risk_assessment: Dict[str, Any] = Field(..., description="Risk analysis")
    
    # Trade details
    summary: Optional[str] = Field(None, description="Trade summary")
    rationale: Optional[str] = Field(None, description="Why this trade makes sense")
    potential_obstacles: List[str] = Field(default_factory=list, description="Potential issues")
    
    # Timeline
    optimal_timing: Optional[str] = Field(None, description="Best time to execute")
    deadline_pressure: Optional[bool] = Field(None, description="Time-sensitive trade")

    class Config(OptimizedConfig):
        schema_extra = {
            "example": {
                "proposal_rank": 1,
                "teams_involved": [
                    {"team": "dodgers", "role": "acquiring"},
                    {"team": "guardians", "role": "trading"}
                ],
                "likelihood": "medium",
                "confidence_score": 0.75,
                "summary": "Dodgers acquire starting pitcher for prospects"
            }
        }


class CostInfo(BaseModel):
    """AI analysis cost tracking"""
    total_tokens_used: conint(ge=0) = Field(..., description="Total tokens consumed")
    cost_usd: confloat(ge=0) = Field(..., description="Estimated cost in USD")
    model_used: str = Field(..., description="AI model used")
    analysis_duration_seconds: confloat(ge=0) = Field(..., description="Analysis duration")
    
    # Token breakdown
    prompt_tokens: Optional[conint(ge=0)] = Field(None, description="Prompt tokens")
    completion_tokens: Optional[conint(ge=0)] = Field(None, description="Completion tokens")
    
    # Cost efficiency metrics
    tokens_per_second: Optional[confloat(ge=0)] = Field(None, description="Processing rate")
    cost_per_proposal: Optional[confloat(ge=0)] = Field(None, description="Cost per proposal generated")

    @root_validator
    def calculate_efficiency_metrics(cls, values):
        """Calculate derived efficiency metrics"""
        duration = values.get('analysis_duration_seconds', 0)
        total_tokens = values.get('total_tokens_used', 0)
        
        if duration > 0 and total_tokens > 0:
            values['tokens_per_second'] = round(total_tokens / duration, 2)
        
        return values

    class Config(OptimizedConfig):
        pass


class TradeAnalysisResponse(BaseModel):
    """Comprehensive trade analysis response"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    team: str = Field(..., description="Requesting team")
    original_request: str = Field(..., description="Original trade request")
    status: AnalysisStatus = Field(..., description="Current analysis status")
    
    # Progress tracking
    progress: Optional[Dict[str, Any]] = Field(None, description="Analysis progress")
    current_step: Optional[str] = Field(None, description="Current processing step")
    
    # Results
    results: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    proposals: Optional[List[TradeProposal]] = Field(None, description="Trade proposals")
    cost_info: Optional[CostInfo] = Field(None, description="Analysis cost information")
    
    # Metadata
    created_at: datetime = Field(..., description="Analysis creation time")
    completed_at: Optional[datetime] = Field(None, description="Analysis completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    departments_consulted: List[str] = Field(default_factory=list, description="Departments involved")
    
    # Performance metrics
    total_processing_time: Optional[confloat(ge=0)] = Field(None, description="Total processing time")
    cache_hits: Optional[conint(ge=0)] = Field(None, description="Number of cache hits")

    @root_validator
    def calculate_processing_time(cls, values):
        """Calculate total processing time"""
        created = values.get('created_at')
        completed = values.get('completed_at')
        
        if created and completed:
            delta = completed - created
            values['total_processing_time'] = delta.total_seconds()
        
        return values
    
    @validator('analysis_id')
    def validate_analysis_id(cls, v):
        # Basic UUID format validation
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', v):
            raise ValueError("Invalid analysis ID format")
        return v

    class Config(OptimizedConfig):
        schema_extra = {
            "example": {
                "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
                "team": "dodgers",
                "original_request": "Need starting pitcher",
                "status": "completed",
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:03:45Z"
            }
        }


# System and utility models
class ValidationResult(BaseModel):
    """Validation result model"""
    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    field_errors: Dict[str, List[str]] = Field(default_factory=dict, description="Field-specific errors")

    @property
    def has_errors(self) -> bool:
        """Check if there are any validation errors"""
        return len(self.errors) > 0 or len(self.field_errors) > 0

    class Config(OptimizedConfig):
        pass


class SystemHealth(BaseModel):
    """System health status model"""
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    uptime_seconds: confloat(ge=0) = Field(..., description="System uptime")
    
    # Component health
    database_status: str = Field(..., description="Database health")
    cache_status: str = Field(..., description="Cache system health")
    queue_status: str = Field(..., description="Queue system health")
    
    # Metrics
    active_analyses: conint(ge=0) = Field(..., description="Currently active analyses")
    total_requests: conint(ge=0) = Field(..., description="Total requests served")
    error_rate: confloat(ge=0, le=1) = Field(..., description="Current error rate")

    class Config(OptimizedConfig):
        pass


# Batch operation models for performance
class BatchTradeRequest(BaseModel):
    """Batch trade analysis request"""
    requests: List[TradeRequestCreate] = Field(
        ...,
        description="Batch of trade requests",
        min_items=1,
        max_items=10  # Limit batch size
    )
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    parallel_processing: bool = Field(True, description="Process requests in parallel")

    class Config(OptimizedConfig):
        pass


class BatchTradeResponse(BaseModel):
    """Batch trade analysis response"""
    batch_id: str = Field(..., description="Batch identifier") 
    total_requests: conint(ge=1) = Field(..., description="Total number of requests")
    completed: conint(ge=0) = Field(..., description="Number of completed analyses")
    failed: conint(ge=0) = Field(..., description="Number of failed analyses")
    
    results: List[TradeAnalysisResponse] = Field(..., description="Individual analysis results")
    batch_cost: Optional[CostInfo] = Field(None, description="Total batch cost")
    processing_time: confloat(ge=0) = Field(..., description="Total batch processing time")

    class Config(OptimizedConfig):
        pass


# Export commonly used models
__all__ = [
    'AnalysisStatus', 'UrgencyLevel', 'PlayerPosition',
    'TradeRequestCreate', 'QuickAnalysisRequest', 
    'PlayerInfo', 'TeamInfo', 'TradeProposal', 'CostInfo',
    'TradeAnalysisResponse', 'ValidationResult', 'SystemHealth',
    'BatchTradeRequest', 'BatchTradeResponse'
]