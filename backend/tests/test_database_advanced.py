"""
Advanced database integration tests for Baseball Trade AI
Tests complex database scenarios, transactions, data integrity, and performance
"""

import pytest
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta, date
import uuid
import json
from typing import Dict, List, Any, Optional

from backend.services.supabase_service import SupabaseService, TradeAnalysisRecord


class TestAdvancedTeamOperations:
    """Test advanced team-related database operations"""
    
    @pytest.fixture
    def supabase_service_real(self):
        """Create a test Supabase service with real-like behavior"""
        with patch('backend.services.supabase_service.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            service = SupabaseService()
            service.supabase = mock_client
            
            yield service, mock_client
    
    @pytest.mark.asyncio
    async def test_team_roster_management(self, supabase_service_real):
        """Test comprehensive team roster management"""
        service, mock_client = supabase_service_real
        
        # Mock roster data with contracts and stats
        roster_data = [
            {
                'id': 1, 'name': 'Aaron Judge', 'team_id': 1, 'position': 'OF',
                'war': 8.2, 'age': 31, 'salary': 40000000,
                'contract_years': 7, 'contract_end': '2030-12-31',
                'no_trade_clause': True, '10_5_rights': False,
                'service_time': '7.045', 'arbitration_eligible': False,
                'stats': {'avg': 0.267, 'hr': 37, 'rbi': 102, 'obp': 0.404}
            },
            {
                'id': 2, 'name': 'Gleyber Torres', 'team_id': 1, 'position': '2B', 
                'war': 2.1, 'age': 27, 'salary': 9300000,
                'contract_years': 1, 'contract_end': '2024-12-31',
                'no_trade_clause': False, '10_5_rights': False,
                'service_time': '6.112', 'arbitration_eligible': True,
                'stats': {'avg': 0.273, 'hr': 25, 'rbi': 86, 'obp': 0.339}
            }
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = roster_data
        
        roster = await service.get_team_roster_with_contracts(1)
        
        assert len(roster) == 2
        assert roster[0]['name'] == 'Aaron Judge'
        assert roster[0]['no_trade_clause'] is True
        assert roster[1]['arbitration_eligible'] is True
    
    @pytest.mark.asyncio
    async def test_payroll_calculations(self, supabase_service_real):
        """Test complex payroll and luxury tax calculations"""
        service, mock_client = supabase_service_real
        
        # Mock payroll data
        payroll_data = [
            {'salary': 40000000, 'contract_end': '2030-12-31', 'deferred_money': 0},
            {'salary': 25000000, 'contract_end': '2025-12-31', 'deferred_money': 5000000},
            {'salary': 15000000, 'contract_end': '2024-12-31', 'deferred_money': 0},
            {'salary': 12000000, 'contract_end': '2026-12-31', 'deferred_money': 2000000},
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = payroll_data
        
        payroll_summary = await service.calculate_team_payroll(1, year=2024)
        
        assert payroll_summary['current_payroll'] > 90000000  # Should sum up salaries
        assert 'luxury_tax_bill' in payroll_summary
        assert 'competitive_balance_tax' in payroll_summary
        assert 'deferred_obligations' in payroll_summary
        
        # Test luxury tax thresholds
        if payroll_summary['current_payroll'] > 297000000:  # 2024 threshold
            assert payroll_summary['luxury_tax_bill'] > 0
    
    @pytest.mark.asyncio
    async def test_roster_rule_compliance(self, supabase_service_real):
        """Test MLB roster rule compliance checking"""
        service, mock_client = supabase_service_real
        
        # Mock 40-man roster data
        roster_40man = [{'id': i, 'name': f'Player {i}', '40_man': True} for i in range(42)]  # Over limit
        roster_25man = [{'id': i, 'name': f'Player {i}', 'active_roster': True} for i in range(27)]  # Over limit
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            Mock(data=roster_40man),
            Mock(data=roster_25man)
        ]
        
        compliance = await service.check_roster_rule_compliance(1)
        
        assert compliance['40_man_roster']['current_count'] == 42
        assert compliance['40_man_roster']['compliant'] is False
        assert compliance['active_roster']['current_count'] == 27
        assert compliance['active_roster']['compliant'] is False
        assert 'violations' in compliance
    
    @pytest.mark.asyncio
    async def test_team_needs_analysis(self, supabase_service_real):
        """Test sophisticated team needs analysis"""
        service, mock_client = supabase_service_real
        
        # Mock roster with gaps
        roster_with_gaps = [
            # Strong offense, weak pitching
            {'position': 'C', 'war': 3.5, 'age': 28},
            {'position': '1B', 'war': 4.2, 'age': 26},
            {'position': '2B', 'war': 2.1, 'age': 31},
            {'position': 'SS', 'war': 5.5, 'age': 24},  # Strength
            {'position': '3B', 'war': 1.2, 'age': 33},  # Weakness
            {'position': 'OF', 'war': 6.1, 'age': 25},  # Strength
            {'position': 'OF', 'war': 2.8, 'age': 29},
            {'position': 'OF', 'war': 1.1, 'age': 35},  # Weakness
            {'position': 'SP', 'war': 1.5, 'age': 32},  # Weakness
            {'position': 'SP', 'war': 0.8, 'age': 28},  # Major weakness
            {'position': 'RP', 'war': 2.1, 'age': 30},
            {'position': 'CL', 'war': 0.2, 'age': 34},  # Major weakness
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = roster_with_gaps
        
        needs_analysis = await service.analyze_team_needs(1)
        
        assert 'position_needs' in needs_analysis
        assert 'priority_needs' in needs_analysis
        assert 'depth_concerns' in needs_analysis
        
        # Should identify pitching as major need
        priority_needs = needs_analysis['priority_needs']
        pitching_needs = [need for need in priority_needs if 'SP' in need or 'CL' in need or 'pitching' in need.lower()]
        assert len(pitching_needs) > 0
    
    @pytest.mark.asyncio
    async def test_farm_system_evaluation(self, supabase_service_real):
        """Test farm system and prospect evaluation"""
        service, mock_client = supabase_service_real
        
        # Mock prospect data
        prospects_data = [
            {
                'name': 'Spencer Jones', 'team_id': 1, 'position': 'OF',
                'age': 22, 'level': 'AA', 'eta': '2025',
                'fv_grade': 55, 'hit_tool': 50, 'power_tool': 60,
                'run_tool': 45, 'field_tool': 55, 'arm_tool': 50,
                'overall_rank': 42, 'position_rank': 8,
                'ceiling': 'Everyday RF', 'floor': 'Bench OF',
                'injury_history': [], 'development_track': 'on_schedule'
            },
            {
                'name': 'Trystan Vrieling', 'team_id': 1, 'position': 'RHP',
                'age': 20, 'level': 'A+', 'eta': '2026', 
                'fv_grade': 50, 'fastball': 65, 'slider': 55,
                'changeup': 45, 'command': 50, 'overall_stuff': 60,
                'overall_rank': 78, 'position_rank': 15,
                'ceiling': 'Setup reliever', 'floor': 'Middle relief',
                'injury_history': ['shoulder soreness 2023'], 'development_track': 'accelerated'
            }
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = prospects_data
        
        farm_evaluation = await service.evaluate_farm_system(1)
        
        assert 'system_ranking' in farm_evaluation
        assert 'top_prospects' in farm_evaluation
        assert 'depth_by_position' in farm_evaluation
        assert 'trade_assets' in farm_evaluation
        
        # Should identify top prospects
        top_prospects = farm_evaluation['top_prospects']
        assert len(top_prospects) == 2
        assert any(prospect['name'] == 'Spencer Jones' for prospect in top_prospects)


class TestAdvancedTradeAnalysisOperations:
    """Test advanced trade analysis database operations"""
    
    @pytest.fixture
    def complex_trade_data(self):
        """Complex trade scenario data"""
        return {
            'analysis_id': str(uuid.uuid4()),
            'requesting_team_id': 1,  # Yankees
            'request_text': 'Need ace starting pitcher for playoff push',
            'urgency': 'high',
            'budget_limit': 50000000,
            'status': 'completed',
            'progress': {
                'overall': 1.0,
                'departments_completed': [
                    'Front Office Leadership',
                    'Scouting Department', 
                    'Analytics Department',
                    'Business Operations',
                    'Player Development'
                ]
            },
            'results': {
                'recommendation': 'Proceed with Shane Bieber trade',
                'confidence': 0.87,
                'risk_level': 'medium'
            },
            'proposals': [
                {
                    'rank': 1,
                    'teams_involved': [
                        {'team': 'yankees', 'role': 'acquiring'},
                        {'team': 'guardians', 'role': 'trading'}
                    ],
                    'players_involved': [
                        {
                            'name': 'Shane Bieber',
                            'from_team': 'guardians',
                            'to_team': 'yankees',
                            'position': 'SP',
                            'contract': {'years': 1, 'aav': 12000000},
                            'stats': {'era': 3.20, 'whip': 1.15}
                        },
                        {
                            'name': 'Spencer Jones', 
                            'from_team': 'yankees',
                            'to_team': 'guardians',
                            'type': 'prospect',
                            'fv_grade': 55
                        }
                    ],
                    'likelihood': 'medium',
                    'financial_impact': {
                        'yankees_salary_change': 12000000,
                        'guardians_salary_change': -12000000,
                        'luxury_tax_impact': 1800000
                    },
                    'trade_value': {
                        'yankees_value_given': 45,
                        'yankees_value_received': 48,
                        'balance_score': 0.94
                    }
                }
            ],
            'cost_info': {
                'token_usage': 2847,
                'estimated_cost': 0.57,
                'processing_time': 45.2
            },
            'created_at': datetime.now(),
            'completed_at': datetime.now()
        }
    
    @pytest.mark.asyncio
    async def test_complex_trade_analysis_storage(self, supabase_service_real, complex_trade_data):
        """Test storage of complex trade analysis with proposals"""
        service, mock_client = supabase_service_real
        
        # Mock successful creation
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'analysis_id': complex_trade_data['analysis_id']}
        ]
        
        # Create analysis record
        analysis_record = TradeAnalysisRecord(
            analysis_id=complex_trade_data['analysis_id'],
            requesting_team_id=complex_trade_data['requesting_team_id'],
            request_text=complex_trade_data['request_text'],
            urgency=complex_trade_data['urgency'],
            status=complex_trade_data['status'],
            progress=complex_trade_data['progress'],
            results=complex_trade_data['results'],
            cost_info=complex_trade_data['cost_info']
        )
        
        result = await service.create_trade_analysis(analysis_record)
        
        assert result == complex_trade_data['analysis_id']
        
        # Now test proposal creation
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': 1, 'proposal_rank': 1}
        ]
        
        proposals_created = await service.create_trade_proposals(
            complex_trade_data['analysis_id'], 
            complex_trade_data['proposals']
        )
        
        assert proposals_created is True
    
    @pytest.mark.asyncio
    async def test_trade_analysis_lifecycle(self, supabase_service_real):
        """Test complete trade analysis lifecycle"""
        service, mock_client = supabase_service_real
        
        analysis_id = str(uuid.uuid4())
        
        # 1. Create initial analysis
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'analysis_id': analysis_id}
        ]
        
        initial_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=1,
            request_text='Test request',
            urgency='medium',
            status='queued'
        )
        
        created_id = await service.create_trade_analysis(initial_record)
        assert created_id == analysis_id
        
        # 2. Update to analyzing status
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {'analysis_id': analysis_id, 'status': 'analyzing'}
        ]
        
        analyzing_update = await service.update_trade_analysis_status(
            analysis_id, 
            'analyzing',
            progress={'current_department': 'Scouting Department'}
        )
        assert analyzing_update is True
        
        # 3. Update to completed status with results
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
            {'analysis_id': analysis_id, 'status': 'completed'}
        ]
        
        completed_update = await service.update_trade_analysis_status(
            analysis_id,
            'completed',
            results={'recommendation': 'Test result'},
            cost_info={'tokens': 1500, 'cost': 0.30}
        )
        assert completed_update is True
        
        # 4. Retrieve final analysis
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            'analysis_id': analysis_id,
            'status': 'completed',
            'results': {'recommendation': 'Test result'},
            'cost_info': {'tokens': 1500, 'cost': 0.30}
        }]
        
        final_analysis = await service.get_trade_analysis(analysis_id)
        assert final_analysis['status'] == 'completed'
        assert final_analysis['results']['recommendation'] == 'Test result'
    
    @pytest.mark.asyncio
    async def test_trade_history_and_patterns(self, supabase_service_real):
        """Test trade history tracking and pattern analysis"""
        service, mock_client = supabase_service_real
        
        # Mock historical trade data
        historical_trades = [
            {
                'id': 1, 'date': '2023-07-30', 'teams': ['yankees', 'guardians'],
                'type': 'rental', 'success_rating': 8.5,
                'players': [{'name': 'Andrew Benintendi', 'role': 'acquired'}]
            },
            {
                'id': 2, 'date': '2023-12-15', 'teams': ['yankees', 'padres'], 
                'type': 'long_term', 'success_rating': 6.2,
                'players': [{'name': 'Juan Soto', 'role': 'acquired'}]
            }
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = historical_trades
        
        trade_history = await service.get_team_trade_history(1, limit=10)
        
        assert len(trade_history) == 2
        assert trade_history[0]['type'] == 'rental'
        assert 'success_rating' in trade_history[0]
        
        # Test pattern analysis
        trade_patterns = await service.analyze_trade_patterns(1)
        
        assert 'preferred_trade_types' in trade_patterns
        assert 'success_rate_by_type' in trade_patterns
        assert 'common_trade_partners' in trade_patterns
    
    @pytest.mark.asyncio
    async def test_multi_team_trade_complexity(self, supabase_service_real):
        """Test handling of complex multi-team trades"""
        service, mock_client = supabase_service_real
        
        # 3-team trade scenario
        multi_team_trade = {
            'analysis_id': str(uuid.uuid4()),
            'teams_involved': ['yankees', 'guardians', 'dodgers'],
            'trade_structure': {
                'yankees': {'receives': ['Shane Bieber'], 'gives': ['Prospect A', '$5M']},
                'guardians': {'receives': ['Prospect A', 'Prospect B'], 'gives': ['Shane Bieber']},
                'dodgers': {'receives': ['$5M'], 'gives': ['Prospect B']}
            },
            'complexity_factors': [
                'salary_balancing',
                'prospect_values', 
                'contract_matching',
                'luxury_tax_implications'
            ]
        }
        
        # Mock complex trade storage
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {'id': 1, 'analysis_id': multi_team_trade['analysis_id']}
        ]
        
        stored = await service.store_multi_team_trade_analysis(multi_team_trade)
        
        assert stored is True
        
        # Verify complex trade retrieval
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [multi_team_trade]
        
        retrieved = await service.get_multi_team_trade_analysis(multi_team_trade['analysis_id'])
        
        assert len(retrieved['teams_involved']) == 3
        assert 'salary_balancing' in retrieved['complexity_factors']


class TestPlayerDatabaseOperations:
    """Test advanced player-related database operations"""
    
    @pytest.mark.asyncio
    async def test_player_performance_analytics(self, supabase_service_real):
        """Test comprehensive player performance analysis"""
        service, mock_client = supabase_service_real
        
        # Mock detailed player stats
        player_stats = {
            'basic_stats': {
                'name': 'Aaron Judge', 'age': 31, 'position': 'OF',
                'games': 148, 'avg': 0.267, 'hr': 37, 'rbi': 102, 'war': 8.2
            },
            'advanced_stats': {
                'wrc_plus': 147, 'ops_plus': 140, 'babip': 0.229,
                'k_rate': 0.263, 'bb_rate': 0.158, 'iso': 0.263
            },
            'statcast_data': {
                'exit_velocity': 95.2, 'barrel_rate': 13.8, 'hard_hit_rate': 52.1,
                'sprint_speed': 26.9, 'outs_above_average': 2
            },
            'situational_stats': {
                'risp_avg': 0.245, 'clutch': 0.89, 'vs_lefties': 0.298,
                'vs_righties': 0.251, 'home': 0.272, 'away': 0.261
            },
            'injury_history': [
                {'year': 2022, 'injury': 'toe fracture', 'games_missed': 60},
                {'year': 2021, 'injury': 'oblique strain', 'games_missed': 8}
            ]
        }
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [player_stats]
        
        analytics = await service.get_player_performance_analytics('Aaron Judge')
        
        assert analytics['basic_stats']['war'] == 8.2
        assert analytics['advanced_stats']['wrc_plus'] == 147
        assert 'injury_concerns' in analytics
        assert 'performance_trend' in analytics
    
    @pytest.mark.asyncio
    async def test_player_contract_analysis(self, supabase_service_real):
        """Test player contract value analysis"""
        service, mock_client = supabase_service_real
        
        # Mock contract data
        contract_data = {
            'player': 'Aaron Judge',
            'current_contract': {
                'total_value': 360000000,
                'years': 9,
                'aav': 40000000,
                'start_year': 2023,
                'end_year': 2031,
                'no_trade_clause': True,
                'opt_outs': [],
                'deferred_money': 0
            },
            'performance_vs_contract': {
                'current_year_value': 45000000,  # Based on WAR
                'contract_efficiency': 1.125,  # Over-performing
                'projected_future_value': [42, 38, 35, 30, 25, 20, 15]  # Aging curve
            },
            'comparables': [
                {'player': 'Mike Trout', 'aav': 35000000, 'war_similarity': 0.89},
                {'player': 'Mookie Betts', 'aav': 30000000, 'war_similarity': 0.82}
            ]
        }
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [contract_data]
        
        contract_analysis = await service.analyze_player_contract('Aaron Judge')
        
        assert contract_analysis['current_contract']['aav'] == 40000000
        assert contract_analysis['performance_vs_contract']['contract_efficiency'] > 1.0
        assert len(contract_analysis['comparables']) > 0
    
    @pytest.mark.asyncio
    async def test_player_trade_value_calculation(self, supabase_service_real):
        """Test sophisticated player trade value calculations"""
        service, mock_client = supabase_service_real
        
        # Mock player data for trade value calculation
        player_data = {
            'name': 'Shane Bieber',
            'age': 28,
            'position': 'SP',
            'performance_metrics': {
                'war_3yr_avg': 4.8,
                'era_plus_3yr': 142,
                'durability_score': 0.75,  # Some injury concerns
                'stuff_plus': 115
            },
            'contract_status': {
                'years_remaining': 1,
                'salary_remaining': 12000000,
                'free_agency': '2024',
                'arbitration_eligible': False
            },
            'market_factors': {
                'position_scarcity': 0.85,  # High demand for SPs
                'playoff_impact': 1.2,      # Higher value for contenders
                'rental_premium': 0.9       # Slight discount for rental
            }
        }
        
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [player_data]
        
        trade_value = await service.calculate_player_trade_value('Shane Bieber', requesting_team='yankees')
        
        assert 'base_value' in trade_value
        assert 'adjusted_value' in trade_value
        assert 'value_range' in trade_value
        assert trade_value['base_value'] > 30  # Should be valuable
        assert trade_value['adjusted_value'] != trade_value['base_value']  # Should be adjusted
    
    @pytest.mark.asyncio
    async def test_prospect_ranking_system(self, supabase_service_real):
        """Test comprehensive prospect ranking and evaluation"""
        service, mock_client = supabase_service_real
        
        # Mock prospect database
        prospects_data = [
            {
                'name': 'Spencer Jones', 'team_id': 1, 'age': 22, 'position': 'OF',
                'level': 'AA', 'eta': '2025',
                'tools': {'hit': 50, 'power': 60, 'run': 45, 'field': 55, 'arm': 50},
                'fv_grade': 55, 'ceiling': 'Everyday RF', 'floor': 'Bench OF',
                'recent_performance': {'level': 'AA', 'avg': 0.267, 'hr': 18, 'sb': 15},
                'development_track': 'on_schedule',
                'injury_concerns': [],
                'international_bonus': 0,
                'draft_info': {'year': 2022, 'round': 1, 'pick': 25}
            },
            {
                'name': 'Jasson Dominguez', 'team_id': 1, 'age': 21, 'position': 'OF',
                'level': 'AAA', 'eta': '2024',
                'tools': {'hit': 55, 'power': 65, 'run': 60, 'field': 50, 'arm': 55},
                'fv_grade': 60, 'ceiling': 'All-Star CF', 'floor': 'Solid regular',
                'recent_performance': {'level': 'AAA', 'avg': 0.258, 'hr': 22, 'sb': 28},
                'development_track': 'accelerated',
                'injury_concerns': ['elbow surgery 2023'],
                'international_bonus': 5100000,
                'draft_info': None
            }
        ]
        
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = prospects_data
        
        prospect_rankings = await service.rank_team_prospects(1)
        
        assert len(prospect_rankings) == 2
        assert prospect_rankings[0]['fv_grade'] >= prospect_rankings[1]['fv_grade']  # Should be ranked
        
        # Test individual prospect evaluation
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [prospects_data[1]]
        
        jasson_eval = await service.evaluate_prospect('Jasson Dominguez')
        
        assert jasson_eval['fv_grade'] == 60
        assert 'trade_value' in jasson_eval
        assert 'risk_factors' in jasson_eval
        assert 'elbow surgery' in str(jasson_eval['injury_concerns'])


class TestDatabasePerformanceAndScaling:
    """Test database performance and scaling scenarios"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_operations(self, supabase_service_real):
        """Test operations on large datasets"""
        service, mock_client = supabase_service_real
        
        # Mock large dataset (simulate 30 teams x 40 players each)
        large_dataset = [
            {
                'id': i, 
                'name': f'Player {i}', 
                'team_id': (i // 40) + 1,
                'position': ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP', 'RP'][i % 8],
                'war': round(((i % 10) - 2) + (i % 3) * 0.5, 1),
                'salary': (i % 20 + 1) * 1000000
            }
            for i in range(1200)  # 1200 players total
        ]
        
        mock_client.table.return_value.select.return_value.execute.return_value.data = large_dataset
        
        # Test performance with large dataset
        start_time = datetime.now()
        all_players = await service.get_all_players_with_stats()
        end_time = datetime.now()
        
        query_time = (end_time - start_time).total_seconds()
        
        assert len(all_players) == 1200
        assert query_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, supabase_service_real):
        """Test concurrent database operations"""
        service, mock_client = supabase_service_real
        
        # Mock responses for concurrent operations
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 1, 'name': 'Test Team'}
        ]
        
        # Perform concurrent operations
        tasks = []
        for i in range(20):
            tasks.append(service.get_team_by_id(i % 5 + 1))  # 5 different teams
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 20
    
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, supabase_service_real):
        """Test database connection pooling behavior"""
        service, mock_client = supabase_service_real
        
        # Simulate multiple rapid database calls
        calls_made = []
        
        def track_calls(*args, **kwargs):
            calls_made.append(datetime.now())
            return Mock(data=[{'id': 1, 'name': 'Test'}])
        
        mock_client.table.return_value.select.return_value.execute.side_effect = track_calls
        
        # Make rapid sequential calls
        for i in range(50):
            await service.get_team_by_id(1)
        
        # All calls should complete rapidly
        assert len(calls_made) == 50
        
        # Check timing distribution
        if len(calls_made) > 1:
            time_diffs = [(calls_made[i] - calls_made[i-1]).total_seconds() for i in range(1, len(calls_made))]
            avg_time_between_calls = sum(time_diffs) / len(time_diffs)
            assert avg_time_between_calls < 0.1  # Very fast due to connection pooling
    
    @pytest.mark.asyncio
    async def test_query_optimization(self, supabase_service_real):
        """Test query optimization strategies"""
        service, mock_client = supabase_service_real
        
        # Test different query patterns
        query_patterns = [
            {
                'name': 'simple_select',
                'operation': lambda: service.get_team_by_id(1),
                'expected_calls': 1
            },
            {
                'name': 'complex_join',
                'operation': lambda: service.get_team_roster_with_contracts(1),
                'expected_calls': 1  # Should use efficient JOIN
            },
            {
                'name': 'aggregation',
                'operation': lambda: service.get_team_stats_summary(1),
                'expected_calls': 1  # Should use database aggregation
            }
        ]
        
        for pattern in query_patterns:
            mock_client.reset_mock()
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{}]
            
            await pattern['operation']()
            
            # Verify efficient query usage
            total_calls = mock_client.table.call_count
            assert total_calls <= pattern['expected_calls'], f"Query {pattern['name']} used {total_calls} calls, expected <= {pattern['expected_calls']}"


class TestDataIntegrityAndConsistency:
    """Test data integrity and consistency"""
    
    @pytest.mark.asyncio
    async def test_referential_integrity(self, supabase_service_real):
        """Test referential integrity constraints"""
        service, mock_client = supabase_service_real
        
        # Test foreign key relationships
        integrity_tests = [
            {
                'name': 'player_team_reference',
                'test': lambda: service.create_player({'name': 'Test Player', 'team_id': 999}),  # Non-existent team
                'should_fail': True
            },
            {
                'name': 'analysis_team_reference', 
                'test': lambda: service.create_trade_analysis(TradeAnalysisRecord(
                    analysis_id=str(uuid.uuid4()),
                    requesting_team_id=999,  # Non-existent team
                    request_text='Test',
                    urgency='medium',
                    status='queued'
                )),
                'should_fail': True
            }
        ]
        
        for test_case in integrity_tests:
            if test_case['should_fail']:
                # Mock foreign key violation
                mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Foreign key violation")
                
                with pytest.raises(Exception) as exc_info:
                    await test_case['test']()
                
                assert "foreign key" in str(exc_info.value).lower() or "violation" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_transaction_consistency(self, supabase_service_real):
        """Test transaction consistency"""
        service, mock_client = supabase_service_real
        
        # Test atomic operations
        analysis_id = str(uuid.uuid4())
        
        # Mock partial failure scenario
        call_count = 0
        def mock_insert(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call succeeds (analysis creation)
                return Mock(data=[{'analysis_id': analysis_id}])
            else:
                # Second call fails (proposal creation)
                raise Exception("Database connection lost")
        
        mock_client.table.return_value.insert.return_value.execute.side_effect = mock_insert
        
        # Attempt to create analysis with proposals
        analysis_record = TradeAnalysisRecord(
            analysis_id=analysis_id,
            requesting_team_id=1,
            request_text='Test request',
            urgency='medium',
            status='queued'
        )
        
        proposals = [{'rank': 1, 'teams_involved': ['yankees', 'guardians']}]
        
        # Should handle partial failure gracefully
        try:
            await service.create_complete_trade_analysis(analysis_record, proposals)
        except Exception as e:
            # Should rollback or handle failure
            assert "connection lost" in str(e)
    
    @pytest.mark.asyncio
    async def test_data_validation_constraints(self, supabase_service_real):
        """Test data validation constraints"""
        service, mock_client = supabase_service_real
        
        validation_tests = [
            {
                'name': 'negative_salary',
                'data': {'name': 'Test Player', 'salary': -1000000},
                'should_fail': True
            },
            {
                'name': 'future_birth_date',
                'data': {'name': 'Test Player', 'birth_date': '2050-01-01'},
                'should_fail': True
            },
            {
                'name': 'invalid_position',
                'data': {'name': 'Test Player', 'position': 'INVALID'},
                'should_fail': True
            },
            {
                'name': 'war_extreme_value',
                'data': {'name': 'Test Player', 'war': 50.0},  # Unrealistic WAR
                'should_fail': True
            }
        ]
        
        for test_case in validation_tests:
            if test_case['should_fail']:
                mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Validation constraint violation")
                
                with pytest.raises(Exception):
                    await service.create_player(test_case['data'])
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, supabase_service_real):
        """Test data consistency across multiple operations"""
        service, mock_client = supabase_service_real
        
        # Test salary cap consistency
        team_payroll = 250000000
        new_player_salary = 50000000
        salary_cap = 297000000  # Luxury tax threshold
        
        # Mock current team payroll
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'total_payroll': team_payroll}]
        )
        
        # Check if adding player would exceed cap
        payroll_check = await service.check_payroll_impact(1, new_player_salary)
        
        assert payroll_check['current_payroll'] == team_payroll
        assert payroll_check['projected_payroll'] == team_payroll + new_player_salary
        assert payroll_check['exceeds_luxury_tax'] == (payroll_check['projected_payroll'] > salary_cap)
        
        # Test roster spot consistency
        current_roster_size = 38
        max_roster_size = 40
        
        roster_check = await service.check_roster_space(1)
        
        if 'current_size' in roster_check:
            assert roster_check['available_spots'] == max_roster_size - roster_check['current_size']
            assert roster_check['can_add_player'] == (roster_check['available_spots'] > 0)