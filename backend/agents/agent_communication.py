"""
Agent Communication Protocol Framework

This module defines standardized communication patterns between the 6 specialized 
development agents and the existing CrewAI baseball analysis system.
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
from crewai import Agent, Task

class AgentRole(Enum):
    """Specialized development agent roles"""
    FRONTEND_DEVELOPER = "frontend-developer"
    API_ARCHITECT = "api-architect"
    BACKEND_DEVELOPER = "backend-developer"
    TEST_AUTOMATOR = "test-automator"
    SECURITY_AUDITOR = "security-auditor"
    SENIOR_CODE_REVIEWER = "senior-code-reviewer"

class ReviewType(Enum):
    """Types of reviews agents can perform"""
    CODE_REVIEW = "code_review"
    ARCHITECTURE_REVIEW = "architecture_review"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_REVIEW = "performance_review"
    TEST_COVERAGE = "test_coverage"
    API_DESIGN = "api_design"
    UI_UX_REVIEW = "ui_ux_review"

class ReviewStatus(Enum):
    """Review workflow status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REQUIRES_CHANGES = "requires_changes"
    APPROVED = "approved"
    BLOCKED = "blocked"

@dataclass
class AgentMessage:
    """Standardized message format for agent communication"""
    from_agent: AgentRole
    to_agent: Optional[AgentRole] = None  # None for broadcast
    message_type: str = "info"
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    priority: str = "medium"  # low, medium, high, critical

@dataclass
class ReviewRequest:
    """Structured review request between agents"""
    requesting_agent: AgentRole
    target_agents: List[AgentRole]
    review_type: ReviewType
    artifact_path: str  # File or component being reviewed
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    blocking: bool = False  # Whether this blocks other work

@dataclass
class ReviewResult:
    """Review result from an agent"""
    reviewer_agent: AgentRole
    review_type: ReviewType
    status: ReviewStatus
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    approval_notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

class AgentCommunicationHub:
    """
    Central hub for managing communication between development agents
    and integration with the existing CrewAI baseball system
    """
    
    def __init__(self):
        self.agents: Dict[AgentRole, Dict[str, Any]] = {}
        self.message_history: List[AgentMessage] = []
        self.active_reviews: Dict[str, ReviewRequest] = {}
        self.review_results: Dict[str, List[ReviewResult]] = {}
        self.context_store: Dict[str, Any] = {}
        
    def register_agent(
        self, 
        role: AgentRole, 
        agent_instance: Any,
        capabilities: List[str],
        specializations: List[str]
    ) -> None:
        """Register a development agent with the communication hub"""
        self.agents[role] = {
            'instance': agent_instance,
            'capabilities': capabilities,
            'specializations': specializations,
            'active': True,
            'workload': 0
        }
    
    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Send a message between agents with routing logic"""
        self.message_history.append(message)
        
        # Log the communication
        print(f"[{message.timestamp}] {message.from_agent.value} -> "
              f"{'ALL' if message.to_agent is None else message.to_agent.value}: "
              f"{message.content[:100]}...")
        
        # Handle broadcast messages
        if message.to_agent is None:
            await self._broadcast_message(message)
            return None
        
        # Direct message handling
        return await self._deliver_message(message)
    
    async def initiate_review(self, request: ReviewRequest) -> str:
        """Start a multi-agent review process"""
        review_id = f"{request.review_type.value}_{datetime.now().isoformat()}"
        self.active_reviews[review_id] = request
        self.review_results[review_id] = []
        
        # Notify target agents
        for agent_role in request.target_agents:
            message = AgentMessage(
                from_agent=request.requesting_agent,
                to_agent=agent_role,
                message_type="review_request",
                content=f"Review requested for {request.artifact_path}",
                context={
                    'review_id': review_id,
                    'review_type': request.review_type.value,
                    'artifact_path': request.artifact_path,
                    'description': request.description,
                    'deadline': request.deadline.isoformat() if request.deadline else None,
                    'blocking': request.blocking
                },
                requires_response=True,
                priority="high" if request.blocking else "medium"
            )
            await self.send_message(message)
        
        return review_id
    
    async def submit_review_result(self, review_id: str, result: ReviewResult) -> None:
        """Submit a review result and check if review is complete"""
        if review_id not in self.review_results:
            self.review_results[review_id] = []
        
        self.review_results[review_id].append(result)
        
        # Check if all reviewers have responded
        if self._is_review_complete(review_id):
            await self._finalize_review(review_id)
    
    def get_agent_workload(self, agent_role: AgentRole) -> int:
        """Get current workload for load balancing"""
        return self.agents.get(agent_role, {}).get('workload', 0)
    
    def update_shared_context(self, key: str, value: Any) -> None:
        """Update shared context available to all agents"""
        self.context_store[key] = {
            'value': value,
            'updated_at': datetime.now(),
            'version': self.context_store.get(key, {}).get('version', 0) + 1
        }
    
    def get_shared_context(self, key: str) -> Any:
        """Retrieve shared context"""
        return self.context_store.get(key, {}).get('value')
    
    async def coordinate_parallel_reviews(
        self, 
        artifact_paths: List[str],
        review_types: List[ReviewType],
        requesting_agent: AgentRole
    ) -> Dict[str, str]:
        """Coordinate multiple parallel reviews"""
        review_ids = {}
        
        # Distribute reviews based on agent specialization and workload
        for path in artifact_paths:
            for review_type in review_types:
                target_agents = self._select_optimal_reviewers(review_type, path)
                
                request = ReviewRequest(
                    requesting_agent=requesting_agent,
                    target_agents=target_agents,
                    review_type=review_type,
                    artifact_path=path,
                    description=f"Parallel review of {path} for {review_type.value}"
                )
                
                review_id = await self.initiate_review(request)
                review_ids[f"{path}_{review_type.value}"] = review_id
        
        return review_ids
    
    async def escalate_to_senior_reviewer(
        self, 
        review_id: str, 
        conflict_details: str
    ) -> None:
        """Escalate conflicting reviews to senior code reviewer"""
        message = AgentMessage(
            from_agent=AgentRole.SENIOR_CODE_REVIEWER,  # System escalation
            to_agent=AgentRole.SENIOR_CODE_REVIEWER,
            message_type="escalation",
            content=f"Review conflict requires senior review: {conflict_details}",
            context={
                'review_id': review_id,
                'conflict_details': conflict_details,
                'original_results': self.review_results.get(review_id, [])
            },
            requires_response=True,
            priority="critical"
        )
        
        await self.send_message(message)
    
    # Private methods
    
    async def _broadcast_message(self, message: AgentMessage) -> None:
        """Send message to all active agents"""
        for agent_role in self.agents.keys():
            if self.agents[agent_role]['active']:
                directed_message = AgentMessage(
                    from_agent=message.from_agent,
                    to_agent=agent_role,
                    message_type=message.message_type,
                    content=message.content,
                    context=message.context,
                    requires_response=message.requires_response,
                    priority=message.priority
                )
                await self._deliver_message(directed_message)
    
    async def _deliver_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Deliver message to specific agent and handle response"""
        target_agent_info = self.agents.get(message.to_agent)
        if not target_agent_info or not target_agent_info['active']:
            print(f"Agent {message.to_agent.value} not available")
            return None
        
        # Update workload
        target_agent_info['workload'] += 1
        
        # Simulate agent processing (in real implementation, this would call the actual agent)
        # For now, we'll return a mock response if required
        if message.requires_response:
            response = AgentMessage(
                from_agent=message.to_agent,
                to_agent=message.from_agent,
                message_type="response",
                content=f"Acknowledged: {message.content[:50]}...",
                context={'original_message_id': id(message)},
                priority=message.priority
            )
            return response
        
        return None
    
    def _select_optimal_reviewers(
        self, 
        review_type: ReviewType, 
        artifact_path: str
    ) -> List[AgentRole]:
        """Select the best agents for a specific review type and artifact"""
        
        # Define agent specialization mapping
        review_agent_mapping = {
            ReviewType.CODE_REVIEW: [AgentRole.SENIOR_CODE_REVIEWER, AgentRole.BACKEND_DEVELOPER],
            ReviewType.ARCHITECTURE_REVIEW: [AgentRole.SENIOR_CODE_REVIEWER, AgentRole.API_ARCHITECT],
            ReviewType.SECURITY_AUDIT: [AgentRole.SECURITY_AUDITOR],
            ReviewType.PERFORMANCE_REVIEW: [AgentRole.API_ARCHITECT, AgentRole.BACKEND_DEVELOPER],
            ReviewType.TEST_COVERAGE: [AgentRole.TEST_AUTOMATOR],
            ReviewType.API_DESIGN: [AgentRole.API_ARCHITECT, AgentRole.BACKEND_DEVELOPER],
            ReviewType.UI_UX_REVIEW: [AgentRole.FRONTEND_DEVELOPER]
        }
        
        # Get potential reviewers
        potential_reviewers = review_agent_mapping.get(review_type, [AgentRole.SENIOR_CODE_REVIEWER])
        
        # Filter by artifact type
        if 'frontend/' in artifact_path or artifact_path.endswith(('.tsx', '.jsx', '.css', '.scss')):
            if AgentRole.FRONTEND_DEVELOPER in potential_reviewers:
                potential_reviewers = [AgentRole.FRONTEND_DEVELOPER] + [
                    r for r in potential_reviewers if r != AgentRole.FRONTEND_DEVELOPER
                ]
        
        # Sort by current workload and return top picks
        available_reviewers = [
            agent for agent in potential_reviewers 
            if agent in self.agents and self.agents[agent]['active']
        ]
        
        return sorted(available_reviewers, key=lambda a: self.get_agent_workload(a))[:2]
    
    def _is_review_complete(self, review_id: str) -> bool:
        """Check if all required reviewers have submitted results"""
        request = self.active_reviews.get(review_id)
        results = self.review_results.get(review_id, [])
        
        if not request:
            return False
        
        submitted_agents = {result.reviewer_agent for result in results}
        required_agents = set(request.target_agents)
        
        return required_agents.issubset(submitted_agents)
    
    async def _finalize_review(self, review_id: str) -> None:
        """Finalize a review and notify the requesting agent"""
        request = self.active_reviews[review_id]
        results = self.review_results[review_id]
        
        # Analyze results for conflicts
        approvals = [r for r in results if r.status == ReviewStatus.APPROVED]
        rejections = [r for r in results if r.status == ReviewStatus.REQUIRES_CHANGES]
        blocking_issues = [issue for r in results for issue in r.blocking_issues]
        
        # Determine final status
        if blocking_issues:
            final_status = "blocked"
        elif rejections:
            final_status = "requires_changes"
        elif len(approvals) == len(results):
            final_status = "approved"
        else:
            final_status = "mixed_results"
        
        # Send completion notification
        message = AgentMessage(
            from_agent=AgentRole.SENIOR_CODE_REVIEWER,  # System notification
            to_agent=request.requesting_agent,
            message_type="review_complete",
            content=f"Review complete for {request.artifact_path}: {final_status}",
            context={
                'review_id': review_id,
                'final_status': final_status,
                'total_reviewers': len(results),
                'approvals': len(approvals),
                'rejections': len(rejections),
                'blocking_issues': blocking_issues,
                'results': [
                    {
                        'agent': r.reviewer_agent.value,
                        'status': r.status.value,
                        'findings': r.findings,
                        'recommendations': r.recommendations
                    }
                    for r in results
                ]
            }
        )
        
        await self.send_message(message)
        
        # Clean up completed review
        if review_id in self.active_reviews:
            del self.active_reviews[review_id]

# Global communication hub instance
communication_hub = AgentCommunicationHub()

# Convenience functions for common operations
async def request_code_review(
    artifact_path: str, 
    requesting_agent: AgentRole,
    description: str = "",
    blocking: bool = False
) -> str:
    """Quick function to request a code review"""
    request = ReviewRequest(
        requesting_agent=requesting_agent,
        target_agents=[AgentRole.SENIOR_CODE_REVIEWER],
        review_type=ReviewType.CODE_REVIEW,
        artifact_path=artifact_path,
        description=description or f"Code review requested for {artifact_path}",
        blocking=blocking
    )
    return await communication_hub.initiate_review(request)

async def request_security_audit(
    artifact_path: str,
    requesting_agent: AgentRole,
    description: str = "",
    blocking: bool = True
) -> str:
    """Quick function to request a security audit"""
    request = ReviewRequest(
        requesting_agent=requesting_agent,
        target_agents=[AgentRole.SECURITY_AUDITOR],
        review_type=ReviewType.SECURITY_AUDIT,
        artifact_path=artifact_path,
        description=description or f"Security audit requested for {artifact_path}",
        blocking=blocking
    )
    return await communication_hub.initiate_review(request)

async def request_full_stack_review(
    frontend_path: str,
    backend_path: str,
    requesting_agent: AgentRole,
    description: str = ""
) -> Dict[str, str]:
    """Request comprehensive full-stack review"""
    return await communication_hub.coordinate_parallel_reviews(
        artifact_paths=[frontend_path, backend_path],
        review_types=[
            ReviewType.CODE_REVIEW,
            ReviewType.ARCHITECTURE_REVIEW,
            ReviewType.SECURITY_AUDIT,
            ReviewType.PERFORMANCE_REVIEW
        ],
        requesting_agent=requesting_agent
    )