"""
Cost Optimization Tool for AI Model Selection and Token Management
Intelligent model selection based on task complexity and budget constraints
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model performance tiers"""
    PREMIUM = "premium"      # GPT-4, Claude-3 Opus
    ADVANCED = "advanced"    # GPT-4-turbo, Claude-3 Sonnet  
    STANDARD = "standard"    # GPT-4o, Claude-3 Haiku
    EFFICIENT = "efficient"  # GPT-4o-mini, GPT-3.5-turbo
    LEGACY = "legacy"        # Older models for fallback

@dataclass
class ModelConfig:
    """Configuration for each AI model"""
    name: str
    tier: ModelTier
    input_cost_per_1k: float    # Cost per 1K input tokens
    output_cost_per_1k: float   # Cost per 1K output tokens
    context_window: int         # Maximum context window
    speed_score: float         # Relative speed (1.0 = baseline)
    quality_score: float       # Relative quality (1.0 = baseline)
    specializations: List[str] = field(default_factory=list)
    max_concurrent: int = 10   # Max concurrent requests

@dataclass
class UsageRecord:
    """Record of model usage for cost tracking"""
    model: str
    timestamp: datetime
    input_tokens: int
    output_tokens: int
    cost: float
    task_type: str
    duration_seconds: float
    success: bool

class CostOptimizer:
    """
    Intelligent cost optimization for AI model selection and usage tracking
    
    Features:
    - Dynamic model selection based on task complexity
    - Real-time cost tracking and budgeting
    - Performance-based model recommendations
    - Token usage estimation and optimization
    - Circuit breaker for cost overruns
    """
    
    def __init__(self, daily_budget_limit: float = 100.0, emergency_budget: float = 20.0):
        self.daily_budget_limit = daily_budget_limit
        self.emergency_budget = emergency_budget
        
        # Initialize model configurations
        self.models = self._initialize_model_configs()
        
        # Usage tracking
        self.usage_history: List[UsageRecord] = []
        self.daily_usage = 0.0
        self.current_day = datetime.now().date()
        
        # Performance tracking
        self.model_performance: Dict[str, Dict[str, float]] = {}
        
        # Initialize tokenizer
        if TIKTOKEN_AVAILABLE:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        else:
            self.tokenizer = None
            logger.warning("tiktoken not available - using estimation fallback")
        
        logger.info(f"CostOptimizer initialized with daily budget: ${daily_budget_limit}")
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations with current pricing"""
        return {
            'gpt-4': ModelConfig(
                name='gpt-4',
                tier=ModelTier.PREMIUM,
                input_cost_per_1k=0.03,
                output_cost_per_1k=0.06,
                context_window=8192,
                speed_score=0.6,
                quality_score=1.0,
                specializations=['complex_reasoning', 'detailed_analysis']
            ),
            'gpt-4-turbo': ModelConfig(
                name='gpt-4-turbo',
                tier=ModelTier.ADVANCED,
                input_cost_per_1k=0.01,
                output_cost_per_1k=0.03,
                context_window=128000,
                speed_score=0.8,
                quality_score=0.95,
                specializations=['long_context', 'comprehensive_analysis']
            ),
            'gpt-4o': ModelConfig(
                name='gpt-4o',
                tier=ModelTier.STANDARD,
                input_cost_per_1k=0.005,
                output_cost_per_1k=0.015,
                context_window=128000,
                speed_score=1.0,
                quality_score=0.9,
                specializations=['balanced_performance', 'general_analysis']
            ),
            'gpt-4o-mini': ModelConfig(
                name='gpt-4o-mini',
                tier=ModelTier.EFFICIENT,
                input_cost_per_1k=0.00015,
                output_cost_per_1k=0.0006,
                context_window=128000,
                speed_score=1.2,
                quality_score=0.8,
                specializations=['efficient_processing', 'simple_tasks']
            ),
            'gpt-3.5-turbo': ModelConfig(
                name='gpt-3.5-turbo',
                tier=ModelTier.LEGACY,
                input_cost_per_1k=0.0015,
                output_cost_per_1k=0.002,
                context_window=4096,
                speed_score=1.4,
                quality_score=0.7,
                specializations=['legacy_fallback', 'basic_tasks']
            )
        }
    
    def select_optimal_model(
        self,
        task_complexity: float,
        urgency: str = "medium",
        budget_constraint: Optional[float] = None,
        context_length: int = 4000,
        task_type: str = "general",
        quality_requirement: float = 0.8
    ) -> str:
        """
        Select the most cost-effective model for the given requirements
        
        Args:
            task_complexity: Score 0.0-1.0 indicating task difficulty
            urgency: "low", "medium", "high", "critical"
            budget_constraint: Maximum cost allowed for this task
            context_length: Required context window size
            task_type: Type of task for specialization matching
            quality_requirement: Minimum quality score required
            
        Returns:
            Selected model name
        """
        
        # Check daily budget first
        if self._is_budget_exceeded():
            logger.warning("Daily budget exceeded - selecting most efficient model")
            return self._get_most_efficient_model(context_length)
        
        # Filter models by requirements
        suitable_models = self._filter_suitable_models(
            context_length, quality_requirement, task_type
        )
        
        if not suitable_models:
            logger.warning("No suitable models found - using fallback")
            return 'gpt-4o-mini'
        
        # Score models based on multiple factors
        scored_models = []
        for model_name in suitable_models:
            model = self.models[model_name]
            score = self._calculate_model_score(
                model, task_complexity, urgency, budget_constraint
            )
            scored_models.append((model_name, score))
        
        # Sort by score (higher is better)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        selected_model = scored_models[0][0]
        
        logger.info(f"Selected model: {selected_model} (score: {scored_models[0][1]:.3f})")
        return selected_model
    
    def _filter_suitable_models(
        self, 
        context_length: int, 
        quality_requirement: float,
        task_type: str
    ) -> List[str]:
        """Filter models that meet basic requirements"""
        suitable = []
        
        for name, model in self.models.items():
            # Check context window
            if model.context_window < context_length:
                continue
            
            # Check quality requirement
            if model.quality_score < quality_requirement:
                continue
            
            # Check specialization match
            if task_type in model.specializations:
                suitable.insert(0, name)  # Prioritize specialized models
            else:
                suitable.append(name)
        
        return suitable
    
    def _calculate_model_score(
        self,
        model: ModelConfig,
        task_complexity: float,
        urgency: str,
        budget_constraint: Optional[float]
    ) -> float:
        """Calculate overall score for model selection"""
        
        # Base scores
        quality_score = model.quality_score
        speed_score = model.speed_score
        cost_efficiency = 1.0 / (model.input_cost_per_1k + model.output_cost_per_1k)
        
        # Adjust weights based on task complexity
        if task_complexity > 0.8:
            # High complexity - prioritize quality
            quality_weight = 0.6
            speed_weight = 0.2
            cost_weight = 0.2
        elif task_complexity > 0.4:
            # Medium complexity - balanced
            quality_weight = 0.4
            speed_weight = 0.3
            cost_weight = 0.3
        else:
            # Low complexity - prioritize efficiency
            quality_weight = 0.2
            speed_weight = 0.3
            cost_weight = 0.5
        
        # Adjust for urgency
        urgency_multipliers = {
            'low': {'speed': 0.5, 'cost': 1.5},
            'medium': {'speed': 1.0, 'cost': 1.0},
            'high': {'speed': 1.5, 'cost': 0.7},
            'critical': {'speed': 2.0, 'cost': 0.5}
        }
        
        multiplier = urgency_multipliers.get(urgency, urgency_multipliers['medium'])
        speed_score *= multiplier['speed']
        cost_efficiency *= multiplier['cost']
        
        # Apply budget constraint penalty
        budget_penalty = 1.0
        if budget_constraint:
            estimated_cost = self.estimate_cost(
                4000, 2000, model.name  # Rough estimation
            )
            if estimated_cost > budget_constraint:
                budget_penalty = 0.1  # Heavy penalty for exceeding budget
        
        # Calculate final score
        final_score = (
            quality_score * quality_weight +
            speed_score * speed_weight +
            cost_efficiency * cost_weight
        ) * budget_penalty
        
        return final_score
    
    def estimate_tokens(self, text: str, include_output: bool = True) -> Tuple[int, int]:
        """
        Estimate input and output tokens for cost calculation
        
        Args:
            text: Input text to analyze
            include_output: Whether to estimate output tokens
            
        Returns:
            Tuple of (input_tokens, estimated_output_tokens)
        """
        if self.tokenizer:
            input_tokens = len(self.tokenizer.encode(text))
        else:
            # Fallback estimation: ~1.3 tokens per word
            input_tokens = int(len(text.split()) * 1.3)
        
        if include_output:
            # Estimate output tokens based on task type and input length
            # Baseball analysis typically generates substantial output
            output_tokens = int(input_tokens * 0.8)  # 80% of input length
        else:
            output_tokens = 0
        
        return input_tokens, output_tokens
    
    def estimate_cost(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        model_name: str
    ) -> float:
        """Calculate estimated cost for token usage"""
        if model_name not in self.models:
            logger.warning(f"Unknown model {model_name}, using gpt-4o-mini pricing")
            model_name = 'gpt-4o-mini'
        
        model = self.models[model_name]
        
        input_cost = (input_tokens / 1000) * model.input_cost_per_1k
        output_cost = (output_tokens / 1000) * model.output_cost_per_1k
        
        return input_cost + output_cost
    
    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str,
        duration_seconds: float,
        success: bool = True
    ) -> float:
        """
        Track model usage and calculate cost
        
        Returns:
            Cost of the operation
        """
        cost = self.estimate_cost(input_tokens, output_tokens, model)
        
        # Record usage
        record = UsageRecord(
            model=model,
            timestamp=datetime.now(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            task_type=task_type,
            duration_seconds=duration_seconds,
            success=success
        )
        
        self.usage_history.append(record)
        
        # Update daily usage
        today = datetime.now().date()
        if today != self.current_day:
            self.daily_usage = 0.0
            self.current_day = today
        
        self.daily_usage += cost
        
        # Update performance tracking
        self._update_model_performance(model, cost, duration_seconds, success)
        
        logger.info(f"Usage tracked: {model} - ${cost:.4f} ({input_tokens}+{output_tokens} tokens)")
        
        return cost
    
    def _update_model_performance(
        self, 
        model: str, 
        cost: float, 
        duration: float, 
        success: bool
    ):
        """Update model performance metrics"""
        if model not in self.model_performance:
            self.model_performance[model] = {
                'avg_cost': 0.0,
                'avg_duration': 0.0,
                'success_rate': 1.0,
                'total_uses': 0
            }
        
        perf = self.model_performance[model]
        total_uses = perf['total_uses']
        
        # Update running averages
        perf['avg_cost'] = (perf['avg_cost'] * total_uses + cost) / (total_uses + 1)
        perf['avg_duration'] = (perf['avg_duration'] * total_uses + duration) / (total_uses + 1)
        perf['success_rate'] = (perf['success_rate'] * total_uses + (1.0 if success else 0.0)) / (total_uses + 1)
        perf['total_uses'] += 1
    
    def _is_budget_exceeded(self) -> bool:
        """Check if daily budget has been exceeded"""
        return self.daily_usage >= self.daily_budget_limit
    
    def _get_most_efficient_model(self, context_length: int = 4000) -> str:
        """Get the most cost-efficient model that meets requirements"""
        suitable_models = []
        
        for name, model in self.models.items():
            if model.context_window >= context_length:
                cost_per_token = model.input_cost_per_1k + model.output_cost_per_1k
                suitable_models.append((name, cost_per_token))
        
        if not suitable_models:
            return 'gpt-3.5-turbo'  # Fallback
        
        # Return cheapest model
        suitable_models.sort(key=lambda x: x[1])
        return suitable_models[0][0]
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for the specified time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_usage = [r for r in self.usage_history if r.timestamp >= cutoff]
        
        if not recent_usage:
            return {
                'total_cost': 0.0,
                'total_requests': 0,
                'models_used': [],
                'success_rate': 1.0
            }
        
        total_cost = sum(r.cost for r in recent_usage)
        total_requests = len(recent_usage)
        successful_requests = sum(1 for r in recent_usage if r.success)
        success_rate = successful_requests / total_requests
        
        # Model breakdown
        model_stats = {}
        for record in recent_usage:
            if record.model not in model_stats:
                model_stats[record.model] = {'cost': 0.0, 'requests': 0, 'tokens': 0}
            
            model_stats[record.model]['cost'] += record.cost
            model_stats[record.model]['requests'] += 1
            model_stats[record.model]['tokens'] += record.input_tokens + record.output_tokens
        
        return {
            'period_hours': hours,
            'total_cost': total_cost,
            'total_requests': total_requests,
            'success_rate': success_rate,
            'daily_budget_used': (self.daily_usage / self.daily_budget_limit) * 100,
            'models_used': list(model_stats.keys()),
            'model_breakdown': model_stats,
            'cost_per_request': total_cost / max(total_requests, 1),
            'budget_remaining': max(0, self.daily_budget_limit - self.daily_usage)
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Budget analysis
        budget_usage_pct = (self.daily_usage / self.daily_budget_limit) * 100
        if budget_usage_pct > 80:
            recommendations.append(f"High budget usage ({budget_usage_pct:.1f}%) - consider using more efficient models")
        
        # Model performance analysis
        if self.model_performance:
            # Find least efficient model
            least_efficient = max(
                self.model_performance.items(),
                key=lambda x: x[1]['avg_cost']
            )
            
            if least_efficient[1]['avg_cost'] > 0.1:  # More than 10 cents per use
                recommendations.append(f"Model {least_efficient[0]} is expensive (${least_efficient[1]['avg_cost']:.3f}/use) - consider alternatives")
        
        # Success rate analysis
        recent_records = self.usage_history[-50:] if len(self.usage_history) >= 50 else self.usage_history
        if recent_records:
            success_rate = sum(1 for r in recent_records if r.success) / len(recent_records)
            if success_rate < 0.9:
                recommendations.append(f"Low success rate ({success_rate:.1%}) - review error handling and model selection")
        
        # Token efficiency
        if recent_records:
            avg_tokens = sum(r.input_tokens + r.output_tokens for r in recent_records) / len(recent_records)
            if avg_tokens > 10000:
                recommendations.append("High token usage detected - consider prompt optimization or task splitting")
        
        return recommendations or ["Current usage patterns are efficient"]
    
    def create_budget_alert(self, threshold_pct: float = 80) -> Optional[Dict[str, Any]]:
        """Create budget alert if threshold is exceeded"""
        usage_pct = (self.daily_usage / self.daily_budget_limit) * 100
        
        if usage_pct >= threshold_pct:
            return {
                'alert_type': 'budget_threshold',
                'severity': 'high' if usage_pct >= 90 else 'medium',
                'current_usage': self.daily_usage,
                'budget_limit': self.daily_budget_limit,
                'usage_percentage': usage_pct,
                'remaining_budget': self.daily_budget_limit - self.daily_usage,
                'recommendations': [
                    'Switch to more efficient models',
                    'Reduce analysis scope',
                    'Defer non-critical tasks'
                ],
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    async def optimize_concurrent_usage(self, requested_analyses: int) -> Dict[str, Any]:
        """Optimize resource usage for concurrent analyses"""
        
        # Calculate optimal batch size based on current budget
        remaining_budget = self.daily_budget_limit - self.daily_usage
        
        # Estimate cost per analysis (conservative estimate)
        est_cost_per_analysis = 0.5  # $0.50 per analysis
        
        # Calculate safe concurrent limit
        safe_concurrent = min(
            requested_analyses,
            int(remaining_budget / est_cost_per_analysis),
            10  # Hard limit for API rate limiting
        )
        
        # Suggest batching strategy
        if requested_analyses > safe_concurrent:
            num_batches = (requested_analyses + safe_concurrent - 1) // safe_concurrent
            batch_delay = 30  # 30 seconds between batches
        else:
            num_batches = 1
            batch_delay = 0
        
        return {
            'requested_analyses': requested_analyses,
            'safe_concurrent_limit': safe_concurrent,
            'recommended_batches': num_batches,
            'batch_delay_seconds': batch_delay,
            'estimated_total_cost': requested_analyses * est_cost_per_analysis,
            'budget_sufficient': remaining_budget >= (requested_analyses * est_cost_per_analysis),
            'recommendations': [
                f'Process in {num_batches} batch(es) of {safe_concurrent} analyses',
                f'Wait {batch_delay} seconds between batches',
                'Monitor cost accumulation during processing'
            ]
        }
    
    def export_usage_data(self, format: str = "json") -> str:
        """Export usage data for analysis"""
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'daily_budget_limit': self.daily_budget_limit,
            'current_daily_usage': self.daily_usage,
            'model_configurations': {
                name: {
                    'tier': config.tier.value,
                    'input_cost_per_1k': config.input_cost_per_1k,
                    'output_cost_per_1k': config.output_cost_per_1k,
                    'context_window': config.context_window,
                    'specializations': config.specializations
                }
                for name, config in self.models.items()
            },
            'usage_history': [
                {
                    'model': r.model,
                    'timestamp': r.timestamp.isoformat(),
                    'input_tokens': r.input_tokens,
                    'output_tokens': r.output_tokens,
                    'cost': r.cost,
                    'task_type': r.task_type,
                    'duration_seconds': r.duration_seconds,
                    'success': r.success
                }
                for r in self.usage_history[-100:]  # Last 100 records
            ],
            'model_performance': self.model_performance
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        else:
            return str(data)

# Global instance for use throughout the application
cost_optimizer = CostOptimizer()