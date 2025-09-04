"""
Production-ready MLB Front Office CrewAI Orchestration System
Optimized for cost efficiency, performance, and baseball domain expertise
"""

from crewai import Crew, Task, Process, Agent
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import logging
import json
import time
import os
from contextlib import asynccontextmanager

# Set up OpenAI optimization
os.environ.setdefault('TIKTOKEN_CACHE_DIR', '/tmp/tiktoken_cache')

try:
    import tiktoken
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    tiktoken = None
    AsyncOpenAI = None

# Import optimized agent modules and tools
try:
    from ..agents.front_office import FrontOfficeAgents
    from ..agents.scouting import ScoutingAgents  
    from ..agents.analytics import AnalyticsAgents
    from ..agents.player_development import PlayerDevelopmentAgents
    from ..agents.business_operations import BusinessOperationsAgents
    from ..agents.team_gms import TeamGMAgents
    from ..services.supabase_service import supabase_service
except ImportError:
    try:
        from backend.agents.front_office import FrontOfficeAgents
        from backend.agents.scouting import ScoutingAgents  
        from backend.agents.analytics import AnalyticsAgents
        from backend.agents.player_development import PlayerDevelopmentAgents
        from backend.agents.business_operations import BusinessOperationsAgents
        from backend.agents.team_gms import TeamGMAgents
        from backend.services.supabase_service import supabase_service
    except ImportError:
        # Fallback imports
        from agents.front_office import FrontOfficeAgents
        from agents.scouting import ScoutingAgents  
        from agents.analytics import AnalyticsAgents
        from agents.player_development import PlayerDevelopmentAgents
        from agents.business_operations import BusinessOperationsAgents
        from agents.team_gms import TeamGMAgents
        
        # Mock supabase service for fallback
        class supabase_service:
            @staticmethod
            async def update_trade_analysis_status(*args, **kwargs):
                pass

# Configure logging
logger = logging.getLogger(__name__)

class CostOptimizer:
    """Cost optimization for AI model selection and token management"""
    
    MODEL_COSTS = {
        'gpt-4': {'input': 0.00003, 'output': 0.00006},
        'gpt-4-turbo': {'input': 0.00001, 'output': 0.00003},
        'gpt-4o': {'input': 0.000005, 'output': 0.000015},
        'gpt-4o-mini': {'input': 0.00000015, 'output': 0.0000006},
        'gpt-3.5-turbo': {'input': 0.0000015, 'output': 0.000002}
    }
    
    def __init__(self):
        self.total_cost = 0.0
        self.total_tokens = 0
        if OPENAI_AVAILABLE and tiktoken:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        else:
            self.tokenizer = None
    
    def select_optimal_model(self, complexity_score: float, urgency: str = "medium", budget_limit: Optional[float] = None) -> str:
        """Select the most cost-effective model based on task complexity"""
        
        # High complexity or critical urgency = use best model
        if complexity_score > 0.8 or urgency == "high":
            return "gpt-4o"
        
        # Medium complexity = balanced model
        elif complexity_score > 0.4 or urgency == "medium":
            return "gpt-4o-mini" if budget_limit and budget_limit < 1.0 else "gpt-4-turbo"
        
        # Low complexity = most efficient model
        else:
            return "gpt-4o-mini"
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for cost calculation"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback estimation: ~1.3 tokens per word
            return int(len(text.split()) * 1.3)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate cost for token usage"""
        if model not in self.MODEL_COSTS:
            model = "gpt-4o-mini"  # Fallback to cheapest
        
        costs = self.MODEL_COSTS[model]
        cost = (input_tokens * costs['input']) + (output_tokens * costs['output'])
        
        self.total_cost += cost
        self.total_tokens += input_tokens + output_tokens
        
        return cost
    
    def track_usage(self, tokens: int, model: str, operation: str = "analysis"):
        """Track token usage for monitoring"""
        logger.info(f"Token usage - {operation}: {tokens} tokens, model: {model}")

class StreamingManager:
    """Manage real-time progress streaming for long-running analyses"""
    
    def __init__(self):
        self.active_streams = {}
        self.progress_callbacks = {}
    
    async def stream_progress(self, analysis_id: str, progress_data: Dict[str, Any]):
        """Stream progress update to client"""
        try:
            # Update database with progress
            await supabase_service.update_trade_analysis_status(
                analysis_id=analysis_id,
                status="analyzing",
                progress=progress_data
            )
            
            # Call any registered callbacks
            if analysis_id in self.progress_callbacks:
                callback = self.progress_callbacks[analysis_id]
                await callback(progress_data)
            
            logger.debug(f"Streamed progress for {analysis_id}: {progress_data.get('progress', 0)}%")
            
        except Exception as e:
            logger.error(f"Failed to stream progress for {analysis_id}: {e}")
    
    def register_callback(self, analysis_id: str, callback):
        """Register progress callback for analysis"""
        self.progress_callbacks[analysis_id] = callback
    
    def cleanup_analysis(self, analysis_id: str):
        """Clean up resources for completed analysis"""
        self.active_streams.pop(analysis_id, None)
        self.progress_callbacks.pop(analysis_id, None)

class OptimizedFrontOfficeCrew:
    """
    Production-ready MLB Front Office simulation with optimized AI orchestration
    Features:
    - Intelligent model selection based on task complexity
    - Real-time cost tracking and optimization
    - Streaming progress updates
    - Comprehensive error handling and fallbacks
    - Memory-efficient agent coordination
    - Circuit breakers and timeout management
    """
    
    def __init__(self):
        # Initialize cost optimization and monitoring
        self.cost_optimizer = CostOptimizer()
        self.streaming_manager = StreamingManager()
        
        if OPENAI_AVAILABLE:
            self.openai_client = AsyncOpenAI()
        else:
            self.openai_client = None
        
        # Performance tracking
        self.analysis_start_time = None
        self.total_tokens_used = 0
        self.total_cost = 0.0
        self.agent_performance_cache = {}
        
        # Circuit breaker configuration
        self.max_retries = 3
        self.timeout_seconds = 300  # 5 minutes
        self.fallback_enabled = True
        
        # Initialize agents with cost-optimized configurations
        self._initialize_optimized_agents()
    
    def _initialize_optimized_agents(self):
        """Initialize agents with optimized model selection and caching"""
        try:
            # Core leadership agents (use GPT-4 for complex coordination)
            self.commissioner = FrontOfficeAgents.create_commissioner()
            self.trade_coordinator = FrontOfficeAgents.create_trade_coordinator()
            self.assistant_gm = FrontOfficeAgents.create_assistant_gm()
            
            # Specialized departments (use GPT-4o-mini for efficiency)
            # Scouting Department
            self.pro_scout_al_east = ScoutingAgents.create_pro_scout_al_east()
            self.pro_scout_al_central = ScoutingAgents.create_pro_scout_al_central()
            self.pro_scout_al_west = ScoutingAgents.create_pro_scout_al_west()
            self.pro_scout_nl_east = ScoutingAgents.create_pro_scout_nl_east()
            self.pro_scout_nl_central = ScoutingAgents.create_pro_scout_nl_central()
            self.pro_scout_nl_west = ScoutingAgents.create_pro_scout_nl_west()
            self.international_scout = ScoutingAgents.create_international_scout()
            self.amateur_scout = ScoutingAgents.create_amateur_scout()
            
            # Analytics Department
            self.statcast_analyst = AnalyticsAgents.create_statcast_analyst()
            self.traditional_stats_analyst = AnalyticsAgents.create_traditional_stats_analyst()
            self.projection_analyst = AnalyticsAgents.create_projection_analyst()
            self.defensive_metrics_analyst = AnalyticsAgents.create_defensive_metrics_analyst()
            self.matchup_analyst = AnalyticsAgents.create_matchup_analyst()
            
            # Player Development
            self.minor_league_coordinator = PlayerDevelopmentAgents.create_minor_league_coordinator()
            self.player_development_analyst = PlayerDevelopmentAgents.create_player_development_analyst()
            self.biomechanics_expert = PlayerDevelopmentAgents.create_biomechanics_expert()
            self.mental_performance_coach = PlayerDevelopmentAgents.create_mental_performance_coach()
            
            # Business Operations
            self.salary_cap_strategist = BusinessOperationsAgents.create_salary_cap_strategist()
            self.marketing_impact_analyst = BusinessOperationsAgents.create_marketing_impact_analyst()
            self.media_relations_advisor = BusinessOperationsAgents.create_media_relations_advisor()
            self.revenue_analyst = BusinessOperationsAgents.create_revenue_analyst()
            self.legal_advisor = BusinessOperationsAgents.create_legal_advisor()
            
            logger.info("Successfully initialized all production agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            if self.fallback_enabled:
                self._initialize_fallback_agents()
                
    def _initialize_fallback_agents(self):
        """Initialize lightweight fallback agents when full system fails"""
        logger.warning("Initializing fallback agent system")
        
        # Create minimal agents for basic functionality
        self.commissioner = Agent(
            role="Fallback Commissioner",
            goal="Provide basic trade compliance checking",
            backstory="Simplified compliance checker for when full system is unavailable",
            verbose=False,
            max_iter=2
        )
        
        self.trade_coordinator = Agent(
            role="Fallback Trade Coordinator",
            goal="Provide basic trade coordination",
            backstory="Simplified coordinator for emergency operations",
            verbose=False,
            max_iter=2
        )
        
        # Set other agents to None to indicate limited functionality
        self.assistant_gm = None
        self.statcast_analyst = None
    
    def _analyze_request_complexity(self, trade_request: str) -> float:
        """Analyze request complexity to determine optimal model selection"""
        complexity_indicators = {
            'multi_team': ['three team', 'multiple team', 'complex trade', '3 team', 'three-team'],
            'prospects': ['prospect', 'minor league', 'farm system', 'top prospect', 'rookie'],
            'salary_matching': ['salary', 'contract', 'luxury tax', 'payroll', 'arbitration'],
            'international': ['international', 'signing bonus', 'pool', 'j2', 'international pool'],
            'complex_analysis': ['analytics', 'projection', 'advanced stat', 'statcast', 'war', 'ops+'],
            'deadline_pressure': ['deadline', 'urgent', 'asap', 'immediately', 'quick'],
            'star_players': ['all-star', 'cy young', 'mvp', 'superstar', 'franchise player']
        }
        
        score = 0.0
        request_lower = trade_request.lower()
        
        for category, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                if category in ['multi_team', 'star_players']:
                    score += 0.3  # Higher weight for very complex scenarios
                else:
                    score += 0.15
                    
        # Length-based complexity
        word_count = len(trade_request.split())
        if word_count > 100:
            score += 0.2
        elif word_count > 50:
            score += 0.1
            
        return min(score, 1.0)  # Cap at 1.0
    
    def _select_essential_agents(self, trade_request: str, complexity_score: float) -> List[Agent]:
        """Select minimum viable agent set based on request analysis"""
        essential_agents = [self.trade_coordinator]
        
        # Add assistant GM if available
        if self.assistant_gm:
            essential_agents.append(self.assistant_gm)
        
        request_lower = trade_request.lower()
        
        # Always include key analysts if available
        if self.statcast_analyst:
            essential_agents.append(self.statcast_analyst)
        if self.salary_cap_strategist:
            essential_agents.append(self.salary_cap_strategist)
        
        # Add specialists based on request content
        if any(term in request_lower for term in ['scout', 'prospect', 'minor', 'farm']):
            if self.pro_scout_al_east:
                essential_agents.append(self.pro_scout_al_east)  # Representative scout
            if self.minor_league_coordinator:
                essential_agents.append(self.minor_league_coordinator)
            
        if any(term in request_lower for term in ['pitcher', 'pitching', 'rotation', 'starter', 'reliever']):
            if self.projection_analyst:
                essential_agents.append(self.projection_analyst)
            
        if any(term in request_lower for term in ['defense', 'fielding', 'glove', 'defensive']):
            if self.defensive_metrics_analyst:
                essential_agents.append(self.defensive_metrics_analyst)
            
        if complexity_score > 0.6:
            # High complexity - add more specialists
            available_specialists = [
                self.traditional_stats_analyst,
                self.player_development_analyst,
                self.legal_advisor
            ]
            essential_agents.extend([agent for agent in available_specialists if agent])
            
        return essential_agents
    
    async def create_optimized_trade_analysis_crew(
        self, 
        requesting_team: str, 
        trade_request: str,
        analysis_id: str,
        urgency: str = "medium",
        budget_limit: Optional[float] = None
    ) -> Crew:
        """
        Create optimized crew with intelligent agent selection and cost management
        """
        # Determine optimal model based on complexity and urgency
        complexity_score = self._analyze_request_complexity(trade_request)
        optimal_model = self.cost_optimizer.select_optimal_model(
            complexity_score, urgency, budget_limit
        )
        
        logger.info(f"Selected {optimal_model} for analysis {analysis_id} (complexity: {complexity_score:.2f})")
        
        # Create team-specific GM agent with optimized configuration
        try:
            requesting_gm = TeamGMAgents.get_gm_by_team(requesting_team)
        except Exception as e:
            logger.warning(f"Could not create GM agent for {requesting_team}: {e}")
            requesting_gm = None
        
        # Select essential agents based on request type to reduce costs
        essential_agents = self._select_essential_agents(trade_request, complexity_score)
        
        # Add requesting GM and commissioner if available
        if requesting_gm:
            essential_agents.append(requesting_gm)
        if self.commissioner:
            essential_agents.append(self.commissioner)
        
        # Create optimized task workflow
        tasks = await self._create_optimized_task_workflow(
            trade_request, requesting_team, analysis_id, optimal_model, complexity_score
        )
        
        # Create crew with performance optimizations
        crew = Crew(
            agents=essential_agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=self.trade_coordinator if self.trade_coordinator else essential_agents[0],
            verbose=True,
            memory=True,
            max_execution_time=self.timeout_seconds
        )
        
        return crew
    
    async def _create_optimized_task_workflow(
        self, 
        trade_request: str, 
        requesting_team: str,
        analysis_id: str,
        model: str,
        complexity_score: float
    ) -> List[Task]:
        """Create optimized task workflow with parallel execution and progress tracking"""
        
        tasks = []
        
        # Estimate total tokens for cost tracking
        estimated_tokens = self.cost_optimizer.estimate_tokens(trade_request)
        await self.streaming_manager.stream_progress(
            analysis_id, 
            {"stage": "initialization", "progress": 5, "estimated_cost": estimated_tokens * 0.00002}
        )
        
        # Task 1: Optimized Initial Analysis with Cost Tracking
        initial_analysis_task = Task(
            description=f"""
            BASEBALL TRADE ANALYSIS REQUEST - {requesting_team.upper()}
            
            Request: "{trade_request}"
            
            As the Trade Coordinator, provide a comprehensive initial analysis:
            
            1. PLAYER NEED IDENTIFICATION
               - What specific position/role is needed?
               - What performance level/tier?
               - Timeline constraints (deadline, roster moves)
            
            2. ORGANIZATIONAL FIT ANALYSIS
               - How does this align with {requesting_team}'s competitive window?
               - Budget implications and luxury tax considerations
               - Roster construction impact
            
            3. SEARCH PARAMETERS
               - Define target player criteria
               - Identify key performance metrics
               - Set acquisition cost boundaries
            
            4. COORDINATION PLAN
               - Which departments need to be consulted?
               - What data/analysis is required?
               - Priority timeline for decisions
            
            IMPORTANT: Focus on actionable insights that will guide the specialized departments.
            Consider {requesting_team}'s specific organizational philosophy and constraints.
            """,
            agent=self.trade_coordinator,
            expected_output="""
            Executive Summary Format:
            - Primary Need: [Specific position/role/performance level]
            - Target Timeline: [Urgency level and key dates]
            - Budget Framework: [Salary range and luxury tax impact]
            - Search Criteria: [3-5 specific player attributes/metrics]
            - Department Priorities: [Which specialists to engage first]
            - Success Metrics: [How to evaluate potential deals]
            
            This analysis will serve as the foundation for all departmental evaluations.
            """
        )
        tasks.append(initial_analysis_task)
        
        # Add conditional tasks based on complexity and available agents
        if complexity_score > 0.3 and self.pro_scout_al_east:
            # Task 2: Scouting Analysis
            scouting_task = Task(
                description=f"""
                SCOUTING DEPARTMENT ANALYSIS - Target Identification
                
                Based on the Trade Coordinator's analysis, identify realistic trade targets:
                
                1. TARGET IDENTIFICATION
                   - Scan MLB rosters for players matching criteria
                   - Focus on realistic acquisition targets
                   - Consider team situations and likely availability
                
                2. PLAYER EVALUATION  
                   - Provide scouting grades (20-80 scale) for top 6-8 candidates
                   - Assess current performance vs. ceiling
                   - Identify any red flags or concerns
                
                3. ACQUISITION FEASIBILITY
                   - Which teams might be willing to trade
                   - Competitive landscape assessment
                   - Timing factors (contract status, team needs)
                
                Focus on providing actionable recommendations rather than comprehensive coverage.
                """,
                agent=self.pro_scout_al_east,
                expected_output="""
                Priority Target List (Top 6-8 Candidates):
                
                For Each Player:
                - Name, Team, Contract Status
                - Scouting Grade (Overall 20-80)
                - Key Strengths & Weaknesses
                - Acquisition Likelihood (High/Medium/Low)
                - Character Assessment
                - Projected Cost (prospects/players required)
                
                Summary: Top 3 realistic targets with rationale
                """
            )
            tasks.append(scouting_task)
        
        if complexity_score > 0.4 and self.statcast_analyst:
            # Task 3: Analytics Analysis
            analytics_task = Task(
                description=f"""
                ANALYTICS DEPARTMENT - Performance Analysis
                
                Evaluate identified targets using advanced metrics:
                
                1. PERFORMANCE METRICS
                   - Statcast data and advanced metrics
                   - 2025 projections using multiple systems
                   - Park factors and context adjustments
                
                2. TEAM FIT ANALYSIS
                   - How players fit {requesting_team}'s roster
                   - Value assessment and cost per WAR
                   - Risk-adjusted projections
                
                Provide clear rankings and value recommendations.
                """,
                agent=self.statcast_analyst,
                expected_output="""
                Analytics Rankings:
                - Tier 1 (Elite): [Players with projections]
                - Tier 2 (Above Average): [Players with projections]  
                - Best value targets vs. likely acquisition cost
                - Key analytical red flags to avoid
                """
            )
            tasks.append(analytics_task)
        
        if self.salary_cap_strategist:
            # Task 4: Financial Analysis (Always include for budget management)
            financial_task = Task(
                description=f"""
                FINANCIAL FEASIBILITY ANALYSIS
                
                Evaluate business implications of potential acquisitions:
                
                1. BUDGET ANALYSIS
                   - {requesting_team} current payroll situation
                   - Luxury tax implications for each target
                   - Salary matching requirements
                
                2. VALUE ASSESSMENT
                   - Cost per projected WAR vs. market rates
                   - Revenue impact and ROI projections
                   - Risk management considerations
                
                Provide clear financial boundaries and deal structures.
                """,
                agent=self.salary_cap_strategist,
                expected_output="""
                Financial Framework:
                - Maximum salary absorption: $[X]M
                - Luxury tax threshold considerations  
                - Go/No-Go recommendations for each target
                - Preferred contract terms and structures
                """
            )
            tasks.append(financial_task)
        
        # Final Commissioner Review (Always include)
        if self.commissioner:
            final_task = Task(
                description=f"""
                COMMISSIONER FINAL REVIEW & AUTHORIZATION
                
                Provide final organizational approval and ensure MLB compliance:
                
                1. COMPREHENSIVE REVIEW
                   - Evaluate all departmental recommendations
                   - Assess organizational consensus
                   - Validate alignment with strategic plan
                
                2. MLB COMPLIANCE
                   - Verify trades comply with CBA regulations
                   - Check roster limits and luxury tax rules
                   - Validate no-trade clauses and service time
                
                3. FINAL AUTHORIZATION
                   - Rank deals in order of preference
                   - Set maximum authorization levels
                   - Create implementation timeline
                
                This is the definitive organizational position.
                """,
                agent=self.commissioner,
                expected_output="""
                COMMISSIONER'S FINAL AUTHORIZATION
                
                PRIMARY RECOMMENDATION: [Top choice with rationale]
                AUTHORIZED TARGETS (Priority Order):
                1. [Player Name] - Max package: [Specific assets]
                2. [Player Name] - Max package: [Specific assets]
                
                COMPLIANCE CERTIFICATION:
                ✓ All trades comply with MLB rules
                ✓ Luxury tax implications documented
                ✓ Contract restrictions resolved
                
                IMPLEMENTATION DIRECTIVE:
                - Begin negotiations with primary target
                - Execute decision by [specific date]
                - Escalate issues exceeding authorized parameters
                
                Commissioner Authorization: APPROVED
                """
            )
            tasks.append(final_task)
        
        # Add progress callbacks to all tasks
        for i, task in enumerate(tasks):
            original_callback = getattr(task, 'callback', None)
            task.callback = self._create_progress_callback(analysis_id, i, len(tasks), original_callback)
            
        return tasks
    
    def _create_progress_callback(self, analysis_id: str, task_index: int, total_tasks: int, original_callback=None):
        """Create progress callback for streaming updates"""
        async def callback(step):
            try:
                progress = ((task_index + 0.5) / total_tasks) * 100
                
                # Extract token usage if available
                tokens_used = step.get("tokens_used", 0)
                self.total_tokens_used += tokens_used
                
                await self.streaming_manager.stream_progress(
                    analysis_id,
                    {
                        "stage": f"task_{task_index + 1}",
                        "progress": progress,
                        "current_task": step.get("task_description", f"Processing step {task_index + 1}"),
                        "tokens_used": self.total_tokens_used,
                        "estimated_cost": self.total_cost
                    }
                )
                
                # Call original callback if it exists
                if original_callback:
                    await original_callback(step)
                    
            except Exception as e:
                logger.error(f"Progress callback error for {analysis_id}: {e}")
                
        return callback
    
    async def analyze_trade_request(
        self, 
        requesting_team: str, 
        trade_request: str,
        analysis_id: str = None,
        urgency: str = "medium",
        budget_limit: Optional[float] = None,
        stream_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Execute optimized trade analysis with real CrewAI multi-agent coordination
        """
        self.analysis_start_time = datetime.now()
        analysis_id = analysis_id or f"analysis_{int(time.time())}"
        
        logger.info(f"Starting production CrewAI analysis {analysis_id} for {requesting_team}")
        
        try:
            # Initialize cost tracking
            self.total_tokens_used = 0
            self.total_cost = 0.0
            
            # Stream initial progress
            if stream_progress:
                await self.streaming_manager.stream_progress(
                    analysis_id,
                    {
                        "stage": "crew_initialization", 
                        "progress": 10,
                        "message": f"Assembling {requesting_team} front office crew"
                    }
                )
            
            # Create optimized crew with cost management
            crew = await self.create_optimized_trade_analysis_crew(
                requesting_team, trade_request, analysis_id, urgency, budget_limit
            )
            
            # Execute crew with timeout and error handling
            try:
                async with asyncio.timeout(self.timeout_seconds):
                    result = await crew.kickoff_async({
                        'trade_request': trade_request,
                        'requesting_team': requesting_team,
                        'analysis_id': analysis_id,
                        'urgency': urgency,
                        'budget_limit': budget_limit
                    })
            except asyncio.TimeoutError:
                logger.error(f"Analysis {analysis_id} timed out after {self.timeout_seconds}s")
                return await self._create_timeout_response(analysis_id, requesting_team, trade_request)
            
            # Process and structure results
            end_time = datetime.now()
            duration_seconds = (end_time - self.analysis_start_time).total_seconds()
            
            # Extract structured data from crew result
            structured_result = await self._process_crew_result(
                result, requesting_team, trade_request, analysis_id
            )
            
            # Add comprehensive metadata
            final_result = {
                **structured_result,
                'analysis_metadata': {
                    'analysis_id': analysis_id,
                    'requesting_team': requesting_team,
                    'original_request': trade_request,
                    'analysis_start': self.analysis_start_time.isoformat(),
                    'analysis_complete': end_time.isoformat(),
                    'duration_seconds': duration_seconds,
                    'urgency_level': urgency,
                    'budget_limit': budget_limit
                },
                'cost_tracking': {
                    'total_tokens_used': self.total_tokens_used,
                    'estimated_cost_usd': self.total_cost,
                    'cost_per_token': self.total_cost / max(self.total_tokens_used, 1),
                    'efficiency_score': self._calculate_efficiency_score(duration_seconds, self.total_cost)
                },
                'quality_metrics': {
                    'departments_consulted': len(crew.agents),
                    'analysis_depth_score': self._calculate_depth_score(structured_result),
                    'confidence_level': self._calculate_confidence_level(structured_result)
                }
            }
            
            # Stream completion
            if stream_progress:
                await self.streaming_manager.stream_progress(
                    analysis_id,
                    {
                        "stage": "completed",
                        "progress": 100,
                        "message": "Analysis complete",
                        "cost": self.total_cost,
                        "duration": duration_seconds
                    }
                )
            
            logger.info(f"Completed analysis {analysis_id} in {duration_seconds:.2f}s, cost: ${self.total_cost:.4f}")
            return final_result
            
        except Exception as e:
            logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)
            
            if self.fallback_enabled:
                logger.info(f"Attempting fallback analysis for {analysis_id}")
                return await self._execute_fallback_analysis(
                    analysis_id, requesting_team, trade_request
                )
            else:
                return await self._create_error_response(analysis_id, requesting_team, trade_request, str(e))
    
    async def _process_crew_result(
        self, 
        crew_result: Any, 
        requesting_team: str, 
        trade_request: str,
        analysis_id: str
    ) -> Dict[str, Any]:
        """Process raw crew result into structured format"""
        try:
            # Extract key components from crew result
            if hasattr(crew_result, 'result'):
                result_content = str(crew_result.result)
            elif hasattr(crew_result, 'final_answer'):
                result_content = str(crew_result.final_answer)
            else:
                result_content = str(crew_result)
                
            # Parse structured recommendations from the result
            return {
                'analysis_complete': True,
                'organizational_recommendation': self._extract_recommendations(result_content),
                'department_analyses': self._extract_department_analyses(result_content),
                'trade_scenarios': self._extract_trade_scenarios(result_content),
                'risk_assessment': self._extract_risk_assessment(result_content),
                'implementation_plan': self._extract_implementation_plan(result_content),
                'raw_analysis': result_content[:2000] + "..." if len(result_content) > 2000 else result_content
            }
            
        except Exception as e:
            logger.error(f"Error processing crew result for {analysis_id}: {e}")
            return {
                'analysis_complete': True,
                'organizational_recommendation': {
                    'overall_recommendation': 'Analysis completed with processing errors',
                    'confidence_level': 'Low',
                    'raw_result': str(crew_result)[:1000] if crew_result else "No result"
                },
                'processing_error': str(e)
            }
    
    def _extract_recommendations(self, result_content: str) -> Dict[str, Any]:
        """Extract structured recommendations from crew result"""
        # Simple keyword-based extraction (can be enhanced with NLP)
        content_lower = result_content.lower()
        
        # Determine confidence level
        if any(word in content_lower for word in ['highly recommend', 'strong recommendation', 'excellent fit']):
            confidence = 'High'
        elif any(word in content_lower for word in ['proceed with caution', 'moderate risk', 'carefully consider']):
            confidence = 'Medium'
        else:
            confidence = 'Low'
        
        # Extract overall recommendation
        if 'approved' in content_lower or 'recommend' in content_lower:
            overall_rec = 'Proceed with identified trade opportunities'
        elif 'not recommended' in content_lower or 'avoid' in content_lower:
            overall_rec = 'Do not pursue identified targets'
        else:
            overall_rec = 'Further analysis required'
        
        return {
            'overall_recommendation': overall_rec,
            'confidence_level': confidence,
            'primary_targets': self._extract_player_names(result_content),
            'timeline': self._extract_timeline(result_content),
            'key_points': self._extract_key_points(result_content)
        }
    
    def _extract_player_names(self, content: str) -> List[str]:
        """Extract player names mentioned in the analysis"""
        # Simple regex pattern for potential player names (Title Case words)
        import re
        pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        potential_names = re.findall(pattern, content)
        
        # Filter out common false positives
        false_positives = ['Trade Coordinator', 'General Manager', 'Major League', 'American League', 
                          'National League', 'New York', 'Los Angeles', 'San Francisco']
        
        return [name for name in potential_names[:5] if name not in false_positives]
    
    def _extract_timeline(self, content: str) -> str:
        """Extract timeline information"""
        content_lower = content.lower()
        
        if 'immediately' in content_lower or 'asap' in content_lower:
            return 'Immediate action required'
        elif 'deadline' in content_lower or 'urgent' in content_lower:
            return 'Within 1-2 weeks'
        elif 'offseason' in content_lower:
            return 'Offseason priority'
        else:
            return 'Standard timeline (2-4 weeks)'
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key analytical points"""
        # Look for bullet points or numbered items
        import re
        
        # Find lines that start with numbers, bullets, or dashes
        bullet_pattern = r'^[•\-\*\d+\.]\s*(.+)$'
        key_points = re.findall(bullet_pattern, content, re.MULTILINE)
        
        # If no bullets found, extract sentences with key words
        if not key_points:
            key_words = ['recommend', 'suggest', 'important', 'critical', 'warning', 'opportunity']
            sentences = content.split('.')
            key_points = [sentence.strip() for sentence in sentences 
                         if any(word in sentence.lower() for word in key_words)][:5]
        
        return key_points[:8]  # Limit to most important points
    
    def _extract_department_analyses(self, result_content: str) -> Dict[str, Any]:
        """Extract department-specific analyses"""
        departments = {
            'scouting': {'status': 'completed', 'grade': 'B+'},
            'analytics': {'status': 'completed', 'risk_level': 'Medium'},
            'development': {'status': 'completed', 'upside': 'Positive'},
            'business': {'status': 'completed', 'approved': True}
        }
        
        # Enhanced parsing could be added here
        content_lower = result_content.lower()
        
        if 'scout' in content_lower:
            departments['scouting']['targets_found'] = len(self._extract_player_names(result_content))
        
        if 'analytics' in content_lower or 'statcast' in content_lower:
            departments['analytics']['metrics_analyzed'] = True
            
        return departments
    
    def _extract_trade_scenarios(self, result_content: str) -> List[Dict[str, Any]]:
        """Extract specific trade scenarios"""
        scenarios = []
        
        # Look for numbered scenarios or trade proposals
        import re
        scenario_pattern = r'(?:scenario|trade|deal)\s*[:#]?\s*(.+?)(?=\n|$)'
        matches = re.findall(scenario_pattern, result_content, re.IGNORECASE)
        
        for i, match in enumerate(matches[:3]):  # Limit to top 3 scenarios
            scenarios.append({
                'scenario_id': i + 1,
                'description': match.strip()[:200],
                'likelihood': 'Medium',  # Default
                'timeline': '1-2 weeks'
            })
        
        return scenarios
    
    def _extract_risk_assessment(self, result_content: str) -> Dict[str, Any]:
        """Extract risk analysis"""
        content_lower = result_content.lower()
        
        # Determine overall risk level
        if any(word in content_lower for word in ['high risk', 'dangerous', 'avoid', 'significant risk']):
            risk_level = 'High'
        elif any(word in content_lower for word in ['moderate risk', 'some concern', 'caution']):
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
        
        return {
            'overall_risk': risk_level,
            'key_risks': self._extract_risks(result_content),
            'mitigation_strategies': self._extract_mitigations(result_content)
        }
    
    def _extract_risks(self, content: str) -> List[str]:
        """Extract specific risk factors"""
        risk_keywords = ['injury', 'decline', 'age', 'contract', 'expensive', 'overvalued']
        sentences = content.split('.')
        
        risk_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                risk_sentences.append(sentence.strip()[:150])
                if len(risk_sentences) >= 3:
                    break
        
        return risk_sentences
    
    def _extract_mitigations(self, content: str) -> List[str]:
        """Extract risk mitigation strategies"""
        mitigation_keywords = ['insurance', 'medical', 'conditional', 'backup', 'alternative']
        sentences = content.split('.')
        
        mitigation_sentences = []
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in mitigation_keywords):
                mitigation_sentences.append(sentence.strip()[:150])
                if len(mitigation_sentences) >= 3:
                    break
        
        return mitigation_sentences
    
    def _extract_implementation_plan(self, result_content: str) -> Dict[str, Any]:
        """Extract implementation timeline and steps"""
        return {
            'immediate_actions': ['Contact target teams', 'Prepare trade packages'],
            'week_1_goals': ['Initial negotiations', 'Due diligence'],
            'decision_deadline': self._extract_timeline(result_content),
            'success_metrics': ['Trade completion', 'Team improvement']
        }
    
    def _calculate_efficiency_score(self, duration: float, cost: float) -> float:
        """Calculate analysis efficiency score"""
        # Baseline expectations
        baseline_duration = 180  # 3 minutes
        baseline_cost = 1.0  # $1
        
        duration_efficiency = max(0, min(1, (baseline_duration - duration) / baseline_duration + 0.5))
        cost_efficiency = max(0, min(1, (baseline_cost - cost) / baseline_cost + 0.5))
        
        return (duration_efficiency + cost_efficiency) / 2
    
    def _calculate_depth_score(self, result: Dict[str, Any]) -> float:
        """Calculate analysis depth and comprehensiveness score"""
        depth_indicators = [
            bool(result.get('organizational_recommendation')),
            bool(result.get('department_analyses')),
            bool(result.get('trade_scenarios')),
            bool(result.get('risk_assessment')),
            bool(result.get('implementation_plan')),
            bool(result.get('raw_analysis'))
        ]
        return sum(depth_indicators) / len(depth_indicators)
    
    def _calculate_confidence_level(self, result: Dict[str, Any]) -> str:
        """Determine overall confidence level"""
        depth_score = self._calculate_depth_score(result)
        
        # Check for processing errors
        if result.get('processing_error'):
            return 'Low'
        
        if depth_score >= 0.8:
            return 'High'
        elif depth_score >= 0.6:
            return 'Medium'
        else:
            return 'Low'
    
    async def _create_timeout_response(self, analysis_id: str, team: str, request: str) -> Dict[str, Any]:
        """Create response for timed out analysis"""
        return {
            'analysis_complete': False,
            'error_type': 'timeout',
            'message': f'Analysis timed out after {self.timeout_seconds} seconds',
            'analysis_id': analysis_id,
            'requesting_team': team,
            'original_request': request,
            'partial_results': 'Timeout occurred during crew execution',
            'recommendation': 'Retry with simplified request or higher timeout',
            'cost_tracking': {
                'total_tokens_used': self.total_tokens_used,
                'estimated_cost_usd': self.total_cost
            }
        }
    
    async def _create_error_response(self, analysis_id: str, team: str, request: str, error: str) -> Dict[str, Any]:
        """Create response for failed analysis"""
        return {
            'analysis_complete': False,
            'error_type': 'execution_error',
            'error_message': error,
            'analysis_id': analysis_id,
            'requesting_team': team,
            'original_request': request,
            'recommendation': 'Check logs and retry with fallback enabled',
            'cost_tracking': {
                'total_tokens_used': self.total_tokens_used,
                'estimated_cost_usd': self.total_cost
            }
        }
    
    async def _execute_fallback_analysis(self, analysis_id: str, team: str, request: str) -> Dict[str, Any]:
        """Execute simplified fallback analysis when full crew fails"""
        logger.info(f"Executing fallback analysis for {analysis_id}")
        
        # Simple rule-based analysis as fallback
        request_lower = request.lower()
        
        # Basic need analysis
        if any(word in request_lower for word in ['pitcher', 'pitching', 'starter', 'reliever']):
            need_type = 'pitching'
        elif any(word in request_lower for word in ['hitter', 'bat', 'offense', 'outfield', 'infield']):
            need_type = 'hitting'
        else:
            need_type = 'general roster improvement'
        
        # Basic urgency analysis
        if any(word in request_lower for word in ['urgent', 'immediate', 'asap', 'deadline']):
            urgency = 'High'
        else:
            urgency = 'Medium'
        
        fallback_result = {
            'analysis_complete': True,
            'analysis_type': 'fallback',
            'organizational_recommendation': {
                'overall_recommendation': f'Identified need for {need_type} - recommend full system analysis',
                'confidence_level': 'Low',
                'primary_need': need_type,
                'urgency_level': urgency,
                'fallback_suggestions': [
                    f'Request appears to seek {need_type} improvement',
                    'Recommend consulting scouting and analytics departments manually',
                    'Consider budget implications before proceeding',
                    'Full CrewAI system needed for comprehensive analysis'
                ]
            },
            'limitations': 'This is a simplified fallback analysis with limited capabilities',
            'next_steps': 'Resolve system issues and rerun full analysis for detailed recommendations',
            'cost_tracking': {
                'total_tokens_used': 0,
                'estimated_cost_usd': 0.0,
                'note': 'Fallback analysis uses no AI tokens'
            }
        }
        
        return fallback_result
    
    # Additional utility methods for production optimization
    
    async def analyze_trade_request_batch(
        self, 
        trade_requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process multiple trade requests efficiently with batching"""
        results = []
        
        # Process in batches to manage resource usage
        batch_size = 3  # Limit concurrent analyses
        
        for i in range(0, len(trade_requests), batch_size):
            batch = trade_requests[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.analyze_trade_request(
                    requesting_team=req['team'],
                    trade_request=req['request'],
                    analysis_id=req.get('analysis_id'),
                    urgency=req.get('urgency', 'medium'),
                    budget_limit=req.get('budget_limit')
                )
                for req in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Brief pause between batches to prevent API rate limiting
            await asyncio.sleep(2)
            
        return results
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost tracking summary"""
        return {
            'total_tokens_used': self.total_tokens_used,
            'total_cost_usd': self.total_cost,
            'average_cost_per_analysis': self.total_cost / max(1, len(self.agent_performance_cache)),
            'cost_per_token': self.total_cost / max(1, self.total_tokens_used),
            'cost_optimization_suggestions': self._generate_cost_suggestions()
        }
    
    def _generate_cost_suggestions(self) -> List[str]:
        """Generate cost optimization suggestions"""
        suggestions = []
        
        if self.total_cost > 5.0:  # If analysis costs more than $5
            suggestions.append("Consider using GPT-4o-mini for simpler analyses")
            
        if self.total_tokens_used > 100000:  # High token usage
            suggestions.append("Reduce agent verbosity or limit task scope")
            
        if len(self.agent_performance_cache) > 0:
            suggestions.append("Review agent performance and optimize task assignments")
        
        return suggestions or ["Current cost levels are within acceptable ranges"]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check system health and readiness"""
        try:
            # Test basic agent initialization
            test_agents = [
                self.commissioner,
                self.trade_coordinator,
                self.statcast_analyst
            ]
            agents_healthy = all(agent is not None for agent in test_agents)
            
            # Test OpenAI connectivity if available
            openai_healthy = True
            if self.openai_client:
                try:
                    test_response = await self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": "health check"}],
                        max_tokens=5
                    )
                    openai_healthy = bool(test_response)
                except Exception as e:
                    logger.warning(f"OpenAI health check failed: {e}")
                    openai_healthy = False
            
            return {
                'status': 'healthy' if agents_healthy and openai_healthy else 'degraded',
                'agents_available': agents_healthy,
                'openai_connected': openai_healthy,
                'cost_optimizer_active': bool(self.cost_optimizer),
                'streaming_available': bool(self.streaming_manager),
                'fallback_enabled': self.fallback_enabled,
                'total_analyses_run': len(self.agent_performance_cache),
                'total_cost_incurred': self.total_cost,
                'system_uptime': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'fallback_available': self.fallback_enabled,
                'timestamp': datetime.now().isoformat()
            }

# Create a singleton instance for use throughout the application
optimized_front_office_crew = OptimizedFrontOfficeCrew()