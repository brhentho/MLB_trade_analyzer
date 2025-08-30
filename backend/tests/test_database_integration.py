"""
Integration tests for database operations with Supabase
Tests the actual database service layer functionality
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import uuid

from backend.services.supabase_service import SupabaseService, TradeAnalysisRecord


class TestSupabaseServiceIntegration:
    """Test Supabase service integration with database operations"""

    @pytest.fixture
    def supabase_service(self):
        """Create a test Supabase service instance"""
        with patch('backend.services.supabase_service.create_client'):
            service = SupabaseService()
            return service

    @pytest.fixture
    def mock_supabase_client(self, supabase_service):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        supabase_service.supabase = mock_client
        return mock_client

    class TestTeamOperations:
        """Test team-related database operations"""

        @pytest.mark.asyncio
        async def test_get_all_teams(self, supabase_service, mock_supabase_client):
            """Test retrieving all teams from database"""
            mock_response = Mock()
            mock_response.data = [
                {
                    'id': 1,
                    'team_key': 'yankees',
                    'name': 'New York Yankees',
                    'abbreviation': 'NYY',
                    'division': 'AL East',
                    'league': 'American League',
                    'budget_level': 'high',
                    'competitive_window': 'win-now',
                    'market_size': 'large'
                },
                {
                    'id': 2,
                    'team_key': 'redsox',
                    'name': 'Boston Red Sox',
                    'abbreviation': 'BOS',
                    'division': 'AL East',
                    'league': 'American League',
                    'budget_level': 'high',
                    'competitive_window': 'win-now',
                    'market_size': 'large'
                }
            ]
            
            mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
            
            # Clear cache to ensure fresh database call
            supabase_service._teams_cache = {}
            
            teams = await supabase_service.get_all_teams()
            
            assert len(teams) == 2
            assert teams[0]['team_key'] == 'yankees'
            assert teams[1]['team_key'] == 'redsox'

        @pytest.mark.asyncio
        async def test_get_team_by_key(self, supabase_service):
            """Test retrieving team by key"""
            # Setup cache with team data
            supabase_service._teams_cache = {
                'yankees': {
                    'id': 1,
                    'team_key': 'yankees',
                    'name': 'New York Yankees',
                    'division': 'AL East'
                }
            }
            
            team = await supabase_service.get_team_by_key('yankees')
            
            assert team is not None
            assert team['team_key'] == 'yankees'
            assert team['name'] == 'New York Yankees'

        @pytest.mark.asyncio
        async def test_get_team_by_key_not_found(self, supabase_service):
            """Test retrieving non-existent team"""
            supabase_service._teams_cache = {}
            
            team = await supabase_service.get_team_by_key('nonexistent')
            
            assert team is None

        @pytest.mark.asyncio
        async def test_update_team_info(self, supabase_service, mock_supabase_client):
            """Test updating team information"""
            mock_response = Mock()
            mock_response.data = [{'id': 1, 'updated_field': 'new_value'}]
            
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
            
            # Setup cache
            supabase_service._teams_cache = {1: {'id': 1, 'old_field': 'old_value'}}
            
            updates = {'updated_field': 'new_value'}
            result = await supabase_service.update_team_info(1, updates)
            
            assert result is True
            mock_supabase_client.table.assert_called_with('teams')

    class TestPlayerOperations:
        """Test player-related database operations"""

        @pytest.mark.asyncio
        async def test_get_player_by_name(self, supabase_service, mock_supabase_client):
            """Test retrieving player by name"""
            mock_response = Mock()
            mock_response.data = [{
                'id': 1,
                'name': 'Aaron Judge',
                'team_id': 1,
                'position': 'OF',
                'war': 8.2
            }]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            player = await supabase_service.get_player_by_name('Aaron Judge')
            
            assert player is not None
            assert player['name'] == 'Aaron Judge'
            assert player['position'] == 'OF'

        @pytest.mark.asyncio
        async def test_search_players(self, supabase_service, mock_supabase_client):
            """Test searching players by name"""
            mock_response = Mock()
            mock_response.data = [
                {'name': 'Aaron Judge', 'position': 'OF'},
                {'name': 'Aaron Nola', 'position': 'SP'}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.ilike.return_value.limit.return_value.execute.return_value = mock_response
            
            players = await supabase_service.search_players('Aaron')
            
            assert len(players) == 2
            assert all('Aaron' in player['name'] for player in players)

        @pytest.mark.asyncio
        async def test_get_team_roster(self, supabase_service, mock_supabase_client):
            """Test retrieving team roster"""
            mock_response = Mock()
            mock_response.data = [
                {'name': 'Player 1', 'team_id': 1, 'position': 'SS'},
                {'name': 'Player 2', 'team_id': 1, 'position': 'SP'}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            roster = await supabase_service.get_team_roster(1)
            
            assert len(roster) == 2
            assert all(player['team_id'] == 1 for player in roster)

        @pytest.mark.asyncio
        async def test_upsert_player_new(self, supabase_service, mock_supabase_client):
            """Test inserting new player"""
            # Mock player doesn't exist
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            # Mock successful insert
            mock_insert_response = Mock()
            mock_insert_response.data = [{'id': 1, 'name': 'New Player'}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_insert_response
            
            player_data = {'name': 'New Player', 'position': 'SP', 'war': 3.5}
            result = await supabase_service.upsert_player(player_data)
            
            assert result is True
            mock_supabase_client.table.return_value.insert.assert_called_once()

    class TestTradeAnalysisOperations:
        """Test trade analysis database operations"""

        @pytest.mark.asyncio
        async def test_create_trade_analysis(self, supabase_service, mock_supabase_client):
            """Test creating new trade analysis record"""
            mock_response = Mock()
            mock_response.data = [{'analysis_id': 'test-id'}]
            
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_response
            
            analysis = TradeAnalysisRecord(
                analysis_id='test-id',
                requesting_team_id=1,
                request_text='Test trade request',
                urgency='medium',
                status='queued'
            )
            
            result = await supabase_service.create_trade_analysis(analysis)
            
            assert result == 'test-id'
            mock_supabase_client.table.assert_called_with('trade_analyses')

        @pytest.mark.asyncio
        async def test_get_trade_analysis(self, supabase_service, mock_supabase_client):
            """Test retrieving trade analysis"""
            mock_response = Mock()
            mock_response.data = [{
                'id': 1,
                'analysis_id': 'test-id',
                'requesting_team_id': 1,
                'status': 'completed',
                'results': {'recommendation': 'Test result'}
            }]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            analysis = await supabase_service.get_trade_analysis('test-id')
            
            assert analysis is not None
            assert analysis['analysis_id'] == 'test-id'
            assert analysis['status'] == 'completed'

        @pytest.mark.asyncio
        async def test_update_trade_analysis_status(self, supabase_service, mock_supabase_client):
            """Test updating trade analysis status"""
            mock_response = Mock()
            mock_response.data = [{'analysis_id': 'test-id', 'status': 'completed'}]
            
            mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
            
            result = await supabase_service.update_trade_analysis_status(
                'test-id',
                'completed',
                results={'recommendation': 'Test'},
                cost_info={'tokens': 100}
            )
            
            assert result is True

        @pytest.mark.asyncio
        async def test_get_recent_trade_analyses(self, supabase_service, mock_supabase_client):
            """Test retrieving recent analyses"""
            mock_response = Mock()
            mock_response.data = [
                {'analysis_id': 'test-1', 'created_at': datetime.now().isoformat()},
                {'analysis_id': 'test-2', 'created_at': datetime.now().isoformat()}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = mock_response
            
            analyses = await supabase_service.get_recent_trade_analyses(limit=2)
            
            assert len(analyses) == 2
            assert analyses[0]['analysis_id'] == 'test-1'

    class TestTradeProposalOperations:
        """Test trade proposal database operations"""

        @pytest.mark.asyncio
        async def test_create_trade_proposals(self, supabase_service, mock_supabase_client):
            """Test creating trade proposals"""
            # Mock analysis lookup
            mock_analysis_response = Mock()
            mock_analysis_response.data = [{'id': 1, 'analysis_id': 'test-id'}]
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_analysis_response
            
            # Mock proposal creation
            mock_proposal_response = Mock()
            mock_proposal_response.data = [{'id': 1}, {'id': 2}]
            mock_supabase_client.table.return_value.insert.return_value.execute.return_value = mock_proposal_response
            
            proposals = [
                {
                    'teams_involved': ['Yankees', 'Red Sox'],
                    'players_involved': ['Player A', 'Player B'],
                    'likelihood': 'medium'
                }
            ]
            
            result = await supabase_service.create_trade_proposals('test-id', proposals)
            
            assert result is True

        @pytest.mark.asyncio
        async def test_get_trade_proposals(self, supabase_service, mock_supabase_client):
            """Test retrieving trade proposals"""
            # Mock analysis lookup
            mock_analysis_response = Mock()
            mock_analysis_response.data = [{'id': 1}]
            
            # Mock proposals retrieval
            mock_proposals_response = Mock()
            mock_proposals_response.data = [
                {
                    'id': 1,
                    'proposal_rank': 1,
                    'teams_involved': ['Yankees', 'Red Sox'],
                    'likelihood': 'medium'
                }
            ]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
                mock_analysis_response,
                mock_proposals_response
            ]
            
            proposals = await supabase_service.get_trade_proposals('test-id')
            
            assert len(proposals) == 1
            assert proposals[0]['proposal_rank'] == 1

    class TestAnalyticsOperations:
        """Test analytics and statistics operations"""

        @pytest.mark.asyncio
        async def test_get_team_stats_summary(self, supabase_service, mock_supabase_client):
            """Test team statistics calculation"""
            mock_response = Mock()
            mock_response.data = [
                {'war': 5.5, 'age': 28, 'salary': 10000000, 'position': 'SP'},
                {'war': 3.2, 'age': 26, 'salary': 8000000, 'position': 'OF'},
                {'war': 2.1, 'age': 30, 'salary': 5000000, 'position': 'SP'}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            stats = await supabase_service.get_team_stats_summary(1)
            
            assert stats['team_id'] == 1
            assert stats['total_players'] == 3
            assert stats['total_war'] == 10.8
            assert abs(stats['average_age'] - 28.0) < 0.1
            assert stats['total_salary'] == 23000000
            assert stats['position_breakdown']['SP'] == 2
            assert stats['position_breakdown']['OF'] == 1

        @pytest.mark.asyncio
        async def test_get_position_market_data(self, supabase_service, mock_supabase_client):
            """Test position market analysis"""
            mock_response = Mock()
            mock_response.data = [
                {'war': 6.0, 'salary': 15000000, 'age': 29, 'position': 'SP'},
                {'war': 4.5, 'salary': 12000000, 'age': 27, 'position': 'SP'},
                {'war': 3.2, 'salary': 8000000, 'age': 25, 'position': 'SP'}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
            
            market_data = await supabase_service.get_position_market_data('SP')
            
            assert market_data['position'] == 'SP'
            assert market_data['total_players'] == 3
            assert abs(market_data['avg_war'] - 4.57) < 0.1
            assert market_data['median_war'] == 4.5
            assert len(market_data['top_performers']) == 3

    class TestUtilityOperations:
        """Test utility and maintenance operations"""

        @pytest.mark.asyncio
        async def test_health_check(self, supabase_service, mock_supabase_client):
            """Test database health check"""
            # Mock teams count
            supabase_service._teams_cache = {'team1': {}, 'team2': {}}
            
            # Mock players count
            mock_players_response = Mock()
            mock_players_response.count = 500
            mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_players_response
            
            # Mock recent analyses
            mock_analyses_response = Mock()
            mock_analyses_response.data = [
                {'created_at': datetime.now().isoformat()},
                {'created_at': datetime.now().isoformat()}
            ]
            
            health = await supabase_service.health_check()
            
            assert health['status'] == 'healthy'
            assert health['teams_count'] == 2
            assert health['players_count'] == 500
            assert health['recent_analyses_count'] == 2

        @pytest.mark.asyncio
        async def test_cleanup_old_data(self, supabase_service, mock_supabase_client):
            """Test data cleanup functionality"""
            mock_response = Mock()
            mock_response.data = [{'id': 1}, {'id': 2}]  # 2 records cleaned
            
            mock_supabase_client.table.return_value.delete.return_value.lt.return_value.in_.return_value.execute.return_value = mock_response
            
            result = await supabase_service.cleanup_old_data(30)
            
            assert result['cleaned_analyses'] == 2
            assert 'cutoff_date' in result

    class TestErrorHandling:
        """Test database error handling scenarios"""

        @pytest.mark.asyncio
        async def test_database_connection_error(self, supabase_service, mock_supabase_client):
            """Test handling of database connection errors"""
            mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception("Connection failed")
            
            teams = await supabase_service.get_all_teams()
            
            # Should return empty list on error
            assert teams == []

        @pytest.mark.asyncio
        async def test_invalid_query_error(self, supabase_service, mock_supabase_client):
            """Test handling of invalid query errors"""
            mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Invalid query")
            
            player = await supabase_service.get_player_by_name("Invalid Name")
            
            assert player is None

        @pytest.mark.asyncio
        async def test_timeout_error(self, supabase_service, mock_supabase_client):
            """Test handling of database timeout errors"""
            import asyncio
            
            async def timeout_side_effect(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate timeout
                raise asyncio.TimeoutError("Query timeout")
            
            mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = timeout_side_effect
            
            analysis = TradeAnalysisRecord(
                analysis_id='timeout-test',
                requesting_team_id=1,
                request_text='Test',
                urgency='medium',
                status='queued'
            )
            
            result = await supabase_service.create_trade_analysis(analysis)
            
            assert result == ""  # Should return empty string on error

    class TestCacheManagement:
        """Test caching functionality"""

        @pytest.mark.asyncio
        async def test_cache_refresh(self, supabase_service, mock_supabase_client):
            """Test cache refresh functionality"""
            mock_response = Mock()
            mock_response.data = [
                {'id': 1, 'team_key': 'yankees', 'abbreviation': 'NYY'}
            ]
            
            mock_supabase_client.table.return_value.select.return_value.execute.return_value = mock_response
            
            # Clear cache
            supabase_service._teams_cache = {}
            supabase_service._cache_expiry = {}
            
            # This should trigger cache refresh
            teams = await supabase_service.get_all_teams()
            
            assert len(teams) == 1
            assert 'yankees' in supabase_service._teams_cache
            assert 1 in supabase_service._teams_cache  # Also keyed by ID

        def test_cache_expiry_check(self, supabase_service):
            """Test cache expiry logic"""
            # Set expired cache
            past_time = datetime.now() - timedelta(minutes=10)
            supabase_service._cache_expiry['teams'] = past_time
            
            assert supabase_service._is_cache_expired('teams') is True
            
            # Set fresh cache
            future_time = datetime.now() + timedelta(minutes=10)
            supabase_service._cache_expiry['teams'] = future_time
            
            assert supabase_service._is_cache_expired('teams') is False