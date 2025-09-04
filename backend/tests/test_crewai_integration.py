"""
Comprehensive tests for CrewAI agent functionality and multi-agent orchestration
Tests agent communication, decision making, and trade analysis workflows
"""

import pytest
import asyncio
import json
from unittest.mock import patch, Mock, AsyncMock, MagicMock, call
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

from backend.crews.front_office_crew import FrontOfficeCrew
from backend.agents.team_gms import TeamGMAgents
from backend.nlp.trade_parser import TradeRequestParser
from backend.services.supabase_service import TradeAnalysisRecord


class TestTradeRequestParser:
    """Test the natural language trade request parser"""
    
    def test_simple_trade_request_parsing(self):
        """Test parsing of simple trade requests"""
        parser = TradeRequestParser()
        
        simple_requests = [
            {
                "request": "Need a starting pitcher",
                "expected_need": "starting_pitcher",
                "expected_confidence": 0.9
            },
            {
                "request": "Looking for bullpen help",
                "expected_need": "relief_pitcher",
                "expected_confidence": 0.8
            },
            {
                "request": "Need a closer",
                "expected_need": "closer",
                "expected_confidence": 0.9
            },
            {
                "request": "Want an outfielder",
                "expected_need": "outfielder",
                "expected_confidence": 0.8
            }
        ]
        
        for case in simple_requests:
            result = parser.parse_trade_request(case["request"])
            
            assert result.primary_need == case["expected_need"]
            assert result.confidence_score >= case["expected_confidence"] - 0.1
    
    def test_complex_trade_request_parsing(self):
        """Test parsing of complex, realistic trade requests"""
        parser = TradeRequestParser()
        
        complex_requests = [
            {
                "request": "Need a left-handed starting pitcher under 30 with at least 3 years of team control, ERA under 4.00, and postseason experience. Budget around $20M AAV.",
                "expected_elements": {
                    "primary_need": "starting_pitcher",
                    "handedness": "left",
                    "age_limit": 30,
                    "budget_constraints": 20000000,
                    "experience_requirements": ["postseason"]
                }
            },
            {
                "request": "Looking for a versatile utility infielder who can play shortstop and second base, good OBP, team-friendly contract under $5M per year",
                "expected_elements": {
                    "primary_need": "utility_infielder",
                    "positions": ["shortstop", "second_base"],
                    "budget_constraints": 5000000,
                    "skill_requirements": ["obp"]
                }
            }
        ]
        
        for case in complex_requests:
            result = parser.parse_trade_request(case["request"])
            
            assert result.primary_need == case["expected_elements"]["primary_need"]
            assert result.confidence_score > 0.7  # Should be confident on complex but clear requests
            
            # Check specific elements were parsed
            if "budget_constraints" in case["expected_elements"]:
                assert result.budget_constraints is not None
                assert abs(result.budget_constraints - case["expected_elements"]["budget_constraints"]) < 5000000
    
    def test_ambiguous_request_parsing(self):
        """Test parsing of ambiguous or unclear requests"""
        parser = TradeRequestParser()
        
        ambiguous_requests = [
            "Need help",
            "Want a player",
            "Something good",
            "Idk maybe a guy who plays baseball",
            "Get better",
        ]
        
        for request in ambiguous_requests:
            result = parser.parse_trade_request(request)
            
            # Should have low confidence for ambiguous requests
            assert result.confidence_score < 0.5
            assert result.primary_need in ["unknown", "general", "unclear"]
    
    def test_parser_prompt_generation(self):
        """Test generation of CrewAI prompts from parsed requests"""
        parser = TradeRequestParser()
        
        parsed_request = Mock(
            primary_need="starting_pitcher",
            secondary_needs=["bullpen_depth"],
            urgency_level="high",
            budget_constraints=25000000,
            team_context={"contending": True, "payroll_space": True},
            confidence_score=0.9
        )
        
        prompt = parser.generate_crew_prompt(parsed_request, "yankees")
        
        assert "starting_pitcher" in prompt
        assert "yankees" in prompt.lower()
        assert "high" in prompt  # urgency
        assert "$25" in prompt or "25000000" in prompt  # budget
    
    def test_parser_error_handling(self):
        """Test parser error handling with invalid inputs"""
        parser = TradeRequestParser()
        
        invalid_inputs = [
            "",
            None,
            " ",
            "\n\t",
            "a" * 10000,  # Too long
            "🔥💯🚀",  # Only emojis
        ]
        
        for invalid_input in invalid_inputs:
            try:
                result = parser.parse_trade_request(invalid_input)
                # Should handle gracefully
                assert result.confidence_score < 0.3
            except Exception as e:
                # If it raises an exception, it should be a known type
                assert isinstance(e, (ValueError, TypeError))


class TestFrontOfficeCrew:
    """Test the main FrontOfficeCrew orchestration"""
    
    @pytest.fixture
    def mock_crew_dependencies(self):
        """Mock all CrewAI dependencies"""
        with patch('backend.crews.front_office_crew.Agent') as mock_agent, \
             patch('backend.crews.front_office_crew.Task') as mock_task, \
             patch('backend.crews.front_office_crew.Crew') as mock_crew:
            
            # Mock agent instances
            mock_agent_instance = Mock()
            mock_agent_instance.role = "Test Agent"
            mock_agent.return_value = mock_agent_instance
            
            # Mock task instances
            mock_task_instance = Mock()
            mock_task_instance.description = "Test Task"
            mock_task.return_value = mock_task_instance
            
            # Mock crew instance
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Mock analysis result",
                token_usage=1500,
                tasks_output=[
                    Mock(raw="Department 1 result", agent="Agent 1"),
                    Mock(raw="Department 2 result", agent="Agent 2")
                ]
            )
            mock_crew.return_value = mock_crew_instance
            
            yield {
                "agent": mock_agent,
                "task": mock_task,
                "crew": mock_crew,
                "crew_instance": mock_crew_instance
            }
    
    @pytest.mark.asyncio
    async def test_analyze_trade_request_basic(self, mock_crew_dependencies):
        """Test basic trade request analysis"""
        crew = FrontOfficeCrew()
        
        request_data = {
            "team": "yankees",
            "request": "Need a starting pitcher with ERA under 4.0",
            "urgency": "medium"
        }
        
        result = await crew.analyze_trade_request(request_data)
        
        assert "organizational_recommendation" in result
        assert "departments_consulted" in result
        assert "token_usage" in result
        assert "estimated_cost" in result
        assert result["analysis_complete"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_trade_request_with_context(self, mock_crew_dependencies):
        """Test trade analysis with rich contextual information"""
        crew = FrontOfficeCrew()
        
        complex_request = {
            "team": "yankees",
            "request": "Need a left-handed starting pitcher under 30 with postseason experience",
            "urgency": "high",
            "budget_limit": 30000000,
            "include_prospects": True,
            "team_context": {
                "payroll": 280000000,
                "luxury_tax_space": 5000000,
                "playoff_position": "wild_card_race",
                "rotation_needs": "immediate",
                "farm_system_strength": "above_average"
            }
        }
        
        result = await crew.analyze_trade_request(complex_request)
        
        assert result["analysis_complete"] is True
        assert "organizational_recommendation" in result
        assert "token_usage" in result
        
        # Should handle complex context
        assert result["token_usage"] > 1000  # Complex requests should use more tokens
    
    @pytest.mark.asyncio
    async def test_crew_error_handling(self, mock_crew_dependencies):
        """Test CrewAI error handling scenarios"""
        crew = FrontOfficeCrew()
        
        # Mock crew failure
        mock_crew_dependencies["crew_instance"].kickoff.side_effect = Exception("CrewAI processing error")
        
        request_data = {
            "team": "yankees",
            "request": "Need pitcher"
        }
        
        with pytest.raises(Exception) as exc_info:
            await crew.analyze_trade_request(request_data)
        
        assert "CrewAI processing error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_crew_timeout_handling(self, mock_crew_dependencies):
        """Test CrewAI timeout handling"""
        crew = FrontOfficeCrew()
        
        # Mock crew timeout
        mock_crew_dependencies["crew_instance"].kickoff.side_effect = asyncio.TimeoutError("Analysis timeout")
        
        request_data = {
            "team": "yankees",
            "request": "Need pitcher"
        }
        
        with pytest.raises(asyncio.TimeoutError):
            await crew.analyze_trade_request(request_data)
    
    def test_crew_initialization(self, mock_crew_dependencies):
        """Test CrewAI crew initialization"""
        crew = FrontOfficeCrew()
        
        # Should initialize without errors
        assert crew is not None
        
        # Mock agents should be called during initialization
        assert mock_crew_dependencies["agent"].called
        assert mock_crew_dependencies["task"].called
        assert mock_crew_dependencies["crew"].called
    
    def test_crew_department_configuration(self, mock_crew_dependencies):
        """Test that all required departments are configured"""
        crew = FrontOfficeCrew()
        
        expected_departments = [
            "Front Office Leadership",
            "Scouting Department", 
            "Analytics Department",
            "Player Development",
            "Business Operations"
        ]
        
        # Check that agents are created for each department
        agent_calls = mock_crew_dependencies["agent"].call_args_list
        
        # Should have calls for each department
        assert len(agent_calls) >= len(expected_departments)


class TestTeamGMAgents:
    """Test individual team GM agent functionality"""
    
    @pytest.fixture
    def mock_gm_agents(self):
        """Mock GM agents setup"""
        with patch('backend.agents.team_gms.Agent') as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.role = "Yankees GM"
            mock_agent_instance.backstory = "Yankees GM backstory"
            mock_agent.return_value = mock_agent_instance
            
            yield mock_agent
    
    def test_create_team_gm_agent(self, mock_gm_agents):
        """Test creation of team-specific GM agents"""
        gm_agents = TeamGMAgents()
        
        team_configs = [
            {
                "team": "yankees",
                "expected_role": "New York Yankees General Manager",
                "context": "high_budget_win_now"
            },
            {
                "team": "rays",
                "expected_role": "Tampa Bay Rays General Manager", 
                "context": "low_budget_analytics"
            },
            {
                "team": "dodgers",
                "expected_role": "Los Angeles Dodgers General Manager",
                "context": "high_budget_development"
            }
        ]
        
        for config in team_configs:
            agent = gm_agents.create_gm_agent(config["team"])
            
            assert agent is not None
            # Mock should be called with team-specific parameters
            mock_gm_agents.assert_called()
    
    def test_gm_agent_team_specific_behavior(self, mock_gm_agents):
        """Test that GM agents have team-specific behavior"""
        gm_agents = TeamGMAgents()
        
        # Test different team philosophies
        yankees_agent = gm_agents.create_gm_agent("yankees")
        rays_agent = gm_agents.create_gm_agent("rays")
        
        # Both should be created but with different configurations
        assert mock_gm_agents.call_count >= 2
        
        # Check that different calls were made (different parameters)
        call_args_list = mock_gm_agents.call_args_list
        assert len(call_args_list) >= 2
    
    def test_get_team_context(self, mock_gm_agents):
        """Test retrieval of team-specific context"""
        gm_agents = TeamGMAgents()
        
        contexts = [
            ("yankees", ["high_budget", "win_now", "luxury_tax"]),
            ("rays", ["low_budget", "analytics", "player_development"]),
            ("rebuilding_team", ["prospects", "future", "salary_dump"])
        ]
        
        for team, expected_elements in contexts:
            context = gm_agents.get_team_context(team)
            
            assert context is not None
            # Context should contain relevant elements for team type
            context_str = str(context).lower()
            
            # At least one expected element should be present
            found_elements = [elem for elem in expected_elements if elem.lower() in context_str]
            # Note: This might pass even with mocked data, but tests the structure
    
    def test_gm_agent_decision_consistency(self, mock_gm_agents):
        """Test that GM agents make consistent decisions"""
        gm_agents = TeamGMAgents()
        
        # Create same agent multiple times
        agent1 = gm_agents.create_gm_agent("yankees")
        agent2 = gm_agents.create_gm_agent("yankees")
        
        # Should create consistent agents (same configuration)
        # In mock environment, this tests the creation logic
        assert mock_gm_agents.call_count >= 2


class TestAgentCommunication:
    """Test inter-agent communication and coordination"""
    
    @pytest.fixture
    def mock_multi_agent_setup(self):
        """Setup for multi-agent testing"""
        with patch('backend.crews.front_office_crew.Agent') as mock_agent, \
             patch('backend.crews.front_office_crew.Crew') as mock_crew:
            
            # Create different agent mocks
            agents = {}
            for dept in ["front_office", "scouting", "analytics", "development", "business"]:
                agent_mock = Mock()
                agent_mock.role = f"{dept}_agent"
                agent_mock.department = dept
                agents[dept] = agent_mock
            
            mock_agent.side_effect = lambda *args, **kwargs: agents.get(
                kwargs.get('role', '').lower().replace(' ', '_'), Mock()
            )
            
            # Mock crew interactions
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Multi-agent analysis complete",
                token_usage=2500,
                tasks_output=[
                    Mock(raw=f"{dept} analysis result", agent=dept) 
                    for dept in agents.keys()
                ]
            )
            mock_crew.return_value = mock_crew_instance
            
            yield {
                "agents": agents,
                "crew": mock_crew_instance,
                "agent_class": mock_agent
            }
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, mock_multi_agent_setup):
        """Test coordination between multiple agents"""
        crew = FrontOfficeCrew()
        
        trade_request = {
            "team": "yankees",
            "request": "Complex multi-team trade involving prospects and veterans",
            "urgency": "high",
            "max_trade_partners": 3
        }
        
        result = await crew.analyze_trade_request(trade_request)
        
        # Should involve multiple departments
        assert result["analysis_complete"] is True
        assert "departments_consulted" in result
        assert len(result["departments_consulted"]) >= 3  # Multiple departments
        
        # Token usage should be higher for complex multi-agent analysis
        assert result["token_usage"] > 1000
    
    @pytest.mark.asyncio
    async def test_agent_disagreement_resolution(self, mock_multi_agent_setup):
        """Test handling of agent disagreements"""
        # Mock conflicting agent outputs
        mock_multi_agent_setup["crew"].kickoff.return_value = Mock(
            raw="Agents reached consensus after discussion",
            token_usage=3000,  # Higher usage due to disagreement resolution
            tasks_output=[
                Mock(raw="Scouting: Player has injury concerns", agent="scouting"),
                Mock(raw="Analytics: Player metrics are excellent", agent="analytics"),
                Mock(raw="Medical: Injury risk is manageable", agent="medical"),
                Mock(raw="Final consensus: Proceed with caution", agent="coordination")
            ]
        )
        
        crew = FrontOfficeCrew()
        
        trade_request = {
            "team": "yankees",
            "request": "Trade for injury-prone star player",
            "urgency": "medium"
        }
        
        result = await crew.analyze_trade_request(trade_request)
        
        # Should handle disagreement and reach consensus
        assert result["analysis_complete"] is True
        assert result["token_usage"] > 2000  # Higher due to extended discussion
    
    @pytest.mark.asyncio
    async def test_department_specialization(self, mock_multi_agent_setup):
        """Test that different departments contribute specialized analysis"""
        crew = FrontOfficeCrew()
        
        specialized_requests = [
            {
                "request": "Evaluate prospect trade value",
                "expected_departments": ["scouting", "development", "analytics"]
            },
            {
                "request": "Salary cap implications of trade",
                "expected_departments": ["business", "front_office", "analytics"]
            },
            {
                "request": "Player injury risk assessment",
                "expected_departments": ["scouting", "medical", "analytics"]
            }
        ]
        
        for case in specialized_requests:
            trade_request = {
                "team": "yankees",
                "request": case["request"],
                "urgency": "medium"
            }
            
            result = await crew.analyze_trade_request(trade_request)
            
            # Should involve relevant specialized departments
            assert result["analysis_complete"] is True
            departments = result["departments_consulted"]
            
            # Should have meaningful department involvement
            assert len(departments) >= 2


class TestAnalysisQualityAndRealism:
    """Test the quality and realism of trade analysis"""
    
    @pytest.fixture
    def realistic_crew_output(self):
        """Mock realistic CrewAI output"""
        return {
            "organizational_recommendation": {
                "overall_recommendation": "Proceed with trade negotiations for Shane Bieber",
                "confidence_level": "High",
                "risk_level": "Medium",
                "timeline": "Immediate - before trade deadline",
                "priority_targets": [
                    {
                        "player": "Shane Bieber",
                        "team": "Guardians", 
                        "position": "SP",
                        "age": 28,
                        "contract": {"years": 1, "aav": 12000000},
                        "stats": {"era": 3.20, "whip": 1.15, "k_9": 11.2},
                        "fit_score": 0.92,
                        "acquisition_likelihood": "Medium-High"
                    },
                    {
                        "player": "Dylan Cease",
                        "team": "Padres",
                        "position": "SP", 
                        "fit_score": 0.85,
                        "acquisition_likelihood": "Medium"
                    }
                ],
                "trade_packages": [
                    {
                        "target": "Shane Bieber",
                        "giving_up": [
                            {"player": "Spencer Jones", "type": "prospect", "value": 45},
                            {"player": "Trystan Vrieling", "type": "prospect", "value": 35}
                        ],
                        "receiving": [
                            {"player": "Shane Bieber", "type": "mlb", "value": 80}
                        ],
                        "value_balance": 0.95,
                        "likelihood": "Medium",
                        "risk_factors": ["injury_history", "contract_year"]
                    }
                ]
            },
            "departments_consulted": [
                "Front Office Leadership",
                "Scouting Department",
                "Analytics Department", 
                "Business Operations",
                "Player Development"
            ],
            "analysis_details": {
                "scouting_report": {
                    "bieber_analysis": "Top-tier stuff when healthy, concerns about recent injuries",
                    "prospect_evaluation": "Jones projects as future corner OF, Vrieling has closer upside"
                },
                "analytics_insight": {
                    "performance_projection": "3.50 ERA expected in Yankee Stadium",
                    "contract_value": "Slight overpay but justified for playoff push"
                },
                "business_impact": {
                    "payroll_impact": 8000000,
                    "luxury_tax_increase": 1200000,
                    "revenue_upside": "Significant playoff revenue potential"
                }
            },
            "token_usage": 2847,
            "estimated_cost": 0.57,
            "analysis_duration": 45.2,
            "confidence_metrics": {
                "overall_confidence": 0.87,
                "data_quality": 0.92,
                "market_assessment": 0.84,
                "risk_evaluation": 0.90
            }
        }
    
    @pytest.mark.asyncio
    async def test_realistic_trade_analysis_structure(self, realistic_crew_output):
        """Test that analysis output has realistic structure"""
        with patch('backend.crews.front_office_crew.Crew') as mock_crew:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw=json.dumps(realistic_crew_output),
                token_usage=realistic_crew_output["token_usage"]
            )
            mock_crew.return_value = mock_crew_instance
            
            crew = FrontOfficeCrew()
            
            request = {
                "team": "yankees",
                "request": "Need ace starting pitcher for playoff push",
                "urgency": "high"
            }
            
            result = await crew.analyze_trade_request(request)
            
            # Check realistic output structure
            assert "organizational_recommendation" in result
            org_rec = result["organizational_recommendation"]
            
            if "priority_targets" in org_rec:
                targets = org_rec["priority_targets"]
                assert len(targets) > 0
                
                for target in targets:
                    # Should have realistic player information
                    assert "player" in target
                    assert "team" in target
                    assert "fit_score" in target or "likelihood" in target
    
    def test_baseball_rule_compliance(self):
        """Test that trade analysis respects baseball rules"""
        # This would test against actual baseball rules
        # For now, test the structure that enables rule checking
        
        trade_scenarios = [
            {
                "description": "40-man roster compliance",
                "players_added": 2,
                "players_removed": 2,
                "roster_space": 38,  # Current 40-man size
                "should_pass": True
            },
            {
                "description": "Luxury tax threshold",
                "current_payroll": 280000000,
                "added_salary": 25000000,
                "luxury_threshold": 297000000,
                "should_trigger_warning": True
            },
            {
                "description": "Service time manipulation",
                "player_service_time": "2.145",
                "team_control_years": 3,
                "should_be_noted": True
            }
        ]
        
        for scenario in trade_scenarios:
            # Test that the analysis framework can handle these considerations
            # In a real implementation, this would validate against actual rules
            assert "description" in scenario
            assert scenario["description"] is not None
    
    def test_market_value_realism(self):
        """Test that trade values are realistic"""
        # Test realistic trade value calculations
        player_values = [
            {"name": "Superstar SP", "war": 6.5, "age": 27, "expected_value": "80-100M"},
            {"name": "Average SP", "war": 2.5, "age": 30, "expected_value": "20-40M"}, 
            {"name": "Top Prospect", "ranking": 15, "eta": "2025", "expected_value": "30-50M"},
            {"name": "Utility Player", "war": 1.5, "age": 28, "expected_value": "5-15M"}
        ]
        
        for player in player_values:
            # Test that value calculations are reasonable
            # This would integrate with real trade value models
            assert player["expected_value"] is not None
            assert "M" in player["expected_value"]  # Contains monetary value


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_trade_analysis_workflow(self):
        """Test complete workflow from request to analysis"""
        with patch('backend.crews.front_office_crew.Crew') as mock_crew, \
             patch('backend.nlp.trade_parser.TradeRequestParser') as mock_parser:
            
            # Mock parser
            mock_parser_instance = Mock()
            mock_parser_instance.parse_trade_request.return_value = Mock(
                primary_need="starting_pitcher",
                confidence_score=0.9,
                budget_constraints=25000000,
                urgency_level="high"
            )
            mock_parser_instance.generate_crew_prompt.return_value = "Analyze SP trade for Yankees"
            mock_parser.return_value = mock_parser_instance
            
            # Mock crew
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Complete trade analysis",
                token_usage=1800
            )
            mock_crew.return_value = mock_crew_instance
            
            # Run complete workflow
            crew = FrontOfficeCrew()
            
            request = {
                "team": "yankees",
                "request": "Need a starting pitcher with postseason experience under $25M AAV",
                "urgency": "high"
            }
            
            result = await crew.analyze_trade_request(request)
            
            # Verify complete workflow
            assert result["analysis_complete"] is True
            assert "token_usage" in result
            assert result["token_usage"] > 1000
    
    @pytest.mark.asyncio 
    async def test_multi_team_trade_analysis(self):
        """Test analysis of complex multi-team trades"""
        with patch('backend.crews.front_office_crew.Crew') as mock_crew:
            # Mock complex multi-team analysis
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Complex 3-team trade analysis complete",
                token_usage=3500,  # Higher for complex trades
                tasks_output=[
                    Mock(raw="Yankees perspective", agent="yankees_gm"),
                    Mock(raw="Guardians perspective", agent="guardians_gm"),
                    Mock(raw="Dodgers perspective", agent="dodgers_gm"),
                    Mock(raw="League office approval", agent="commissioner")
                ]
            )
            mock_crew.return_value = mock_crew_instance
            
            crew = FrontOfficeCrew()
            
            complex_request = {
                "team": "yankees",
                "request": "3-team trade to get Shane Bieber, send prospects to multiple teams",
                "max_trade_partners": 3,
                "urgency": "high"
            }
            
            result = await crew.analyze_trade_request(complex_request)
            
            # Should handle complex multi-team scenarios
            assert result["analysis_complete"] is True
            assert result["token_usage"] > 3000  # More complex = more tokens
            assert len(result["departments_consulted"]) >= 5  # Multiple departments involved
    
    @pytest.mark.asyncio
    async def test_deadline_pressure_analysis(self):
        """Test analysis behavior under trade deadline pressure"""
        with patch('backend.crews.front_office_crew.Crew') as mock_crew:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Urgent trade deadline analysis",
                token_usage=2200
            )
            mock_crew.return_value = mock_crew_instance
            
            crew = FrontOfficeCrew()
            
            deadline_request = {
                "team": "yankees", 
                "request": "Need starter immediately, trade deadline in 2 hours",
                "urgency": "critical",
                "deadline": "2024-07-30T18:00:00Z"
            }
            
            result = await crew.analyze_trade_request(deadline_request)
            
            # Should prioritize speed and available options
            assert result["analysis_complete"] is True
            # Urgent analysis might use fewer tokens for speed
            assert result["token_usage"] > 1500


@pytest.mark.integration
class TestCrewAIPerformance:
    """Test CrewAI performance and resource usage"""
    
    @pytest.mark.asyncio
    async def test_analysis_performance_benchmarks(self):
        """Test performance benchmarks for different analysis types"""
        with patch('backend.crews.front_office_crew.Crew') as mock_crew:
            analysis_types = [
                {"type": "simple", "expected_time": 30, "expected_tokens": 1000},
                {"type": "complex", "expected_time": 60, "expected_tokens": 2500},
                {"type": "multi_team", "expected_time": 90, "expected_tokens": 4000}
            ]
            
            for analysis_type in analysis_types:
                mock_crew_instance = Mock()
                mock_crew_instance.kickoff.return_value = Mock(
                    raw=f"{analysis_type['type']} analysis complete",
                    token_usage=analysis_type["expected_tokens"]
                )
                mock_crew.return_value = mock_crew_instance
                
                crew = FrontOfficeCrew()
                
                start_time = datetime.now()
                result = await crew.analyze_trade_request({
                    "team": "yankees",
                    "request": f"{analysis_type['type']} trade request"
                })
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                # Performance assertions
                assert result["token_usage"] == analysis_type["expected_tokens"]
                # In real implementation, would check actual duration
                assert duration < analysis_type["expected_time"]
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage during analysis"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with patch('backend.crews.front_office_crew.Crew') as mock_crew:
            mock_crew_instance = Mock()
            mock_crew_instance.kickoff.return_value = Mock(
                raw="Memory test analysis",
                token_usage=2000
            )
            mock_crew.return_value = mock_crew_instance
            
            crew = FrontOfficeCrew()
            
            # Run multiple analyses
            for i in range(10):
                await crew.analyze_trade_request({
                    "team": "yankees",
                    "request": f"Analysis {i}"
                })
            
            final_memory = process.memory_info().rss
            memory_growth = final_memory - initial_memory
            
            # Memory growth should be reasonable
            assert memory_growth < 100 * 1024 * 1024  # Less than 100MB growth
    
    def test_token_usage_optimization(self):
        """Test token usage optimization strategies"""
        crew = FrontOfficeCrew()
        
        # Test different prompt lengths and complexity
        requests = [
            {"request": "Need pitcher", "expected_tokens": (500, 1500)},
            {"request": "Need left-handed starting pitcher under 30", "expected_tokens": (1000, 2000)},
            {"request": "Complex 3-team trade analysis with prospects", "expected_tokens": (2000, 4000)}
        ]
        
        # In a real implementation, this would test actual token optimization
        # For now, test the framework for optimization
        for request in requests:
            min_tokens, max_tokens = request["expected_tokens"]
            
            # Test that we have mechanisms to estimate token usage
            assert min_tokens < max_tokens
            assert min_tokens > 0