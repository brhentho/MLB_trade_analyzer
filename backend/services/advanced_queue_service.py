"""
Advanced Background Task Queue Service for Baseball Trade AI
Priority-based task processing, graceful shutdown, and comprehensive monitoring
"""

import asyncio
import json
import logging
import os
import pickle
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from typing import Any, Dict, List, Optional, Callable, Set, Tuple, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Configuration
MAX_WORKERS = int(os.getenv('QUEUE_MAX_WORKERS', '4'))
MAX_RETRIES = int(os.getenv('QUEUE_MAX_RETRIES', '3'))
RETRY_DELAY = int(os.getenv('QUEUE_RETRY_DELAY', '60'))  # seconds
TASK_TIMEOUT = int(os.getenv('QUEUE_TASK_TIMEOUT', '300'))  # 5 minutes
ENABLE_PERSISTENCE = os.getenv('ENABLE_QUEUE_PERSISTENCE', 'false').lower() == 'true'
QUEUE_STORAGE_PATH = os.getenv('QUEUE_STORAGE_PATH', './queue_data')


class TaskPriority(IntEnum):
    """Task priority levels (higher number = higher priority)"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class TaskStatus(str):
    """Task status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    EXPIRED = "expired"


@dataclass
class QueueTask:
    """Task definition with comprehensive metadata"""
    id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    status: str = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None  # For delayed tasks
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = MAX_RETRIES
    timeout_seconds: int = TASK_TIMEOUT
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-init validation and setup"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if isinstance(self.tags, list):
            self.tags = set(self.tags)
    
    @property
    def is_expired(self) -> bool:
        """Check if task has expired"""
        if not self.created_at:
            return False
        
        age = datetime.now(timezone.utc) - self.created_at
        return age > timedelta(hours=24)  # Tasks expire after 24 hours
    
    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries and self.status in [TaskStatus.FAILED]
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to run"""
        if self.scheduled_at:
            return datetime.now(timezone.utc) >= self.scheduled_at
        return self.status == TaskStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "error_message": self.error_message,
            "result": self.result,
            "tags": list(self.tags),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueTask':
        """Create task from dictionary"""
        # Parse datetime fields
        for field_name in ['created_at', 'scheduled_at', 'started_at', 'completed_at']:
            if data.get(field_name):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Convert priority back to enum
        if 'priority' in data:
            data['priority'] = TaskPriority(data['priority'])
        
        return cls(**data)


class TaskHandler:
    """Base class for task handlers"""
    
    def __init__(self, task_type: str):
        self.task_type = task_type
    
    async def execute(self, task: QueueTask) -> Dict[str, Any]:
        """Execute the task - override in subclasses"""
        raise NotImplementedError("Task handlers must implement execute method")
    
    async def on_success(self, task: QueueTask, result: Dict[str, Any]):
        """Called when task succeeds"""
        logger.info(f"Task {task.id} ({task.task_type}) completed successfully")
    
    async def on_failure(self, task: QueueTask, error: Exception):
        """Called when task fails"""
        logger.error(f"Task {task.id} ({task.task_type}) failed: {error}")
    
    async def on_retry(self, task: QueueTask, error: Exception):
        """Called before retrying a failed task"""
        logger.warning(f"Retrying task {task.id} ({task.task_type}): attempt {task.retry_count + 1}")


class TradeAnalysisTaskHandler(TaskHandler):
    """Handler for trade analysis tasks"""
    
    def __init__(self):
        super().__init__("trade_analysis")
    
    async def execute(self, task: QueueTask) -> Dict[str, Any]:
        """Execute trade analysis task"""
        from ..crews.front_office_crew import FrontOfficeCrew
        from ..services.supabase_service import supabase_service
        
        payload = task.payload
        analysis_id = payload.get("analysis_id")
        
        try:
            # Update status to running
            await supabase_service.update_trade_analysis_status(
                analysis_id, "analyzing"
            )
            
            # Run the analysis
            crew = FrontOfficeCrew()
            result = await crew.analyze_trade_request_with_progress(
                team_key=payload["team_key"],
                request_text=payload["request_text"],
                urgency=payload.get("urgency", "medium"),
                budget_limit=payload.get("budget_limit"),
                include_prospects=payload.get("include_prospects", True),
                analysis_id=analysis_id
            )
            
            # Update with results
            await supabase_service.update_trade_analysis_status(
                analysis_id, "completed", results=result
            )
            
            return {"analysis_id": analysis_id, "result": result}
            
        except Exception as e:
            # Update with error
            await supabase_service.update_trade_analysis_status(
                analysis_id, "error", error_message=str(e)
            )
            raise


class DataUpdateTaskHandler(TaskHandler):
    """Handler for data update tasks"""
    
    def __init__(self):
        super().__init__("data_update")
    
    async def execute(self, task: QueueTask) -> Dict[str, Any]:
        """Execute data update task"""
        from ..services.data_ingestion import data_service
        
        update_type = task.payload.get("type", "full")
        
        if update_type == "full":
            result = await data_service.run_daily_update()
        elif update_type == "roster":
            result = await data_service.update_rosters()
        elif update_type == "stats":
            result = await data_service.update_player_stats()
        else:
            raise ValueError(f"Unknown update type: {update_type}")
        
        return {"update_type": update_type, "result": result}


class CleanupTaskHandler(TaskHandler):
    """Handler for cleanup tasks"""
    
    def __init__(self):
        super().__init__("cleanup")
    
    async def execute(self, task: QueueTask) -> Dict[str, Any]:
        """Execute cleanup task"""
        from ..services.cache_service import cache_service
        from ..services.supabase_service import supabase_service
        
        cleanup_type = task.payload.get("type", "general")
        cleaned_items = 0
        
        if cleanup_type in ["general", "cache"]:
            # Clean expired cache entries
            if hasattr(cache_service, '_cleanup_memory_cache'):
                await cache_service._cleanup_memory_cache()
                cleaned_items += 1
        
        if cleanup_type in ["general", "database"]:
            # Clean old analysis records (older than 30 days)
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            # This would be implemented in supabase_service
            cleaned_items += 1
        
        return {"cleanup_type": cleanup_type, "items_cleaned": cleaned_items}


class AdvancedQueueService:
    """Advanced background task queue service"""
    
    def __init__(self):
        self.tasks: Dict[str, QueueTask] = {}
        self.handlers: Dict[str, TaskHandler] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.worker_semaphore = asyncio.Semaphore(MAX_WORKERS)
        
        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_retried": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0
        }
        
        # Register default handlers
        self._register_default_handlers()
        
        # Setup persistence if enabled
        if ENABLE_PERSISTENCE:
            self._setup_persistence()
    
    def _register_default_handlers(self):
        """Register default task handlers"""
        self.register_handler(TradeAnalysisTaskHandler())
        self.register_handler(DataUpdateTaskHandler())
        self.register_handler(CleanupTaskHandler())
    
    def _setup_persistence(self):
        """Setup task persistence"""
        os.makedirs(QUEUE_STORAGE_PATH, exist_ok=True)
        logger.info(f"Queue persistence enabled: {QUEUE_STORAGE_PATH}")
    
    def register_handler(self, handler: TaskHandler):
        """Register a task handler"""
        self.handlers[handler.task_type] = handler
        logger.info(f"Registered handler for task type: {handler.task_type}")
    
    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        delay_seconds: int = 0,
        max_retries: int = MAX_RETRIES,
        timeout_seconds: int = TASK_TIMEOUT,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enqueue a new task"""
        
        if task_type not in self.handlers:
            raise ValueError(f"No handler registered for task type: {task_type}")
        
        # Create task
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            priority=priority,
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=delay_seconds) if delay_seconds > 0 else None,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            tags=tags or set(),
            metadata=metadata or {}
        )
        
        # Store task
        self.tasks[task.id] = task
        
        # Persist if enabled
        if ENABLE_PERSISTENCE:
            await self._persist_task(task)
        
        logger.info(
            f"Enqueued task {task.id} ({task_type}) with priority {priority.name}"
            f"{f' (delayed {delay_seconds}s)' if delay_seconds > 0 else ''}"
        )
        
        return task.id
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
            task.status = TaskStatus.CANCELLED
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False
    
    async def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def get_tasks_by_type(self, task_type: str, status: Optional[str] = None) -> List[QueueTask]:
        """Get tasks by type and optionally status"""
        tasks = [task for task in self.tasks.values() if task.task_type == task_type]
        
        if status:
            tasks = [task for task in tasks if task.status == status]
        
        return tasks
    
    async def get_tasks_by_tags(self, tags: Set[str]) -> List[QueueTask]:
        """Get tasks by tags"""
        return [
            task for task in self.tasks.values()
            if tags.intersection(task.tags)
        ]
    
    async def start(self):
        """Start the queue service"""
        if self.running:
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        # Load persisted tasks
        if ENABLE_PERSISTENCE:
            await self._load_persisted_tasks()
        
        # Start worker tasks
        for i in range(MAX_WORKERS):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start maintenance task
        maintenance_task = asyncio.create_task(self._maintenance_loop())
        self.workers.append(maintenance_task)
        
        logger.info(f"Queue service started with {MAX_WORKERS} workers")
    
    async def shutdown(self, timeout: int = 30):
        """Graceful shutdown of the queue service"""
        if not self.running:
            return
        
        logger.info("Initiating queue service shutdown...")
        
        # Signal shutdown
        self.running = False
        self.shutdown_event.set()
        
        # Wait for workers to finish current tasks
        if self.workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.workers, return_exceptions=True),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Queue shutdown timeout after {timeout}s, cancelling workers")
                for worker in self.workers:
                    worker.cancel()
        
        # Persist remaining tasks
        if ENABLE_PERSISTENCE:
            await self._persist_all_tasks()
        
        logger.info("Queue service shutdown complete")
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get next task
                task = await self._get_next_task()
                
                if not task:
                    # No tasks available, sleep briefly
                    await asyncio.sleep(1)
                    continue
                
                # Process task with semaphore
                async with self.worker_semaphore:
                    await self._process_task(task, worker_id)
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause on error
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_task(self) -> Optional[QueueTask]:
        """Get the next task to process (priority-based)"""
        ready_tasks = [
            task for task in self.tasks.values()
            if task.is_ready and task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]
            and not task.is_expired
        ]
        
        if not ready_tasks:
            return None
        
        # Sort by priority (descending) then by created_at (ascending)
        ready_tasks.sort(
            key=lambda t: (-t.priority.value, t.created_at)
        )
        
        return ready_tasks[0]
    
    async def _process_task(self, task: QueueTask, worker_id: str):
        """Process a single task"""
        handler = self.handlers.get(task.task_type)
        if not handler:
            logger.error(f"No handler for task type: {task.task_type}")
            task.status = TaskStatus.FAILED
            task.error_message = f"No handler for task type: {task.task_type}"
            return
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        
        logger.info(f"Worker {worker_id} processing task {task.id} ({task.task_type})")
        
        start_time = time.time()
        
        try:
            # Execute task with timeout
            result = await asyncio.wait_for(
                handler.execute(task),
                timeout=task.timeout_seconds
            )
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            task.result = result
            
            await handler.on_success(task, result)
            
            # Update statistics
            self.stats["tasks_completed"] += 1
            processing_time = time.time() - start_time
            self.stats["total_processing_time"] += processing_time
            self.stats["avg_processing_time"] = (
                self.stats["total_processing_time"] / self.stats["tasks_processed"]
            )
            
            logger.info(f"Task {task.id} completed in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            error_msg = f"Task timeout after {task.timeout_seconds} seconds"
            await self._handle_task_failure(task, handler, Exception(error_msg))
            
        except Exception as e:
            await self._handle_task_failure(task, handler, e)
        
        finally:
            self.stats["tasks_processed"] += 1
            
            # Persist task state
            if ENABLE_PERSISTENCE:
                await self._persist_task(task)
    
    async def _handle_task_failure(self, task: QueueTask, handler: TaskHandler, error: Exception):
        """Handle task failure and retry logic"""
        task.error_message = str(error)
        
        if task.can_retry:
            task.status = TaskStatus.RETRYING
            task.retry_count += 1
            task.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=RETRY_DELAY)
            
            await handler.on_retry(task, error)
            self.stats["tasks_retried"] += 1
            
            logger.warning(
                f"Task {task.id} failed, retry {task.retry_count}/{task.max_retries} "
                f"scheduled in {RETRY_DELAY}s: {error}"
            )
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now(timezone.utc)
            
            await handler.on_failure(task, error)
            self.stats["tasks_failed"] += 1
            
            logger.error(f"Task {task.id} failed permanently: {error}")
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.running:
            try:
                await self._cleanup_old_tasks()
                await asyncio.sleep(300)  # Run every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_tasks(self):
        """Clean up old completed/failed tasks"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        
        tasks_to_remove = [
            task_id for task_id, task in self.tasks.items()
            if task.completed_at and task.completed_at < cutoff_time
            and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    async def _persist_task(self, task: QueueTask):
        """Persist a single task to storage"""
        if not ENABLE_PERSISTENCE:
            return
        
        try:
            file_path = os.path.join(QUEUE_STORAGE_PATH, f"task_{task.id}.json")
            with open(file_path, 'w') as f:
                json.dump(task.to_dict(), f)
        except Exception as e:
            logger.error(f"Failed to persist task {task.id}: {e}")
    
    async def _persist_all_tasks(self):
        """Persist all tasks to storage"""
        if not ENABLE_PERSISTENCE:
            return
        
        try:
            # Save active tasks
            active_tasks = [
                task.to_dict() for task in self.tasks.values()
                if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
            ]
            
            queue_file = os.path.join(QUEUE_STORAGE_PATH, "queue_state.json")
            with open(queue_file, 'w') as f:
                json.dump({
                    "tasks": active_tasks,
                    "stats": self.stats,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f)
            
            logger.info(f"Persisted {len(active_tasks)} active tasks")
        except Exception as e:
            logger.error(f"Failed to persist queue state: {e}")
    
    async def _load_persisted_tasks(self):
        """Load persisted tasks from storage"""
        if not ENABLE_PERSISTENCE:
            return
        
        try:
            queue_file = os.path.join(QUEUE_STORAGE_PATH, "queue_state.json")
            if os.path.exists(queue_file):
                with open(queue_file, 'r') as f:
                    data = json.load(f)
                
                loaded_count = 0
                for task_data in data.get("tasks", []):
                    try:
                        task = QueueTask.from_dict(task_data)
                        
                        # Reset running tasks to pending
                        if task.status == TaskStatus.RUNNING:
                            task.status = TaskStatus.PENDING
                            task.started_at = None
                        
                        self.tasks[task.id] = task
                        loaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to load task: {e}")
                
                # Restore statistics
                if "stats" in data:
                    self.stats.update(data["stats"])
                
                logger.info(f"Loaded {loaded_count} persisted tasks")
        except Exception as e:
            logger.error(f"Failed to load persisted tasks: {e}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        status_counts = {}
        priority_counts = {}
        type_counts = {}
        
        for task in self.tasks.values():
            # Status counts
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
            
            # Priority counts
            priority_name = task.priority.name
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
            
            # Type counts
            type_counts[task.task_type] = type_counts.get(task.task_type, 0) + 1
        
        return {
            **self.stats,
            "total_tasks": len(self.tasks),
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "type_counts": type_counts,
            "active_workers": len([w for w in self.workers if not w.done()]),
            "max_workers": MAX_WORKERS,
            "running": self.running,
            "handlers_registered": list(self.handlers.keys())
        }


# Global queue service instance
advanced_queue_service = AdvancedQueueService()


# Export main components
__all__ = [
    'AdvancedQueueService', 'QueueTask', 'TaskHandler', 'TaskPriority', 'TaskStatus',
    'TradeAnalysisTaskHandler', 'DataUpdateTaskHandler', 'CleanupTaskHandler',
    'advanced_queue_service'
]