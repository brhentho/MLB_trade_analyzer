"""
Global test configuration and fixtures for Baseball Trade AI Backend
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import application modules
from api.trade_analyzer_v2 import app
from api.models import (
    TradeRequestCreate, TradeAnalysisResponse, AnalysisStatus,
    UrgencyLevel, TeamInfo, TradeProposal, SystemHealth
)
from services.supabase_service import supabase_service, TradeAnalysisRecord
from crews.front_office_crew import FrontOfficeCrew
from nlp.trade_parser import TradeRequestParser

# Test data fixtures
@pytest.fixture
def sample_team_data():
    """Sample team data for testing"""
    return {
        'id': 1,
        'team_key': 'yankees',
        'name': 'New York Yankees',
        'abbreviation': 'NYY',
        'city': 'New York',
        'division': 'AL East',
        'league': 'American League',
        'primary_color': '#132448',
        'secondary_color': '#C4CED4',
        'budget_level': 'high',
        'competitive_window': 'win-now',
        'market_size': 'large',
        'philosophy': 'Win championships through strategic acquisitions'
    }

@pytest.fixture
def sample_teams_data():
    """Sample teams collection for testing"""
    return [
        {
            'id': 1,
            'team_key': 'yankees',
            'name': 'New York Yankees',
            'abbreviation': 'NYY',
            'city': 'New York',
            'division': 'AL East',
            'league': 'American League',
            'budget_level': 'high',
            'competitive_window': 'win-now',
            'market_size': 'large'
        },
        {
            'id': 2,
            'team_key': 'dodgers',
            'name': 'Los Angeles Dodgers',
            'abbreviation': 'LAD',
            'city': 'Los Angeles',
            'division': 'NL West',
            'league': 'National League',
            'budget_level': 'high',
            'competitive_window': 'win-now',
            'market_size': 'large'
        },
        {
            'id': 3,
            'team_key': 'rays',
            'name': 'Tampa Bay Rays',
            'abbreviation': 'TB',
            'city': 'Tampa Bay',
            'division': 'AL East',
            'league': 'American League',
            'budget_level': 'low',
            'competitive_window': 'win-now',
            'market_size': 'small'
        }
    ]

@pytest.fixture
def valid_trade_request():
    """Valid trade request for testing"""
    return TradeRequestCreate(
        team="yankees",
        request="We need a starting pitcher with ERA under 3.50 for the playoff push",
        urgency=UrgencyLevel.HIGH,
        budget_limit=50000000.0,
        include_prospects=True,
        max_trade_partners=2
    )

@pytest.fixture
def sample_trade_analysis_record():
    """Sample trade analysis record"""
    return TradeAnalysisRecord(
        analysis_id=str(uuid.uuid4()),
        requesting_team_id=1,
        request_text="Need a starting pitcher",
        urgency="high",
        status=AnalysisStatus.QUEUED.value
    )

@pytest.fixture
def sample_crew_ai_result():
    """Mock CrewAI analysis result"""
    return {
        "organizational_recommendation": {
            "priority_targets": [
                {
                    "player": "Shane Bieber",
                    "team": "Guardians",
                    "position": "SP",
                    "confidence": 0.85
                }
            ],
            "trade_packages": [
                {
                    "giving": ["Prospect A", "Prospect B"],
                    "receiving": ["Shane Bieber"],
                    "likelihood": "medium"
                }
            ]
        },
        "departments_consulted": [
            "Front Office Leadership",
            "Scouting Department",
            "Analytics Department"
        ],
        "token_usage": 15000,
        "estimated_cost": 0.30,
        "duration_seconds": 45.2
    }

@pytest.fixture
def sample_trade_proposals():
    """Sample trade proposals"""
    return [
        {
            "proposal_rank": 1,
            "teams_involved": [
                {"team": "yankees", "role": "acquiring"},
                {"team": "guardians", "role": "trading"}
            ],
            "players_involved": [
                {"player": "Shane Bieber", "from_team": "guardians", "to_team": "yankees"},
                {"player": "Prospect A", "from_team": "yankees", "to_team": "guardians"},
                {"player": "Prospect B", "from_team": "yankees", "to_team": "guardians"}
            ],
            "likelihood": "medium",
            "financial_impact": {
                "salary_added": 15000000,
                "luxury_tax_impact": 2000000
            },
            "risk_assessment": {
                "risk_level": "medium",
                "concerns": ["injury_history", "contract_year"]
            },
            "summary": "High-impact ace acquisition for playoff push"
        }
    ]

# Application fixtures
@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Mock fixtures
@pytest.fixture
def mock_supabase_service():
    """Mock Supabase service"""
    mock = AsyncMock(spec=supabase_service)
    mock.health_check.return_value = {"status": "healthy"}
    mock.get_all_teams.return_value = []
    mock.get_team_by_key.return_value = None
    mock.get_team_by_id.return_value = None
    mock.create_trade_analysis.return_value = 1
    mock.get_trade_analysis.return_value = None
    mock.update_trade_analysis_status.return_value = True
    mock.get_trade_proposals.return_value = []
    mock.create_trade_proposals.return_value = True
    mock.get_recent_trade_analyses.return_value = []
    return mock

@pytest.fixture
def mock_front_office_crew():
    """Mock Front Office Crew"""
    mock = AsyncMock(spec=FrontOfficeCrew)
    mock.analyze_trade_request.return_value = {
        "organizational_recommendation": "Mock analysis complete",
        "departments_consulted": ["Front Office", "Analytics"],
        "token_usage": 1000,
        "estimated_cost": 0.02
    }
    return mock

@pytest.fixture
def mock_trade_parser():
    """Mock Trade Parser"""
    mock = Mock(spec=TradeRequestParser)
    mock.parse_trade_request.return_value = Mock(
        primary_need="starting_pitcher",
        secondary_needs=["bullpen_depth"],
        urgency_level="high",
        budget_constraints=50000000,
        trade_preference="veteran",
        confidence_score=0.9,
        raw_request="Need a starting pitcher"
    )
    mock.generate_crew_prompt.return_value = "Analyze trade request for starting pitcher"
    return mock

# Database fixtures
@pytest.fixture
async def clean_database():
    """Ensure clean database state for testing"""
    # In a real implementation, this would clean test database
    # For now, we'll use mocks
    yield
    # Cleanup code would go here

# Authentication fixtures
@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json"
    }

# Error simulation fixtures
@pytest.fixture
def mock_database_error():
    """Mock database connection error"""
    return Exception("Database connection failed")

@pytest.fixture
def mock_crew_ai_error():
    """Mock CrewAI processing error"""
    return Exception("CrewAI analysis timeout")

@pytest.fixture
def mock_timeout_error():
    """Mock timeout error"""
    return asyncio.TimeoutError("Operation timed out")

# Performance testing fixtures
@pytest.fixture
def performance_trade_requests():
    """Large batch of trade requests for performance testing"""
    return [
        TradeRequestCreate(
            team=f"team_{i}",
            request=f"Need player type {i % 5}",
            urgency=UrgencyLevel.MEDIUM
        )
        for i in range(100)
    ]

# Security testing fixtures
@pytest.fixture
def malicious_inputs():
    """Collection of potentially malicious inputs for security testing"""
    return [
        # SQL injection attempts
        "'; DROP TABLE teams; --",
        "' OR '1'='1",
        
        # XSS attempts
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        
        # Path traversal
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        
        # Command injection
        "; ls -la",
        "| cat /etc/passwd",
        
        # Long strings (buffer overflow)
        "A" * 10000,
        
        # Null bytes
        "test\x00.txt",
        
        # Unicode issues
        "\u0000\u0001\u0002",
    ]

# Environment fixtures
@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("SUPABASE_URL", "http://test-supabase.com")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test_service_key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("ENVIRONMENT", "testing")

# Mock external services
@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls"""
    with patch('openai.ChatCompletion.acreate') as mock:
        mock.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Mock OpenAI response"
                    }
                }
            ],
            "usage": {
                "total_tokens": 100
            }
        }
        yield mock

@pytest.fixture
def mock_redis():
    """Mock Redis cache"""
    mock = Mock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    with patch('redis.Redis', return_value=mock):
        yield mock

# Async test utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async testing"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Custom assertions and utilities
@pytest.fixture
def assert_valid_uuid():
    """Helper to assert valid UUID format"""
    def _assert_valid_uuid(uuid_string: str):
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    return _assert_valid_uuid

@pytest.fixture
def assert_valid_timestamp():
    """Helper to assert valid timestamp format"""
    def _assert_valid_timestamp(timestamp_string: str):
        try:
            datetime.fromisoformat(timestamp_string.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    return _assert_valid_timestamp

# Test data factories
class TradeRequestFactory:
    """Factory for creating test trade requests"""
    
    @staticmethod
    def create(team: str = "yankees", **kwargs) -> TradeRequestCreate:
        defaults = {
            "team": team,
            "request": "Need a starting pitcher with good ERA",
            "urgency": UrgencyLevel.MEDIUM,
            "budget_limit": 30000000.0,
            "include_prospects": True,
            "max_trade_partners": 2
        }
        defaults.update(kwargs)
        return TradeRequestCreate(**defaults)
    
    @staticmethod
    def create_batch(count: int = 10) -> List[TradeRequestCreate]:
        teams = ["yankees", "dodgers", "astros", "braves", "mets"]
        return [
            TradeRequestFactory.create(
                team=teams[i % len(teams)],
                request=f"Trade request {i + 1}"
            )
            for i in range(count)
        ]

@pytest.fixture
def trade_request_factory():
    """Trade request factory fixture"""
    return TradeRequestFactory

# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup():
    """Automatic cleanup after each test"""
    yield
    # Reset any global state
    # Clear caches
    # Reset mocks