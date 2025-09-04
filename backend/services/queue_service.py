"""
Queue Service for Baseball Trade AI
Manages background task queuing and processing for trade analysis
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class QueueTask:
    """Individual queue task"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class QueueService:
    """
    In-memory queue service with Redis fallback option
    Handles background task processing with priority and retry logic
    """
    
    def __init__(self):
        self.tasks: Dict[str, QueueTask] = {}
        self.pending_queues: Dict[TaskPriority, List[str]] = {
            priority: [] for priority in TaskPriority
        }
        self.processing_tasks: Dict[str, QueueTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self._worker_active = False
        self._max_concurrent_tasks = 5
        self._shutdown_event = asyncio.Event()
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default task handlers"""
        self.task_handlers = {
            'trade_analysis': self._handle_trade_analysis,
            'data_refresh': self._handle_data_refresh,
            'cache_warming': self._handle_cache_warming,
            'cleanup': self._handle_cleanup
        }
    
    async def enqueue_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3
    ) -> str:
        """Enqueue a new task for background processing"""
        task_id = str(uuid.uuid4())
        
        task = QueueTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            payload=payload,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        self.pending_queues[priority].append(task_id)
        
        logger.info(f"Enqueued task {task_id} ({task_type}) with priority {priority.value}")
        
        # Start worker if not already active
        if not self._worker_active:
            asyncio.create_task(self._start_worker())
        
        return task_id
    
    async def enqueue_analysis(
        self,
        analysis_id: str,
        team_data: Dict,
        request_data: Dict,
        parsed_request: Dict
    ) -> str:
        """Convenience method for enqueueing trade analysis"""
        payload = {
            'analysis_id': analysis_id,
            'team_data': team_data,
            'request_data': request_data,
            'parsed_request': parsed_request
        }
        
        # Determine priority based on urgency
        urgency = request_data.get('urgency', 'medium')
        priority_map = {
            'low': TaskPriority.LOW,
            'medium': TaskPriority.MEDIUM,
            'high': TaskPriority.HIGH
        }
        priority = priority_map.get(urgency, TaskPriority.MEDIUM)
        
        return await self.enqueue_task(
            task_type='trade_analysis',
            payload=payload,
            priority=priority,
            max_retries=2  # Lower retries for analysis tasks
        )
    
    async def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get status of a specific task"""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.PENDING:
            # Remove from pending queue
            for priority_queue in self.pending_queues.values():
                if task_id in priority_queue:
                    priority_queue.remove(task_id)
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False  # Can't cancel processing/completed tasks
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            'total_tasks': len(self.tasks),
            'pending_by_priority': {
                priority.value: len(queue) 
                for priority, queue in self.pending_queues.items()
            },
            'processing_count': len(self.processing_tasks),
            'worker_active': self._worker_active,
            'status_breakdown': {}
        }
        
        # Count tasks by status
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        stats['status_breakdown'] = status_counts
        
        return stats
    
    async def _start_worker(self):
        """Start the background worker"""
        if self._worker_active:
            return
        
        self._worker_active = True
        logger.info("Queue worker started")
        
        try:
            while self._worker_active and not self._shutdown_event.is_set():
                # Process tasks with priority
                task_processed = False
                
                for priority in [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
                    if len(self.processing_tasks) >= self._max_concurrent_tasks:
                        break
                    
                    queue = self.pending_queues[priority]
                    if queue:
                        task_id = queue.pop(0)
                        task = self.tasks.get(task_id)
                        
                        if task and task.status == TaskStatus.PENDING:
                            # Start processing task
                            asyncio.create_task(self._process_task(task))
                            task_processed = True
                
                if not task_processed:
                    # No tasks to process, wait a bit
                    await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Queue worker error: {e}")
        finally:
            self._worker_active = False
            logger.info("Queue worker stopped")
    
    async def _process_task(self, task: QueueTask):
        """Process an individual task"""
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now()
        self.processing_tasks[task.task_id] = task
        
        logger.info(f"Processing task {task.task_id} ({task.task_type})")
        
        try:
            # Get handler for task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler found for task type: {task.task_type}")
            
            # Execute the task
            await handler(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            logger.info(f"Completed task {task.task_id}")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # Handle retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.started_at = None
                
                # Re-enqueue with lower priority
                priority = TaskPriority.LOW if task.priority == TaskPriority.URGENT else task.priority
                self.pending_queues[priority].append(task.task_id)
                
                logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
            else:
                # Max retries reached
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error_message = str(e)
                
        finally:
            # Remove from processing
            if task.task_id in self.processing_tasks:
                del self.processing_tasks[task.task_id]
    
    async def _handle_trade_analysis(self, task: QueueTask):
        """Handle trade analysis task"""
        payload = task.payload
        analysis_id = payload['analysis_id']
        
        try:
            # Import here to avoid circular imports
            from ..crews.front_office_crew import FrontOfficeCrew
            
            crew = FrontOfficeCrew()
            
            # Process the analysis
            result = await crew.analyze_trade_request_with_progress(
                team_key=payload['team_data']['team_key'],
                request_text=payload['request_data']['request'],
                urgency=payload['request_data'].get('urgency', 'medium'),
                budget_limit=payload['request_data'].get('budget_limit'),
                include_prospects=payload['request_data'].get('include_prospects', True),
                analysis_id=analysis_id
            )
            
            # Update task with results
            task.payload['result'] = result
            
            logger.info(f"Trade analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Trade analysis {analysis_id} failed: {e}")
            raise
    
    async def _handle_data_refresh(self, task: QueueTask):
        """Handle data refresh task"""
        try:
            from ..services.data_ingestion import data_service
            await data_service.run_daily_update()
            logger.info("Data refresh completed")
        except Exception as e:
            logger.error(f"Data refresh failed: {e}")
            raise
    
    async def _handle_cache_warming(self, task: QueueTask):
        """Handle cache warming task"""
        try:
            from ..services.cache_service import cache_service
            result = await cache_service.warm_cache()
            task.payload['result'] = result
            logger.info("Cache warming completed")
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            raise
    
    async def _handle_cleanup(self, task: QueueTask):
        """Handle cleanup task"""
        try:
            # Clean up old completed/failed tasks
            cutoff_time = datetime.now() - asyncio.timedelta(hours=24)
            
            tasks_to_remove = [
                task_id for task_id, task in self.tasks.items()
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                and task.completed_at and task.completed_at < cutoff_time
            ]
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
            
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the queue service"""
        logger.info("Shutting down queue service...")
        self._shutdown_event.set()
        self._worker_active = False
        
        # Wait for processing tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = datetime.now()
        
        while self.processing_tasks and (datetime.now() - start_time).seconds < timeout:
            await asyncio.sleep(1)
        
        if self.processing_tasks:
            logger.warning(f"{len(self.processing_tasks)} tasks still processing during shutdown")
        
        logger.info("Queue service shutdown complete")


# Global queue service instance
queue_service = QueueService()