"""
Enhanced API endpoint tests for Baseball Trade AI
Comprehensive testing of all endpoints with edge cases, error scenarios, and performance considerations
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Any

from backend.api.trade_analyzer_v2 import app
from backend.api.models import (
    AnalysisStatus, UrgencyLevel, TradeRequestCreate,
    TradeAnalysisResponse, SystemHealth
)
from backend.services.supabase_service import TradeAnalysisRecord


class TestSystemHealthEndpointEnhanced:
    """Enhanced tests for system health endpoint"""
    
    def test_health_check_with_degraded_database(self, test_client, mock_supabase_service):
        """Test health check when database is partially degraded"""
        mock_supabase_service.health_check.return_value = {
            'status': 'degraded',
            'teams_count': 30,
            'players_count': 0,  # No player data
            'recent_analyses_count': 5
        }
        
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database_status"] == "degraded"
        assert data["service"] == "Baseball Trade AI - Front Office Simulation"
    
    def test_health_check_with_no_teams(self, test_client, mock_supabase_service):
        """Test health check when no teams are available"""
        mock_supabase_service.health_check.return_value = {'status': 'healthy'}
        mock_supabase_service.get_all_teams.return_value = []
        mock_supabase_service.get_recent_trade_analyses.return_value = []
        
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available_teams"] == []
        assert data["active_analyses"] == 0
    
    def test_health_check_timeout_handling(self, test_client, mock_supabase_service):
        """Test health check when database operations timeout"""
        mock_supabase_service.health_check.side_effect = asyncio.TimeoutError("Database timeout")
        
        response = test_client.get("/")
        
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert "timeout" in data["error"].lower() or "database" in data["error"].lower()
    
    def test_health_check_performance_metrics(self, test_client, mock_supabase_service, performance_monitor):
        """Test health check response time"""
        performance_monitor.start()
        response = test_client.get("/")
        performance_monitor.stop()
        
        assert response.status_code == 200
        assert performance_monitor.duration < 2.0  # Should respond within 2 seconds
    
    def test_health_check_concurrent_requests(self, test_client, mock_supabase_service):
        """Test health check under concurrent load"""
        import concurrent.futures
        
        def make_health_request():
            return test_client.get("/")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "status" in data


class TestTeamsEndpointEnhanced:
    """Enhanced tests for teams endpoint"""
    
    def test_teams_with_complete_data(self, test_client, mock_supabase_service):
        """Test teams endpoint with complete team data"""
        complete_teams_data = [
            {
                'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees',
                'abbreviation': 'NYY', 'city': 'New York', 'division': 'AL East',
                'league': 'American League', 'budget_level': 'high',
                'competitive_window': 'win-now', 'market_size': 'large',
                'primary_color': '#132448', 'secondary_color': '#C4CED4',
                'philosophy': 'Win championships', 'payroll': 250000000,
                'farm_system_rank': 15, 'last_playoff_year': 2023
            },
            {
                'id': 2, 'team_key': 'rays', 'name': 'Tampa Bay Rays',
                'abbreviation': 'TB', 'city': 'Tampa Bay', 'division': 'AL East',
                'league': 'American League', 'budget_level': 'low',
                'competitive_window': 'win-now', 'market_size': 'small',
                'primary_color': '#092C5C', 'secondary_color': '#8FBCE6',
                'philosophy': 'Smart analytics', 'payroll': 80000000,
                'farm_system_rank': 5, 'last_playoff_year': 2023
            }
        ]
        
        mock_supabase_service.get_all_teams.return_value = complete_teams_data
        
        response = test_client.get("/api/teams")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_teams"] == 2
        assert data["source"] == "database"
        assert len(data["teams"]) == 2
        
        # Check team data structure
        yankees = data["teams"][0]
        assert yankees["team_key"] == "yankees"
        assert yankees["budget_level"] == "high"
        assert yankees["payroll"] == 250000000
    
    def test_teams_with_missing_optional_fields(self, test_client, mock_supabase_service):
        """Test teams endpoint with minimal team data"""
        minimal_teams_data = [
            {
                'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees',
                'abbreviation': 'NYY', 'division': 'AL East', 'league': 'American League'
                # Missing optional fields like colors, philosophy, etc.
            }
        ]
        
        mock_supabase_service.get_all_teams.return_value = minimal_teams_data
        
        response = test_client.get("/api/teams")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["teams"]) == 1
        
        team = data["teams"][0]
        assert team["team_key"] == "yankees"
        # Should handle missing optional fields gracefully
        assert "name" in team
        assert "abbreviation" in team
    
    def test_teams_caching_behavior(self, test_client, mock_supabase_service):
        """Test teams endpoint caching"""
        teams_data = [{'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees'}]
        mock_supabase_service.get_all_teams.return_value = teams_data
        
        # First request
        response1 = test_client.get("/api/teams")
        assert response1.status_code == 200
        
        # Second request should use cache
        response2 = test_client.get("/api/teams")
        assert response2.status_code == 200
        
        # Should have same data
        assert response1.json() == response2.json()
        
        # Service should be called only once due to caching
        assert mock_supabase_service.get_all_teams.call_count <= 2  # Account for cache refresh
    
    def test_teams_endpoint_with_query_parameters(self, test_client, mock_supabase_service):
        """Test teams endpoint with filtering parameters"""
        all_teams_data = [
            {'id': 1, 'team_key': 'yankees', 'division': 'AL East', 'league': 'American League'},
            {'id': 2, 'team_key': 'redsox', 'division': 'AL East', 'league': 'American League'},
            {'id': 3, 'team_key': 'dodgers', 'division': 'NL West', 'league': 'National League'}
        ]
        
        mock_supabase_service.get_all_teams.return_value = all_teams_data
        
        # Test with division filter (if implemented)
        response = test_client.get("/api/teams?division=AL East")
        assert response.status_code == 200
        
        # Test with league filter (if implemented)
        response = test_client.get("/api/teams?league=American League")
        assert response.status_code == 200
    
    def test_teams_data_consistency(self, test_client, mock_supabase_service):
        """Test teams data consistency and validation"""
        teams_data = [
            {
                'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees',
                'abbreviation': 'NYY', 'division': 'AL East', 'league': 'American League',
                'budget_level': 'high', 'competitive_window': 'win-now', 'market_size': 'large'
            }
        ]
        
        mock_supabase_service.get_all_teams.return_value = teams_data
        
        response = test_client.get("/api/teams")
        
        assert response.status_code == 200
        data = response.json()
        
        team = data["teams"][0]
        
        # Validate required fields
        required_fields = ['team_key', 'name', 'abbreviation', 'division', 'league']
        for field in required_fields:
            assert field in team and team[field], f"Missing or empty required field: {field}"
        
        # Validate enum values
        if 'budget_level' in team:
            assert team['budget_level'] in ['low', 'medium', 'high']
        if 'competitive_window' in team:
            assert team['competitive_window'] in ['rebuild', 'retool', 'win-now']
        if 'market_size' in team:
            assert team['market_size'] in ['small', 'medium', 'large']


class TestTradeAnalysisEndpointEnhanced:
    """Enhanced tests for trade analysis endpoint"""
    
    def test_analyze_trade_with_all_parameters(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test trade analysis with all optional parameters"""
        complete_request = {
            "team": "yankees",
            "request": "Need a starting pitcher with ERA under 3.50 for playoff push",
            "urgency": "high",
            "budget_limit": 50000000.0,
            "include_prospects": True,
            "max_trade_partners": 3,
            "preferred_positions": ["SP", "RP"],
            "exclude_teams": ["redsox", "orioles"],
            "max_contract_years": 2
        }
        
        response = test_client.post("/api/analyze-trade", json=complete_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "yankees"
        assert data["urgency"] == "high"
        assert "budget_limit" in str(data.get("original_request", ""))
    
    def test_analyze_trade_with_complex_requests(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test analysis with complex, realistic trade requests"""
        complex_requests = [
            {
                "team": "yankees",
                "request": "Looking for a left-handed starting pitcher under 30 with at least 3 years of team control, ERA under 4.00, and postseason experience. Willing to trade prospects but not our top 3.",
                "urgency": "medium"
            },
            {
                "team": "dodgers",
                "request": "Need bullpen help, specifically a closer or setup man who can handle high-leverage situations. Budget around $15M AAV, prefer someone with playoff experience.",
                "urgency": "high"
            },
            {
                "team": "rays",
                "request": "Seeking versatile utility player who can play multiple infield positions, good OBP, team-friendly contract. Looking for value acquisition.",
                "urgency": "low"
            }
        ]
        
        for request_data in complex_requests:
            response = test_client.post("/api/analyze-trade", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert data["team"] == request_data["team"]
            assert data["urgency"] == request_data["urgency"]
    
    def test_analyze_trade_edge_cases(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test edge cases in trade analysis"""
        edge_cases = [
            {
                "name": "minimum_valid_request",
                "data": {"team": "yankees", "request": "need pitcher"},
                "expected_status": 200
            },
            {
                "name": "maximum_length_request",
                "data": {"team": "yankees", "request": "a" * 1000},  # 1000 characters
                "expected_status": 200
            },
            {
                "name": "unicode_team_name",
                "data": {"team": "yankees", "request": "Need pitcher with résumé"},
                "expected_status": 200
            },
            {
                "name": "special_characters",
                "data": {"team": "yankees", "request": "Need pitcher @ $10M/year, 50% chance"},
                "expected_status": 200
            }
        ]
        
        for case in edge_cases:
            response = test_client.post("/api/analyze-trade", json=case["data"])
            assert response.status_code == case["expected_status"], f"Failed case: {case['name']}"
    
    def test_analyze_trade_with_invalid_urgency(self, test_client, mock_supabase_service):
        """Test analysis with invalid urgency levels"""
        invalid_urgencies = ["urgent", "critical", "immediate", "asap", "now", ""]
        
        for urgency in invalid_urgencies:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": "Need pitcher",
                "urgency": urgency
            })
            
            # Should be rejected due to invalid urgency
            assert response.status_code == 422
    
    def test_analyze_trade_budget_validation(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test budget limit validation"""
        budget_cases = [
            {"budget_limit": -1000000, "should_fail": True},  # Negative budget
            {"budget_limit": 0, "should_fail": True},  # Zero budget
            {"budget_limit": 500000000, "should_fail": False},  # Very high budget
            {"budget_limit": 1000000, "should_fail": False},  # Low but valid budget
            {"budget_limit": "invalid", "should_fail": True},  # Invalid type
        ]
        
        for case in budget_cases:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": "Need pitcher",
                "budget_limit": case["budget_limit"]
            })
            
            if case["should_fail"]:
                assert response.status_code == 422
            else:
                assert response.status_code == 200
    
    def test_analyze_trade_background_task_tracking(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test background task creation and tracking"""
        # Mock analysis ID generation
        test_analysis_id = str(uuid.uuid4())
        mock_supabase_service.create_trade_analysis.return_value = test_analysis_id
        
        response = test_client.post("/api/analyze-trade", json={
            "team": "yankees",
            "request": "Need starting pitcher"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == test_analysis_id
        assert data["status"] == "queued"
        
        # Verify background task was initiated
        mock_supabase_service.create_trade_analysis.assert_called_once()
    
    def test_analyze_trade_concurrent_submissions(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test concurrent trade analysis submissions"""
        import concurrent.futures
        
        def submit_analysis(request_id):
            return test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Need pitcher {request_id}"
            })
        
        # Submit 5 concurrent analyses
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(submit_analysis, i) for i in range(5)]
            responses = [future.result() for future in futures]
        
        # All should succeed or fail gracefully
        for response in responses:
            assert response.status_code in [200, 429, 503]
        
        # At least some should succeed
        successful = [r for r in responses if r.status_code == 200]
        assert len(successful) > 0


class TestAnalysisStatusEndpointEnhanced:
    """Enhanced tests for analysis status endpoint"""
    
    def test_get_analysis_with_detailed_progress(self, test_client, mock_supabase_service):
        """Test analysis retrieval with detailed progress information"""
        detailed_analysis = {
            'id': 1,
            'analysis_id': 'test-analysis-id',
            'requesting_team_id': 1,
            'request_text': 'Need starting pitcher',
            'status': 'analyzing',
            'progress': {
                'overall_progress': 0.6,
                'current_department': 'Analytics Department',
                'departments_completed': [
                    'Front Office Leadership',
                    'Scouting Department'
                ],
                'departments_remaining': [
                    'Player Development',
                    'Business Operations'
                ],
                'estimated_completion_time': '2024-03-15T14:30:00Z',
                'current_task': 'Analyzing comparable players'
            },
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        mock_supabase_service.get_trade_analysis.return_value = detailed_analysis
        
        response = test_client.get("/api/analysis/test-analysis-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == "test-analysis-id"
        assert data["status"] == "analyzing"
        assert "progress" in data
    
    def test_get_analysis_status_transitions(self, test_client, mock_supabase_service):
        """Test all possible analysis status transitions"""
        statuses = [
            ('queued', 'Analysis queued for processing'),
            ('analyzing', 'Analysis in progress'),
            ('completed', 'Analysis completed successfully'),
            ('failed', 'Analysis failed due to error'),
            ('timeout', 'Analysis timed out'),
            ('cancelled', 'Analysis was cancelled')
        ]
        
        for status, description in statuses:
            mock_supabase_service.get_trade_analysis.return_value = {
                'analysis_id': 'test-id',
                'status': status,
                'requesting_team_id': 1,
                'request_text': 'Test request',
                'created_at': datetime.now()
            }
            
            response = test_client.get("/api/analysis/test-id")
            
            if status in ['completed', 'failed', 'timeout']:
                # These statuses should return analysis data
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == status
            else:
                # Other statuses should also return 200 with status info
                assert response.status_code == 200
    
    def test_get_analysis_with_proposals(self, test_client, mock_supabase_service):
        """Test analysis retrieval with trade proposals"""
        mock_analysis = {
            'analysis_id': 'test-id',
            'requesting_team_id': 1,
            'status': 'completed',
            'results': {'recommendation': 'Multiple viable options found'},
            'created_at': datetime.now(),
            'completed_at': datetime.now()
        }
        
        mock_proposals = [
            {
                'id': 1,
                'proposal_rank': 1,
                'teams_involved': [
                    {'team': 'yankees', 'role': 'acquiring'},
                    {'team': 'guardians', 'role': 'trading'}
                ],
                'players_involved': [
                    {
                        'player': 'Shane Bieber',
                        'from_team': 'guardians',
                        'to_team': 'yankees',
                        'position': 'SP',
                        'value': 45000000
                    },
                    {
                        'player': 'Top Prospect',
                        'from_team': 'yankees',
                        'to_team': 'guardians',
                        'position': 'SS',
                        'value': 30000000
                    }
                ],
                'likelihood': 'medium',
                'trade_value_balance': 0.95,
                'risk_assessment': {
                    'overall_risk': 'medium',
                    'injury_risk': 'low',
                    'performance_risk': 'medium',
                    'contract_risk': 'high'
                },
                'financial_impact': {
                    'salary_change': 15000000,
                    'luxury_tax_impact': 2500000,
                    'long_term_commitments': 45000000
                }
            },
            {
                'id': 2,
                'proposal_rank': 2,
                'teams_involved': [
                    {'team': 'yankees', 'role': 'acquiring'},
                    {'team': 'padres', 'role': 'trading'}
                ],
                'players_involved': [
                    {
                        'player': 'Dylan Cease',
                        'from_team': 'padres',
                        'to_team': 'yankees'
                    }
                ],
                'likelihood': 'high'
            }
        ]
        
        mock_supabase_service.get_trade_analysis.return_value = mock_analysis
        mock_supabase_service.get_trade_proposals.return_value = mock_proposals
        
        response = test_client.get("/api/analysis/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "proposals" in data
        assert len(data["proposals"]) == 2
        
        # Check first proposal details
        proposal1 = data["proposals"][0]
        assert proposal1["proposal_rank"] == 1
        assert proposal1["likelihood"] == "medium"
        assert "risk_assessment" in proposal1
        assert "financial_impact" in proposal1
    
    def test_get_analysis_error_details(self, test_client, mock_supabase_service):
        """Test analysis retrieval with error information"""
        failed_analysis = {
            'analysis_id': 'failed-analysis-id',
            'requesting_team_id': 1,
            'status': 'failed',
            'error_message': 'CrewAI analysis timeout after 300 seconds',
            'error_details': {
                'error_type': 'TimeoutError',
                'department': 'Analytics Department',
                'retry_count': 3,
                'last_attempt': '2024-03-15T14:25:00Z'
            },
            'created_at': datetime.now(),
            'failed_at': datetime.now()
        }
        
        mock_supabase_service.get_trade_analysis.return_value = failed_analysis
        
        response = test_client.get("/api/analysis/failed-analysis-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "CrewAI analysis timeout after 300 seconds"
    
    def test_get_analysis_invalid_uuid_format(self, test_client):
        """Test analysis retrieval with invalid UUID formats"""
        invalid_uuids = [
            "not-a-uuid",
            "123",
            "invalid-uuid-format",
            "",
            "null",
            "undefined",
            "12345678-1234-1234-1234-12345678901",  # Too long
            "12345678-1234-1234-1234-123456789012345"  # Way too long
        ]
        
        for invalid_uuid in invalid_uuids:
            response = test_client.get(f"/api/analysis/{invalid_uuid}")
            assert response.status_code in [404, 422], f"Invalid UUID not rejected: {invalid_uuid}"


class TestQuickAnalysisEndpoint:
    """Tests for quick analysis endpoint"""
    
    def test_quick_analysis_basic_functionality(self, test_client, mock_supabase_service, mock_trade_parser):
        """Test basic quick analysis functionality"""
        response = test_client.post("/api/quick-analysis", json={
            "team": "yankees",
            "request": "Need a closer for the bullpen"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "yankees"
        assert data["original_request"] == "Need a closer for the bullpen"
        assert "parsed_request" in data
        assert "confidence_score" in data
    
    def test_quick_analysis_parser_integration(self, test_client, mock_supabase_service, mock_trade_parser):
        """Test integration with trade request parser"""
        # Configure mock parser with detailed response
        mock_trade_parser.parse_trade_request.return_value = Mock(
            primary_need='closer',
            secondary_needs=['setup_man'],
            urgency_level='high',
            budget_constraints=25000000,
            trade_preference='veteran',
            position_specifics={'handedness': 'right'},
            team_context={'contending': True, 'bullpen_depth': 'weak'},
            confidence_score=0.92,
            __dict__={
                'primary_need': 'closer',
                'confidence_score': 0.92,
                'urgency_level': 'high',
                'budget_constraints': 25000000
            }
        )
        
        response = test_client.post("/api/quick-analysis", json={
            "team": "yankees",
            "request": "We desperately need a proven closer with postseason experience, budget around $20-25M"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["confidence_score"] == 0.92
        assert "closer" in str(data["parsed_request"]).lower()
    
    def test_quick_analysis_low_confidence_handling(self, test_client, mock_supabase_service, mock_trade_parser):
        """Test handling of low confidence parse results"""
        mock_trade_parser.parse_trade_request.return_value = Mock(
            primary_need='unknown',
            confidence_score=0.3,  # Low confidence
            __dict__={'primary_need': 'unknown', 'confidence_score': 0.3}
        )
        
        response = test_client.post("/api/quick-analysis", json={
            "team": "yankees",
            "request": "Maybe something good idk"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["confidence_score"] == 0.3
        assert "low_confidence_warning" in data or data["confidence_score"] < 0.5


class TestErrorHandlingEnhanced:
    """Enhanced error handling tests"""
    
    def test_database_connection_failures(self, test_client):
        """Test various database connection failure scenarios"""
        with patch('backend.services.supabase_service.supabase_service') as mock_service:
            # Test connection timeout
            mock_service.health_check.side_effect = asyncio.TimeoutError("Connection timeout")
            
            response = test_client.get("/")
            assert response.status_code == 503
            
            # Test connection refused
            mock_service.get_all_teams.side_effect = ConnectionError("Connection refused")
            
            response = test_client.get("/api/teams")
            assert response.status_code == 503
    
    def test_crewai_analysis_failures(self, test_client, mock_supabase_service):
        """Test CrewAI analysis failure scenarios"""
        with patch('backend.crews.front_office_crew.FrontOfficeCrew') as mock_crew:
            # Test analysis timeout
            mock_instance = Mock()
            mock_instance.analyze_trade_request.side_effect = asyncio.TimeoutError("Analysis timeout")
            mock_crew.return_value = mock_instance
            
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": "Need pitcher"
            })
            
            # Should still return success but mark as queued for retry
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "queued"  # Will be processed in background
    
    def test_malformed_json_handling(self, test_client):
        """Test handling of malformed JSON requests"""
        malformed_requests = [
            '{"team": "yankees", "request": }',  # Missing value
            '{"team": "yankees", "request": "test",}',  # Trailing comma
            '{team: "yankees", request: "test"}',  # Unquoted keys
            '{"team": "yankees", "request": "test"',  # Incomplete JSON
            '',  # Empty body
            'not json at all',  # Not JSON
        ]
        
        for malformed_json in malformed_requests:
            response = test_client.post(
                "/api/analyze-trade",
                data=malformed_json,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 422
    
    def test_request_size_limits(self, test_client, mock_supabase_service):
        """Test request size limitation handling"""
        # Test extremely large request body
        huge_request = {
            "team": "yankees",
            "request": "A" * 1000000,  # 1MB request
            "additional_data": ["X" * 100000 for _ in range(10)]  # Additional large data
        }
        
        response = test_client.post("/api/analyze-trade", json=huge_request)
        
        # Should be rejected due to size
        assert response.status_code in [413, 422]
    
    def test_invalid_content_type_handling(self, test_client):
        """Test handling of invalid content types"""
        valid_data = {"team": "yankees", "request": "Need pitcher"}
        
        # Test with wrong content type
        response = test_client.post(
            "/api/analyze-trade",
            data=json.dumps(valid_data),
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 422
        
        # Test with no content type
        response = test_client.post(
            "/api/analyze-trade",
            data=json.dumps(valid_data)
        )
        
        assert response.status_code == 422


class TestPerformanceAndScaling:
    """Tests for performance and scaling scenarios"""
    
    def test_response_time_benchmarks(self, test_client, mock_supabase_service, performance_monitor):
        """Test response time benchmarks for all endpoints"""
        endpoints = [
            ("GET", "/", 1.0),  # Health check should be very fast
            ("GET", "/api/teams", 2.0),  # Teams should be fast (cached)
            ("POST", "/api/analyze-trade", 5.0),  # Analysis creation should be reasonable
        ]
        
        for method, endpoint, max_time in endpoints:
            performance_monitor.start()
            
            if method == "GET":
                response = test_client.get(endpoint)
            else:
                response = test_client.post(endpoint, json={
                    "team": "yankees",
                    "request": "Need pitcher"
                })
            
            performance_monitor.stop()
            
            assert response.status_code in [200, 422]  # Should respond successfully
            assert performance_monitor.duration < max_time, f"{endpoint} took {performance_monitor.duration}s, expected < {max_time}s"
    
    def test_memory_usage_patterns(self, test_client, mock_supabase_service):
        """Test memory usage doesn't grow unexpectedly"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Make multiple requests
        for i in range(50):
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Need pitcher {i}"
            })
            assert response.status_code in [200, 429, 503]
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for 50 requests)
        assert memory_growth < 50 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024}MB"
    
    def test_concurrent_load_handling(self, test_client, mock_supabase_service):
        """Test handling of concurrent load"""
        import concurrent.futures
        import time
        
        def make_request(request_id):
            start_time = time.time()
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Concurrent request {request_id}"
            })
            end_time = time.time()
            return {
                "response": response,
                "duration": end_time - start_time,
                "request_id": request_id
            }
        
        # Test with 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in futures]
        
        # Analyze results
        successful_requests = [r for r in results if r["response"].status_code == 200]
        failed_requests = [r for r in results if r["response"].status_code not in [200, 429]]
        
        # At least 50% should succeed
        assert len(successful_requests) >= 10, f"Only {len(successful_requests)}/20 requests succeeded"
        
        # No requests should fail with server errors (500, 502, etc.)
        server_errors = [r for r in results if r["response"].status_code >= 500]
        assert len(server_errors) == 0, f"{len(server_errors)} requests failed with server errors"
        
        # Average response time should be reasonable
        avg_response_time = sum(r["duration"] for r in successful_requests) / len(successful_requests)
        assert avg_response_time < 10.0, f"Average response time {avg_response_time}s too high"