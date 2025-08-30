"""
Test suite for FastAPI endpoints
Tests all API endpoints with various scenarios including success, error, and edge cases
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime
import json

from backend.api.trade_analyzer_v2 import app
from backend.api.models import AnalysisStatus
from backend.api.exceptions import TeamNotFoundError, AnalysisNotFoundError


class TestSystemHealthEndpoint:
    """Test system health and status endpoints"""
    
    def test_health_check_success(self, test_client, mock_supabase_service):
        """Test successful health check"""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Baseball Trade AI - Front Office Simulation"
        assert data["version"] == "2.0.0"
        assert data["status"] == "operational"
        assert isinstance(data["available_teams"], list)
        assert "departments" in data
        assert data["database_status"] == "healthy"
        
    def test_health_check_database_failure(self, test_client, mock_supabase_service):
        """Test health check when database fails"""
        mock_supabase_service.health_check.return_value = {'status': 'unhealthy'}
        
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"


class TestTeamsEndpoint:
    """Test teams listing endpoint"""
    
    def test_get_teams_success(self, test_client, mock_supabase_service):
        """Test successful teams retrieval"""
        response = test_client.get("/api/teams")
        
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert data["total_teams"] == 1
        assert data["source"] == "database"
        assert len(data["teams"]) == 1
        
        team = data["teams"][0]
        assert team["team_key"] == "yankees"
        assert team["name"] == "New York Yankees"
        assert team["division"] == "AL East"
    
    def test_get_teams_database_error(self, test_client, database_error_mock):
        """Test teams endpoint with database error"""
        with database_error_mock("get_all_teams"):
            response = test_client.get("/api/teams")
            
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert "Database operation failed" in data["error"]


class TestTradeAnalysisEndpoint:
    """Test trade analysis request endpoint"""
    
    def test_analyze_trade_success(self, test_client, mock_supabase_service, mock_front_office_crew, sample_trade_request):
        """Test successful trade analysis request"""
        response = test_client.post("/api/analyze-trade", json=sample_trade_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["team"] == "yankees"
        assert data["original_request"] == sample_trade_request["request"]
        assert data["status"] == "queued"
        assert isinstance(data["departments_consulted"], list)
        
    def test_analyze_trade_invalid_team(self, test_client, mock_supabase_service, sample_trade_request):
        """Test trade analysis with invalid team"""
        mock_supabase_service.get_team_by_key.return_value = None
        
        invalid_request = sample_trade_request.copy()
        invalid_request["team"] = "nonexistent_team"
        
        response = test_client.post("/api/analyze-trade", json=invalid_request)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]
        
    def test_analyze_trade_validation_errors(self, test_client, mock_supabase_service):
        """Test trade analysis with invalid request data"""
        invalid_requests = [
            {"team": "", "request": ""},  # Empty fields
            {"team": "yankees", "request": "short"},  # Too short request
            {"team": "yankees", "request": "A" * 1001},  # Too long request
            {"team": "yankees"},  # Missing request field
            {"request": "Valid request"},  # Missing team field
        ]
        
        for invalid_request in invalid_requests:
            response = test_client.post("/api/analyze-trade", json=invalid_request)
            assert response.status_code == 422, f"Failed for request: {invalid_request}"
            
    def test_analyze_trade_database_creation_failure(self, test_client, mock_supabase_service, sample_trade_request):
        """Test trade analysis when database creation fails"""
        mock_supabase_service.create_trade_analysis.return_value = ""  # Empty string indicates failure
        
        response = test_client.post("/api/analyze-trade", json=sample_trade_request)
        
        assert response.status_code == 503
        data = response.json()
        assert "Database operation failed" in data["error"]


class TestAnalysisStatusEndpoint:
    """Test analysis status and retrieval endpoints"""
    
    def test_get_analysis_success(self, test_client, mock_supabase_service):
        """Test successful analysis retrieval"""
        response = test_client.get("/api/analysis/test-analysis-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == "test-analysis-id"
        assert data["team"] == "yankees"
        assert data["status"] == "queued"
        
    def test_get_analysis_not_found(self, test_client, mock_supabase_service):
        """Test analysis retrieval with non-existent ID"""
        mock_supabase_service.get_trade_analysis.return_value = None
        
        response = test_client.get("/api/analysis/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]
        
    def test_get_analysis_detailed_status(self, test_client, mock_supabase_service):
        """Test detailed status endpoint"""
        mock_supabase_service.get_trade_analysis.return_value = {
            'analysis_id': 'test-analysis-id',
            'requesting_team_id': 1,
            'status': 'analyzing',
            'progress': {
                'current_department': 'Scouting Department',
                'departments_completed': ['Front Office Leadership']
            },
            'created_at': datetime.now()
        }
        
        response = test_client.get("/api/analysis/test-analysis-id/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == "test-analysis-id"
        assert data["status"] == "analyzing"
        assert "progress" in data
        
    def test_get_analysis_completed_with_proposals(self, test_client, mock_supabase_service):
        """Test analysis retrieval for completed analysis with proposals"""
        mock_supabase_service.get_trade_analysis.return_value = {
            'analysis_id': 'test-analysis-id',
            'requesting_team_id': 1,
            'status': 'completed',
            'request_text': 'Test request',
            'results': {'recommendation': 'Test recommendation'},
            'created_at': datetime.now(),
            'completed_at': datetime.now()
        }
        
        mock_supabase_service.get_trade_proposals.return_value = [
            {
                'proposal_rank': 1,
                'teams_involved': [{'team': 'Test Team'}],
                'players_involved': [{'player': 'Test Player'}],
                'likelihood': 'Medium'
            }
        ]
        
        response = test_client.get("/api/analysis/test-analysis-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "results" in data
        assert "proposals" in data
        assert len(data["proposals"]) == 1


class TestQuickAnalysisEndpoint:
    """Test quick analysis endpoint"""
    
    def test_quick_analysis_success(self, test_client, mock_supabase_service, mock_trade_parser):
        """Test successful quick analysis"""
        request_data = {"team": "yankees", "request": "Need a closer"}
        
        response = test_client.post("/api/quick-analysis", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "yankees"
        assert data["original_request"] == "Need a closer"
        assert "parsed_request" in data
        assert "confidence_score" in data
        assert "recommended_next_steps" in data
        
    def test_quick_analysis_invalid_team(self, test_client, mock_supabase_service):
        """Test quick analysis with invalid team"""
        mock_supabase_service.get_team_by_key.return_value = None
        
        request_data = {"team": "invalid_team", "request": "Need a player"}
        
        response = test_client.post("/api/quick-analysis", json=request_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]


class TestErrorHandling:
    """Test comprehensive error handling scenarios"""
    
    def test_internal_server_error(self, test_client):
        """Test internal server error handling"""
        with patch('backend.api.trade_analyzer_v2.supabase_service') as mock_service:
            mock_service.health_check.side_effect = Exception("Unexpected error")
            
            response = test_client.get("/")
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "timestamp" in data
            
    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON requests"""
        response = test_client.post(
            "/api/analyze-trade",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        
    def test_missing_content_type(self, test_client):
        """Test handling of requests without proper content type"""
        response = test_client.post(
            "/api/analyze-trade",
            data='{"team": "yankees", "request": "test"}'
        )
        
        assert response.status_code == 422


class TestSecurityValidation:
    """Test security-related validation and sanitization"""
    
    def test_sql_injection_attempts(self, test_client, mock_supabase_service, malicious_input_samples):
        """Test SQL injection protection"""
        for malicious_input in malicious_input_samples[:3]:  # Test first 3 samples
            request_data = {
                "team": malicious_input,
                "request": "Looking for a pitcher"
            }
            
            response = test_client.post("/api/analyze-trade", json=request_data)
            # Should either be rejected (422) or sanitized and processed
            assert response.status_code in [422, 404], f"Failed to handle: {malicious_input}"
            
    def test_xss_attempts(self, test_client, mock_supabase_service, malicious_input_samples):
        """Test XSS protection"""
        malicious_request = {
            "team": "yankees",
            "request": malicious_input_samples[1]  # XSS script
        }
        
        response = test_client.post("/api/analyze-trade", json=malicious_request)
        
        # Should be rejected due to validation
        assert response.status_code == 422
        
    def test_oversized_request(self, test_client, mock_supabase_service):
        """Test handling of oversized requests"""
        oversized_request = {
            "team": "yankees",
            "request": "A" * 10000  # Very large request
        }
        
        response = test_client.post("/api/analyze-trade", json=oversized_request)
        
        assert response.status_code == 422


class TestPerformance:
    """Test performance-related scenarios"""
    
    def test_concurrent_requests(self, test_client, mock_supabase_service, sample_trade_request):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            return test_client.post("/api/analyze-trade", json=sample_trade_request)
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed or fail gracefully
        for response in responses:
            assert response.status_code in [200, 429, 503]  # Success, rate limited, or service unavailable
            
    def test_response_time_limits(self, test_client, performance_monitor):
        """Test that endpoints respond within reasonable time limits"""
        performance_monitor.start()
        response = test_client.get("/api/teams")
        performance_monitor.stop()
        
        assert response.status_code == 200
        assert performance_monitor.duration < 5.0  # Should respond within 5 seconds
        
    @pytest.mark.asyncio
    async def test_background_task_handling(self, test_client, mock_supabase_service, mock_front_office_crew, sample_trade_request):
        """Test that background tasks are properly handled"""
        response = test_client.post("/api/analyze-trade", json=sample_trade_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        
        # Verify background task was initiated (hard to test directly, but we can check the response)
        assert "analysis_id" in data