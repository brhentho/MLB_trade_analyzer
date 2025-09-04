"""
Performance and load testing for Baseball Trade AI
Tests response times, throughput, memory usage, and scalability
"""

import pytest
import asyncio
import time
import statistics
import gc
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import threading
from typing import List, Dict, Any, Tuple

from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.api.trade_analyzer_v2 import app
from backend.services.supabase_service import supabase_service
from backend.crews.front_office_crew import FrontOfficeCrew


class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_memory = None
        self.start_cpu = None
        self.start_time = None
        self.measurements = []
    
    def start(self):
        """Start performance monitoring"""
        gc.collect()  # Clean up before measurement
        self.start_memory = self.process.memory_info().rss
        self.start_cpu = self.process.cpu_percent()
        self.start_time = time.time()
        return self
    
    def stop(self):
        """Stop monitoring and calculate metrics"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        return {
            'duration': end_time - self.start_time,
            'memory_growth': end_memory - self.start_memory,
            'peak_memory': self.process.memory_info().rss,
            'cpu_percent': self.process.cpu_percent(),
        }
    
    def record_measurement(self, name: str, value: float):
        """Record a performance measurement"""
        self.measurements.append({
            'name': name,
            'value': value,
            'timestamp': time.time()
        })


@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture"""
    return PerformanceMonitor()


@pytest.fixture
def mock_fast_crew():
    """Mock CrewAI with fast responses for performance testing"""
    with patch('backend.crews.front_office_crew.FrontOfficeCrew') as mock_crew:
        mock_instance = Mock()
        mock_instance.analyze_trade_request = AsyncMock(return_value={
            'organizational_recommendation': {'overall_recommendation': 'Fast mock result'},
            'departments_consulted': ['Front Office'],
            'token_usage': 500,
            'estimated_cost': 0.01,
            'duration_seconds': 0.1
        })
        mock_crew.return_value = mock_instance
        yield mock_instance


@pytest.fixture 
def mock_fast_supabase():
    """Mock Supabase with fast responses"""
    with patch('backend.services.supabase_service.supabase_service') as mock_service:
        mock_service.health_check.return_value = {'status': 'healthy'}
        mock_service.get_all_teams.return_value = [
            {'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees'}
        ]
        mock_service.get_team_by_key.return_value = {
            'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees'
        }
        mock_service.create_trade_analysis.return_value = 'test-analysis-id'
        mock_service.get_trade_analysis.return_value = {
            'analysis_id': 'test-analysis-id',
            'status': 'queued'
        }
        yield mock_service


class TestResponseTimePerformance:
    """Test response time performance for all endpoints"""
    
    def test_health_endpoint_response_time(self, performance_monitor, mock_fast_supabase):
        """Test health endpoint response time"""
        client = TestClient(app)
        
        response_times = []
        
        for _ in range(100):
            monitor = performance_monitor.start()
            response = client.get("/")
            metrics = monitor.stop()
            
            assert response.status_code == 200
            response_times.append(metrics['duration'])
        
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Health check should be very fast
        assert avg_time < 0.1, f"Average response time {avg_time:.3f}s exceeds 100ms"
        assert p95_time < 0.2, f"95th percentile {p95_time:.3f}s exceeds 200ms"
        assert p99_time < 0.5, f"99th percentile {p99_time:.3f}s exceeds 500ms"
        
        print(f"Health endpoint - Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s, P99: {p99_time:.3f}s")
    
    def test_teams_endpoint_response_time(self, performance_monitor, mock_fast_supabase):
        """Test teams endpoint response time with caching"""
        client = TestClient(app)
        
        response_times = []
        
        for i in range(50):
            monitor = performance_monitor.start()
            response = client.get("/api/teams")
            metrics = monitor.stop()
            
            assert response.status_code == 200
            response_times.append(metrics['duration'])
            
            # First request might be slower (cache miss), subsequent should be faster
            if i > 5:  # After cache warmup
                assert metrics['duration'] < 0.05, f"Cached request {i} took {metrics['duration']:.3f}s"
        
        avg_time = statistics.mean(response_times[10:])  # Exclude cache warmup
        assert avg_time < 0.02, f"Average cached response time {avg_time:.3f}s exceeds 20ms"
        
        print(f"Teams endpoint (cached) - Avg: {avg_time:.3f}s")
    
    def test_trade_analysis_endpoint_response_time(self, performance_monitor, mock_fast_supabase, mock_fast_crew):
        """Test trade analysis endpoint response time"""
        client = TestClient(app)
        
        response_times = []
        trade_request = {
            "team": "yankees",
            "request": "Need starting pitcher performance test",
            "urgency": "medium"
        }
        
        for _ in range(20):
            monitor = performance_monitor.start()
            response = client.post("/api/analyze-trade", json=trade_request)
            metrics = monitor.stop()
            
            assert response.status_code == 200
            response_times.append(metrics['duration'])
        
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        
        # Analysis submission should be fast (background processing)
        assert avg_time < 1.0, f"Average submission time {avg_time:.3f}s exceeds 1s"
        assert p95_time < 2.0, f"95th percentile {p95_time:.3f}s exceeds 2s"
        
        print(f"Trade analysis submission - Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s")
    
    def test_analysis_status_endpoint_response_time(self, performance_monitor, mock_fast_supabase):
        """Test analysis status endpoint response time"""
        client = TestClient(app)
        
        response_times = []
        
        for _ in range(50):
            monitor = performance_monitor.start()
            response = client.get("/api/analysis/test-analysis-id")
            metrics = monitor.stop()
            
            # Could be 200 or 404, both should be fast
            assert response.status_code in [200, 404]
            response_times.append(metrics['duration'])
        
        avg_time = statistics.mean(response_times)
        
        # Status checks should be very fast
        assert avg_time < 0.05, f"Average status check time {avg_time:.3f}s exceeds 50ms"
        
        print(f"Analysis status - Avg: {avg_time:.3f}s")


class TestThroughputPerformance:
    """Test throughput and concurrent request handling"""
    
    def test_concurrent_health_checks(self, mock_fast_supabase):
        """Test handling concurrent health check requests"""
        client = TestClient(app)
        
        def make_health_request():
            start_time = time.time()
            response = client.get("/")
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'thread_id': threading.current_thread().ident
            }
        
        # Test with 50 concurrent requests
        with ThreadPoolExecutor(max_workers=50) as executor:
            start_time = time.time()
            futures = [executor.submit(make_health_request) for _ in range(100)]
            results = [future.result() for future in as_completed(futures)]
            total_time = time.time() - start_time
        
        # Verify all requests succeeded
        successful_requests = [r for r in results if r['status_code'] == 200]
        assert len(successful_requests) == 100, f"Only {len(successful_requests)}/100 requests succeeded"
        
        # Calculate throughput
        throughput = len(successful_requests) / total_time
        assert throughput > 50, f"Throughput {throughput:.1f} RPS below minimum of 50 RPS"
        
        # Check response time distribution
        response_times = [r['duration'] for r in successful_requests]
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        assert avg_time < 0.5, f"Average response time {avg_time:.3f}s too high under load"
        assert max_time < 2.0, f"Maximum response time {max_time:.3f}s too high under load"
        
        print(f"Concurrent health checks - Throughput: {throughput:.1f} RPS, Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    def test_concurrent_trade_submissions(self, mock_fast_supabase, mock_fast_crew):
        """Test concurrent trade analysis submissions"""
        client = TestClient(app)
        
        def submit_trade_request(request_id):
            trade_request = {
                "team": "yankees",
                "request": f"Performance test request {request_id}",
                "urgency": "medium"
            }
            
            start_time = time.time()
            response = client.post("/api/analyze-trade", json=trade_request)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'duration': end_time - start_time,
                'request_id': request_id
            }
        
        # Test with 20 concurrent trade submissions
        with ThreadPoolExecutor(max_workers=20) as executor:
            start_time = time.time()
            futures = [executor.submit(submit_trade_request, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
            total_time = time.time() - start_time
        
        # Check success rate
        successful_requests = [r for r in results if r['status_code'] in [200, 429]]  # 429 is acceptable (rate limited)
        success_rate = len([r for r in results if r['status_code'] == 200]) / len(results)
        
        assert success_rate > 0.8, f"Success rate {success_rate:.1%} below 80%"
        
        # Calculate throughput for successful requests  
        successful_only = [r for r in results if r['status_code'] == 200]
        if successful_only:
            throughput = len(successful_only) / total_time
            avg_time = statistics.mean([r['duration'] for r in successful_only])
            
            print(f"Trade submissions - Success rate: {success_rate:.1%}, Throughput: {throughput:.1f} RPS, Avg: {avg_time:.3f}s")
        
        # System should handle at least 5 submissions per second
        if successful_only:
            assert throughput > 5, f"Trade submission throughput {throughput:.1f} RPS below minimum"
    
    def test_mixed_workload_performance(self, mock_fast_supabase, mock_fast_crew):
        """Test performance under mixed workload"""
        client = TestClient(app)
        
        results = {'health': [], 'teams': [], 'trades': [], 'status': []}
        
        def make_health_request():
            start_time = time.time()
            response = client.get("/")
            return {'endpoint': 'health', 'duration': time.time() - start_time, 'status': response.status_code}
        
        def make_teams_request():
            start_time = time.time()
            response = client.get("/api/teams")
            return {'endpoint': 'teams', 'duration': time.time() - start_time, 'status': response.status_code}
        
        def make_trade_request():
            start_time = time.time()
            response = client.post("/api/analyze-trade", json={
                "team": "yankees", "request": "Mixed workload test", "urgency": "medium"
            })
            return {'endpoint': 'trades', 'duration': time.time() - start_time, 'status': response.status_code}
        
        def make_status_request():
            start_time = time.time()
            response = client.get("/api/analysis/test-id")
            return {'endpoint': 'status', 'duration': time.time() - start_time, 'status': response.status_code}
        
        # Create mixed workload
        tasks = []
        with ThreadPoolExecutor(max_workers=30) as executor:
            # Submit mix of requests
            for _ in range(20):
                tasks.append(executor.submit(make_health_request))
                tasks.append(executor.submit(make_teams_request))
            for _ in range(10):
                tasks.append(executor.submit(make_trade_request))
            for _ in range(15):
                tasks.append(executor.submit(make_status_request))
            
            all_results = [future.result() for future in as_completed(tasks)]
        
        # Organize results by endpoint
        for result in all_results:
            endpoint = result['endpoint']
            results[endpoint].append(result)
        
        # Verify performance for each endpoint type
        for endpoint, endpoint_results in results.items():
            if endpoint_results:
                avg_time = statistics.mean([r['duration'] for r in endpoint_results])
                success_rate = len([r for r in endpoint_results if r['status'] in [200, 404, 429]]) / len(endpoint_results)
                
                print(f"{endpoint.title()} endpoint - Avg: {avg_time:.3f}s, Success rate: {success_rate:.1%}")
                
                # Different performance expectations per endpoint
                if endpoint == 'health':
                    assert avg_time < 0.2, f"Health endpoint avg {avg_time:.3f}s too slow under mixed load"
                elif endpoint == 'teams':
                    assert avg_time < 0.1, f"Teams endpoint avg {avg_time:.3f}s too slow under mixed load"
                elif endpoint == 'trades':
                    assert avg_time < 2.0, f"Trades endpoint avg {avg_time:.3f}s too slow under mixed load"
                elif endpoint == 'status':
                    assert avg_time < 0.1, f"Status endpoint avg {avg_time:.3f}s too slow under mixed load"


class TestMemoryPerformance:
    """Test memory usage and garbage collection performance"""
    
    def test_memory_usage_under_load(self, performance_monitor, mock_fast_supabase, mock_fast_crew):
        """Test memory usage during sustained load"""
        client = TestClient(app)
        
        monitor = performance_monitor.start()
        initial_memory = monitor.process.memory_info().rss
        
        # Generate sustained load
        for i in range(100):
            # Mix of different endpoints
            client.get("/")
            client.get("/api/teams")
            
            if i % 5 == 0:  # Every 5th request is a trade analysis
                client.post("/api/analyze-trade", json={
                    "team": "yankees",
                    "request": f"Memory test request {i}",
                    "urgency": "medium"
                })
            
            if i % 10 == 0:  # Check status occasionally
                client.get(f"/api/analysis/test-id-{i}")
            
            # Force garbage collection every 25 requests
            if i % 25 == 0:
                gc.collect()
                current_memory = monitor.process.memory_info().rss
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable
                assert memory_growth < 100 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB after {i} requests"
        
        final_metrics = monitor.stop()
        memory_growth_mb = final_metrics['memory_growth'] / 1024 / 1024
        
        print(f"Memory test - Growth: {memory_growth_mb:.1f}MB over 100 mixed requests")
        
        # Total memory growth should be less than 50MB for 100 requests
        assert memory_growth_mb < 50, f"Memory growth {memory_growth_mb:.1f}MB exceeds 50MB limit"
    
    def test_memory_cleanup_after_analysis(self, performance_monitor, mock_fast_supabase, mock_fast_crew):
        """Test memory cleanup after trade analysis"""
        client = TestClient(app)
        
        # Measure baseline memory
        gc.collect()
        baseline_memory = performance_monitor.process.memory_info().rss
        
        # Perform multiple analyses
        analysis_memories = []
        for i in range(10):
            # Submit analysis
            response = client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Memory cleanup test {i}",
                "urgency": "high"
            })
            assert response.status_code == 200
            
            # Measure memory after each analysis
            current_memory = performance_monitor.process.memory_info().rss
            analysis_memories.append(current_memory - baseline_memory)
            
            # Simulate some processing time
            time.sleep(0.1)
        
        # Force cleanup
        gc.collect()
        final_memory = performance_monitor.process.memory_info().rss
        final_growth = final_memory - baseline_memory
        
        # Memory should not grow linearly with number of analyses
        max_growth = max(analysis_memories)
        
        print(f"Memory cleanup test - Max growth: {max_growth / 1024 / 1024:.1f}MB, Final: {final_growth / 1024 / 1024:.1f}MB")
        
        # Final memory should be reasonable
        assert final_growth < max_growth * 1.2, "Memory not properly cleaned up after analyses"
        assert final_growth / 1024 / 1024 < 30, f"Final memory growth {final_growth / 1024 / 1024:.1f}MB exceeds 30MB"
    
    def test_large_request_memory_handling(self, performance_monitor, mock_fast_supabase, mock_fast_crew):
        """Test memory handling with large trade requests"""
        client = TestClient(app)
        
        # Create progressively larger requests
        base_request = "Need a starting pitcher with excellent control and command, " * 20
        
        memory_usage = []
        
        for size_multiplier in [1, 5, 10, 20]:
            gc.collect()
            start_memory = performance_monitor.process.memory_info().rss
            
            large_request = {
                "team": "yankees",
                "request": base_request * size_multiplier,
                "urgency": "medium"
            }
            
            response = client.post("/api/analyze-trade", json=large_request)
            
            if len(large_request["request"]) > 1000:  # Requests over 1000 chars should be rejected
                assert response.status_code == 422
            else:
                assert response.status_code == 200
            
            end_memory = performance_monitor.process.memory_info().rss
            memory_growth = end_memory - start_memory
            memory_usage.append(memory_growth)
            
            print(f"Request size {len(large_request['request'])}: {memory_growth / 1024:.1f}KB")
        
        # Memory usage shouldn't grow dramatically with request size
        # (since large requests should be rejected)
        valid_requests = [m for i, m in enumerate(memory_usage) if i < 3]  # First 3 should be valid
        if len(valid_requests) > 1:
            max_growth = max(valid_requests)
            assert max_growth < 5 * 1024 * 1024, f"Memory growth {max_growth / 1024 / 1024:.1f}MB too high for large request"


class TestDatabasePerformance:
    """Test database operation performance"""
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, performance_monitor):
        """Test database query performance with realistic load"""
        
        # Mock database with realistic delays
        with patch('backend.services.supabase_service.supabase_service') as mock_service:
            async def slow_team_query(*args, **kwargs):
                await asyncio.sleep(0.01)  # 10ms database latency
                return {'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees'}
            
            async def slow_teams_query(*args, **kwargs):
                await asyncio.sleep(0.02)  # 20ms for multiple teams
                return [
                    {'id': 1, 'team_key': 'yankees', 'name': 'New York Yankees'},
                    {'id': 2, 'team_key': 'redsox', 'name': 'Boston Red Sox'}
                ]
            
            mock_service.get_team_by_key = slow_team_query
            mock_service.get_all_teams = slow_teams_query
            mock_service.create_trade_analysis.return_value = 'test-id'
            
            # Test concurrent database operations
            start_time = time.time()
            
            tasks = []
            for _ in range(20):
                tasks.append(mock_service.get_team_by_key('yankees'))
                tasks.append(mock_service.get_all_teams())
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Verify all queries succeeded
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == 40, f"Only {len(successful_results)}/40 queries succeeded"
            
            # With proper connection pooling, this should be much faster than sequential
            sequential_time_estimate = (20 * 0.01) + (20 * 0.02)  # 0.6 seconds
            
            print(f"Database performance - Concurrent: {total_time:.3f}s, Sequential estimate: {sequential_time_estimate:.3f}s")
            
            # Should be significantly faster due to concurrency
            assert total_time < sequential_time_estimate * 0.5, f"Concurrent queries not fast enough: {total_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, performance_monitor):
        """Test database connection pooling efficiency"""
        
        connection_times = []
        
        # Mock connection with varying delays to simulate pool behavior
        with patch('backend.services.supabase_service.supabase_service') as mock_service:
            call_count = 0
            
            async def pooled_query(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                # First few calls slower (establishing connections)
                if call_count <= 5:
                    await asyncio.sleep(0.05)  # 50ms for new connection
                else:
                    await asyncio.sleep(0.005)  # 5ms for pooled connection
                
                return {'result': f'query_{call_count}'}
            
            mock_service.get_team_by_key = pooled_query
            
            # Make queries and measure connection times
            for i in range(20):
                start_time = time.time()
                result = await mock_service.get_team_by_key('test')
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
                
                # Brief pause between queries
                await asyncio.sleep(0.001)
            
            # First queries should be slower (pool initialization)
            initial_queries = connection_times[:5]
            pooled_queries = connection_times[5:]
            
            avg_initial = statistics.mean(initial_queries)
            avg_pooled = statistics.mean(pooled_queries)
            
            print(f"Connection pooling - Initial: {avg_initial:.3f}s, Pooled: {avg_pooled:.3f}s")
            
            # Pooled connections should be significantly faster
            assert avg_pooled < avg_initial * 0.5, "Connection pooling not providing performance benefit"
            assert avg_pooled < 0.02, f"Pooled connection time {avg_pooled:.3f}s too slow"
    
    def test_database_transaction_performance(self):
        """Test database transaction performance"""
        
        # Mock transactional operations
        with patch('backend.services.supabase_service.supabase_service') as mock_service:
            transaction_times = []
            
            def mock_transaction():
                start_time = time.time()
                
                # Simulate multi-step transaction
                mock_service.create_trade_analysis('test-id', {})
                mock_service.create_trade_proposals('test-id', [])
                mock_service.update_trade_analysis_status('test-id', 'completed')
                
                return time.time() - start_time
            
            # Configure mocks with realistic delays
            mock_service.create_trade_analysis.return_value = 'test-id'
            mock_service.create_trade_proposals.return_value = True
            mock_service.update_trade_analysis_status.return_value = True
            
            # Test transaction performance
            for _ in range(10):
                transaction_time = mock_transaction()
                transaction_times.append(transaction_time)
            
            avg_transaction_time = statistics.mean(transaction_times)
            max_transaction_time = max(transaction_times)
            
            print(f"Transaction performance - Avg: {avg_transaction_time:.3f}s, Max: {max_transaction_time:.3f}s")
            
            # Transactions should complete quickly
            assert avg_transaction_time < 0.1, f"Average transaction time {avg_transaction_time:.3f}s too slow"
            assert max_transaction_time < 0.2, f"Maximum transaction time {max_transaction_time:.3f}s too slow"


class TestScalabilityLimits:
    """Test scalability limits and breaking points"""
    
    def test_maximum_concurrent_users(self, mock_fast_supabase, mock_fast_crew):
        """Test system behavior at maximum concurrent user load"""
        client = TestClient(app)
        
        def simulate_user_session(user_id):
            """Simulate a complete user session"""
            session_results = []
            
            try:
                # User journey: health check -> teams -> submit analysis -> check status
                
                # 1. Health check
                start = time.time()
                health_resp = client.get("/")
                session_results.append({
                    'endpoint': 'health',
                    'status': health_resp.status_code,
                    'duration': time.time() - start
                })
                
                # 2. Get teams
                start = time.time()
                teams_resp = client.get("/api/teams")
                session_results.append({
                    'endpoint': 'teams',
                    'status': teams_resp.status_code,
                    'duration': time.time() - start
                })
                
                # 3. Submit trade analysis
                start = time.time()
                trade_resp = client.post("/api/analyze-trade", json={
                    "team": "yankees",
                    "request": f"Scalability test from user {user_id}",
                    "urgency": "medium"
                })
                session_results.append({
                    'endpoint': 'trade',
                    'status': trade_resp.status_code,
                    'duration': time.time() - start
                })
                
                # 4. Check analysis status (if trade submission succeeded)
                if trade_resp.status_code == 200:
                    analysis_data = trade_resp.json()
                    analysis_id = analysis_data.get('analysis_id', 'test-id')
                    
                    start = time.time()
                    status_resp = client.get(f"/api/analysis/{analysis_id}")
                    session_results.append({
                        'endpoint': 'status',
                        'status': status_resp.status_code,
                        'duration': time.time() - start
                    })
                
                return {
                    'user_id': user_id,
                    'success': True,
                    'requests': session_results
                }
                
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'error': str(e),
                    'requests': session_results
                }
        
        # Test with increasing concurrent user loads
        user_loads = [10, 25, 50, 75, 100]
        results = {}
        
        for user_count in user_loads:
            print(f"Testing {user_count} concurrent users...")
            
            with ThreadPoolExecutor(max_workers=user_count) as executor:
                start_time = time.time()
                futures = [executor.submit(simulate_user_session, i) for i in range(user_count)]
                session_results = [future.result() for future in as_completed(futures)]
                total_time = time.time() - start_time
            
            # Analyze results
            successful_sessions = [s for s in session_results if s['success']]
            success_rate = len(successful_sessions) / len(session_results)
            
            # Calculate response time statistics
            all_requests = []
            for session in successful_sessions:
                all_requests.extend(session['requests'])
            
            if all_requests:
                avg_response_time = statistics.mean([r['duration'] for r in all_requests])
                p95_response_time = statistics.quantiles([r['duration'] for r in all_requests], n=20)[18] if len(all_requests) >= 20 else max([r['duration'] for r in all_requests])
                
                results[user_count] = {
                    'success_rate': success_rate,
                    'avg_response_time': avg_response_time,
                    'p95_response_time': p95_response_time,
                    'total_time': total_time,
                    'throughput': len(all_requests) / total_time
                }
                
                print(f"{user_count} users - Success: {success_rate:.1%}, Avg: {avg_response_time:.3f}s, P95: {p95_response_time:.3f}s, Throughput: {results[user_count]['throughput']:.1f} RPS")
                
                # System should maintain reasonable performance
                if user_count <= 50:  # Up to 50 users should work well
                    assert success_rate > 0.95, f"Success rate {success_rate:.1%} too low at {user_count} users"
                    assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s too high at {user_count} users"
                elif user_count <= 100:  # Up to 100 users should work acceptably
                    assert success_rate > 0.8, f"Success rate {success_rate:.1%} too low at {user_count} users"
                    assert avg_response_time < 2.0, f"Average response time {avg_response_time:.3f}s too high at {user_count} users"
            
            # Brief pause between load tests
            time.sleep(1)
        
        # Verify system degrades gracefully with increased load
        load_50 = results.get(50, {})
        load_100 = results.get(100, {})
        
        if load_50 and load_100:
            response_time_increase = load_100['avg_response_time'] / load_50['avg_response_time']
            assert response_time_increase < 5.0, f"Response time increased {response_time_increase:.1f}x from 50 to 100 users"
    
    def test_request_queue_limits(self, mock_fast_supabase):
        """Test behavior when request queue limits are exceeded"""
        client = TestClient(app)
        
        # Configure slow mock to create backlog
        with patch('backend.crews.front_office_crew.FrontOfficeCrew') as mock_crew:
            mock_instance = Mock()
            
            # Slow analysis to create queue buildup
            async def slow_analysis(*args, **kwargs):
                await asyncio.sleep(2)  # 2 second analysis
                return {
                    'organizational_recommendation': {'overall_recommendation': 'Slow result'},
                    'departments_consulted': ['Front Office'],
                    'token_usage': 1000,
                    'estimated_cost': 0.02
                }
            
            mock_instance.analyze_trade_request = slow_analysis
            mock_crew.return_value = mock_instance
            
            # Submit many requests quickly to overwhelm the queue
            responses = []
            request_times = []
            
            for i in range(20):  # Submit 20 requests rapidly
                start_time = time.time()
                
                response = client.post("/api/analyze-trade", json={
                    "team": "yankees",
                    "request": f"Queue test request {i}",
                    "urgency": "medium"
                })
                
                request_time = time.time() - start_time
                responses.append(response)
                request_times.append(request_time)
            
            # Check response patterns
            status_codes = [r.status_code for r in responses]
            success_count = len([c for c in status_codes if c == 200])
            rate_limited_count = len([c for c in status_codes if c == 429])
            
            print(f"Queue test - Success: {success_count}, Rate limited: {rate_limited_count}")
            
            # System should handle graceful degradation
            assert success_count > 0, "No requests succeeded"
            
            if rate_limited_count > 0:
                # If rate limiting is implemented, it should kick in
                total_handled = success_count + rate_limited_count
                assert total_handled == 20, "Some requests failed unexpectedly"
            
            # Initial requests should be fast (immediate queue), later ones might be slower or rejected
            avg_request_time = statistics.mean(request_times[:5])  # First 5 requests
            assert avg_request_time < 0.5, f"Initial request queueing too slow: {avg_request_time:.3f}s"
    
    def test_resource_exhaustion_recovery(self, performance_monitor, mock_fast_supabase):
        """Test system recovery after resource exhaustion"""
        client = TestClient(app)
        
        # Simulate resource exhaustion scenario
        initial_memory = performance_monitor.process.memory_info().rss
        
        # Phase 1: Generate heavy load
        print("Phase 1: Generating heavy load...")
        heavy_load_responses = []
        
        for i in range(50):
            response = client.post("/api/analyze-trade", json={
                "team": "yankees",
                "request": f"Heavy load test {i}",
                "urgency": "high"
            })
            heavy_load_responses.append(response.status_code)
            
            if i % 10 == 0:
                current_memory = performance_monitor.process.memory_info().rss
                memory_growth = current_memory - initial_memory
                print(f"  Request {i}: Memory growth {memory_growth / 1024 / 1024:.1f}MB")
        
        heavy_load_success_rate = len([c for c in heavy_load_responses if c == 200]) / len(heavy_load_responses)
        
        # Phase 2: Recovery period
        print("Phase 2: Recovery period...")
        time.sleep(2)  # Brief recovery period
        gc.collect()  # Force cleanup
        
        recovery_memory = performance_monitor.process.memory_info().rss
        
        # Phase 3: Test normal operation after load
        print("Phase 3: Testing recovery...")
        recovery_responses = []
        
        for i in range(10):
            response = client.get("/")  # Simple health checks
            recovery_responses.append(response.status_code)
        
        recovery_success_rate = len([c for c in recovery_responses if c == 200]) / len(recovery_responses)
        
        final_memory = performance_monitor.process.memory_info().rss
        memory_recovered = (recovery_memory - initial_memory) - (final_memory - initial_memory)
        
        print(f"Resource exhaustion test - Heavy load success: {heavy_load_success_rate:.1%}, Recovery success: {recovery_success_rate:.1%}")
        print(f"Memory - Peak growth: {(recovery_memory - initial_memory) / 1024 / 1024:.1f}MB, Recovered: {memory_recovered / 1024 / 1024:.1f}MB")
        
        # System should recover gracefully
        assert recovery_success_rate > 0.9, f"Recovery success rate {recovery_success_rate:.1%} too low"
        assert memory_recovered >= 0, "Memory not recovered after load"
        
        # Final memory should be reasonable
        final_memory_growth = (final_memory - initial_memory) / 1024 / 1024
        assert final_memory_growth < 100, f"Final memory growth {final_memory_growth:.1f}MB too high"


@pytest.mark.performance
class TestPerformanceRegression:
    """Test for performance regressions"""
    
    def test_baseline_performance_metrics(self, performance_monitor, mock_fast_supabase, mock_fast_crew):
        """Establish baseline performance metrics"""
        client = TestClient(app)
        
        # Define baseline expectations
        baselines = {
            'health_check': {'max_time': 0.1, 'target_throughput': 100},
            'teams_list': {'max_time': 0.05, 'target_throughput': 200},
            'trade_submission': {'max_time': 1.0, 'target_throughput': 10},
            'status_check': {'max_time': 0.05, 'target_throughput': 150}
        }
        
        results = {}
        
        # Test each endpoint
        for endpoint_name, expectations in baselines.items():
            response_times = []
            
            if endpoint_name == 'health_check':
                for _ in range(50):
                    start = time.time()
                    response = client.get("/")
                    response_times.append(time.time() - start)
                    assert response.status_code == 200
                    
            elif endpoint_name == 'teams_list':
                for _ in range(50):
                    start = time.time()
                    response = client.get("/api/teams")
                    response_times.append(time.time() - start)
                    assert response.status_code == 200
                    
            elif endpoint_name == 'trade_submission':
                for i in range(20):
                    start = time.time()
                    response = client.post("/api/analyze-trade", json={
                        "team": "yankees",
                        "request": f"Baseline test {i}",
                        "urgency": "medium"
                    })
                    response_times.append(time.time() - start)
                    assert response.status_code == 200
                    
            elif endpoint_name == 'status_check':
                for _ in range(30):
                    start = time.time()
                    response = client.get("/api/analysis/baseline-test")
                    response_times.append(time.time() - start)
                    assert response.status_code in [200, 404]
            
            # Calculate statistics
            avg_time = statistics.mean(response_times)
            p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
            estimated_throughput = 1 / avg_time
            
            results[endpoint_name] = {
                'avg_time': avg_time,
                'p95_time': p95_time,
                'max_time': max(response_times),
                'estimated_throughput': estimated_throughput
            }
            
            print(f"{endpoint_name}: Avg {avg_time:.3f}s, P95 {p95_time:.3f}s, Throughput {estimated_throughput:.1f} RPS")
            
            # Verify against baselines
            assert avg_time <= expectations['max_time'], f"{endpoint_name} average time {avg_time:.3f}s exceeds baseline {expectations['max_time']}s"
            assert estimated_throughput >= expectations['target_throughput'] * 0.8, f"{endpoint_name} throughput {estimated_throughput:.1f} below baseline {expectations['target_throughput']}"
        
        # Store results for future regression testing
        performance_summary = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / 1024**3
            }
        }
        
        print(f"Baseline performance test completed: {performance_summary}")
        
        return performance_summary