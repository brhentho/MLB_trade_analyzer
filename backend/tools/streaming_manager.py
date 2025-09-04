"""
Streaming Manager for Real-time Progress Updates
Provides real-time streaming of analysis progress to clients
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class StreamEventType(Enum):
    """Types of streaming events"""
    PROGRESS_UPDATE = "progress_update"
    STAGE_COMPLETE = "stage_complete"
    ERROR_OCCURRED = "error_occurred"
    ANALYSIS_COMPLETE = "analysis_complete"
    COST_UPDATE = "cost_update"
    WARNING = "warning"
    INFO = "info"

@dataclass
class StreamEvent:
    """Individual streaming event"""
    event_type: StreamEventType
    analysis_id: str
    timestamp: datetime
    data: Dict[str, Any]
    sequence_number: int = 0

class ProgressTracker:
    """Track progress for a single analysis"""
    
    def __init__(self, analysis_id: str, total_stages: int = 7):
        self.analysis_id = analysis_id
        self.total_stages = total_stages
        self.current_stage = 0
        self.stage_progress = 0.0  # Progress within current stage (0-100)
        self.overall_progress = 0.0  # Overall progress (0-100)
        self.stages_completed = []
        self.current_stage_name = "Initializing"
        self.start_time = datetime.now()
        self.stage_start_time = datetime.now()
        self.estimated_completion_time = None
        self.cost_tracking = {
            'tokens_used': 0,
            'estimated_cost': 0.0,
            'cost_breakdown': {}
        }
        self.warnings = []
        self.status = "starting"
        
    def update_stage(self, stage_name: str, stage_progress: float = 0.0):
        """Update current stage and progress"""
        if stage_name != self.current_stage_name:
            # Completing previous stage
            if self.current_stage_name != "Initializing":
                self.stages_completed.append({
                    'stage': self.current_stage_name,
                    'completed_at': datetime.now(),
                    'duration_seconds': (datetime.now() - self.stage_start_time).total_seconds()
                })
            
            # Starting new stage
            self.current_stage += 1
            self.current_stage_name = stage_name
            self.stage_start_time = datetime.now()
            self.stage_progress = 0.0
        
        # Update progress
        self.stage_progress = min(100.0, max(0.0, stage_progress))
        self.overall_progress = ((self.current_stage - 1) / self.total_stages * 100) + (self.stage_progress / self.total_stages)
        self.overall_progress = min(100.0, max(0.0, self.overall_progress))
        
        # Update estimated completion time
        if self.overall_progress > 10:  # Wait for some progress before estimating
            elapsed = (datetime.now() - self.start_time).total_seconds()
            estimated_total_time = elapsed * (100 / self.overall_progress)
            self.estimated_completion_time = self.start_time + timedelta(seconds=estimated_total_time)
    
    def update_cost(self, tokens_used: int, cost: float, model: str):
        """Update cost tracking information"""
        self.cost_tracking['tokens_used'] += tokens_used
        self.cost_tracking['estimated_cost'] += cost
        
        if model not in self.cost_tracking['cost_breakdown']:
            self.cost_tracking['cost_breakdown'][model] = {'tokens': 0, 'cost': 0.0}
        
        self.cost_tracking['cost_breakdown'][model]['tokens'] += tokens_used
        self.cost_tracking['cost_breakdown'][model]['cost'] += cost
    
    def add_warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a warning message"""
        self.warnings.append({
            'message': message,
            'timestamp': datetime.now(),
            'details': details or {}
        })
    
    def get_progress_data(self) -> Dict[str, Any]:
        """Get current progress data for streaming"""
        return {
            'analysis_id': self.analysis_id,
            'overall_progress': round(self.overall_progress, 1),
            'current_stage': self.current_stage,
            'current_stage_name': self.current_stage_name,
            'stage_progress': round(self.stage_progress, 1),
            'total_stages': self.total_stages,
            'stages_completed': self.stages_completed,
            'elapsed_time_seconds': (datetime.now() - self.start_time).total_seconds(),
            'estimated_completion_time': self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            'cost_tracking': self.cost_tracking,
            'warnings_count': len(self.warnings),
            'status': self.status
        }

class StreamingManager:
    """
    Manage real-time streaming of analysis progress to clients
    
    Features:
    - Real-time progress updates
    - Cost tracking and alerts
    - Error and warning notifications
    - Multiple client support per analysis
    - Event buffering and replay
    - Automatic cleanup of completed analyses
    """
    
    def __init__(self, max_events_per_stream: int = 1000, cleanup_after_hours: int = 24):
        self.active_streams: Dict[str, ProgressTracker] = {}
        self.event_streams: Dict[str, List[StreamEvent]] = {}
        self.client_callbacks: Dict[str, List[Callable]] = {}
        self.max_events_per_stream = max_events_per_stream
        self.cleanup_after_hours = cleanup_after_hours
        
        # Global sequence counter for events
        self._sequence_counter = 0
        
        logger.info("StreamingManager initialized")
    
    def start_analysis_stream(self, analysis_id: str, total_stages: int = 7) -> ProgressTracker:
        """Start streaming for a new analysis"""
        if analysis_id in self.active_streams:
            logger.warning(f"Analysis stream {analysis_id} already exists - replacing")
        
        tracker = ProgressTracker(analysis_id, total_stages)
        self.active_streams[analysis_id] = tracker
        self.event_streams[analysis_id] = []
        self.client_callbacks[analysis_id] = []
        
        # Send initial event
        self._add_event(
            analysis_id,
            StreamEventType.INFO,
            {
                'message': 'Analysis stream started',
                'total_stages': total_stages,
                'start_time': tracker.start_time.isoformat()
            }
        )
        
        logger.info(f"Started analysis stream for {analysis_id}")
        return tracker
    
    async def stream_progress(self, analysis_id: str, progress_data: Dict[str, Any]):
        """Stream progress update for an analysis"""
        if analysis_id not in self.active_streams:
            logger.warning(f"No active stream for analysis {analysis_id}")
            return
        
        tracker = self.active_streams[analysis_id]
        
        # Update tracker based on progress data
        if 'stage' in progress_data:
            stage_progress = progress_data.get('progress', 0.0)
            tracker.update_stage(progress_data['stage'], stage_progress)
        
        if 'tokens_used' in progress_data:
            cost = progress_data.get('estimated_cost', 0.0)
            model = progress_data.get('model', 'unknown')
            tracker.update_cost(progress_data['tokens_used'], cost, model)
        
        if 'warning' in progress_data:
            tracker.add_warning(progress_data['warning'], progress_data.get('warning_details'))
        
        if 'status' in progress_data:
            tracker.status = progress_data['status']
        
        # Create progress event
        event_data = {
            **tracker.get_progress_data(),
            **progress_data  # Allow override of tracker data
        }
        
        await self._broadcast_event(
            analysis_id,
            StreamEventType.PROGRESS_UPDATE,
            event_data
        )
    
    async def stream_stage_complete(self, analysis_id: str, stage_name: str, stage_data: Dict[str, Any]):
        """Stream stage completion event"""
        if analysis_id in self.active_streams:
            tracker = self.active_streams[analysis_id]
            tracker.update_stage(stage_name, 100.0)  # Mark stage as complete
            
            event_data = {
                'stage_name': stage_name,
                'stage_data': stage_data,
                'overall_progress': tracker.overall_progress,
                'timestamp': datetime.now().isoformat()
            }
            
            await self._broadcast_event(
                analysis_id,
                StreamEventType.STAGE_COMPLETE,
                event_data
            )
    
    async def stream_error(self, analysis_id: str, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Stream error event"""
        if analysis_id in self.active_streams:
            tracker = self.active_streams[analysis_id]
            tracker.status = "error"
            
            event_data = {
                'error_message': error_message,
                'error_details': error_details or {},
                'analysis_id': analysis_id,
                'timestamp': datetime.now().isoformat()
            }
            
            await self._broadcast_event(
                analysis_id,
                StreamEventType.ERROR_OCCURRED,
                event_data
            )
    
    async def stream_completion(self, analysis_id: str, final_results: Dict[str, Any]):
        """Stream analysis completion event"""
        if analysis_id not in self.active_streams:
            logger.warning(f"No active stream for analysis {analysis_id}")
            return
        
        tracker = self.active_streams[analysis_id]
        tracker.status = "completed"
        tracker.overall_progress = 100.0
        
        # Calculate final statistics
        total_duration = (datetime.now() - tracker.start_time).total_seconds()
        
        event_data = {
            'analysis_id': analysis_id,
            'completion_time': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'final_results': final_results,
            'cost_summary': tracker.cost_tracking,
            'stages_completed': len(tracker.stages_completed),
            'warnings_count': len(tracker.warnings)
        }
        
        await self._broadcast_event(
            analysis_id,
            StreamEventType.ANALYSIS_COMPLETE,
            event_data
        )
        
        # Schedule cleanup
        asyncio.create_task(self._schedule_cleanup(analysis_id))
    
    async def stream_cost_alert(self, analysis_id: str, alert_data: Dict[str, Any]):
        """Stream cost-related alert"""
        event_data = {
            'alert_type': 'cost_alert',
            'analysis_id': analysis_id,
            'alert_data': alert_data,
            'timestamp': datetime.now().isoformat()
        }
        
        await self._broadcast_event(
            analysis_id,
            StreamEventType.COST_UPDATE,
            event_data
        )
    
    def register_client_callback(self, analysis_id: str, callback: Callable):
        """Register a callback for streaming events"""
        if analysis_id not in self.client_callbacks:
            self.client_callbacks[analysis_id] = []
        
        self.client_callbacks[analysis_id].append(callback)
        logger.debug(f"Registered callback for analysis {analysis_id}")
    
    def unregister_client_callback(self, analysis_id: str, callback: Callable):
        """Unregister a client callback"""
        if analysis_id in self.client_callbacks:
            try:
                self.client_callbacks[analysis_id].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    async def get_stream_generator(self, analysis_id: str) -> AsyncGenerator[StreamEvent, None]:
        """Get an async generator for streaming events"""
        if analysis_id not in self.event_streams:
            return
        
        # Send existing events first
        for event in self.event_streams[analysis_id]:
            yield event
        
        # Set up callback for new events
        new_events = asyncio.Queue()
        
        async def callback(event: StreamEvent):
            await new_events.put(event)
        
        self.register_client_callback(analysis_id, callback)
        
        try:
            # Stream new events as they come
            while analysis_id in self.active_streams:
                try:
                    event = await asyncio.wait_for(new_events.get(), timeout=30)
                    yield event
                    
                    # Check if analysis is complete
                    if event.event_type == StreamEventType.ANALYSIS_COMPLETE:
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive event
                    yield StreamEvent(
                        event_type=StreamEventType.INFO,
                        analysis_id=analysis_id,
                        timestamp=datetime.now(),
                        data={'message': 'keepalive'},
                        sequence_number=self._get_next_sequence()
                    )
                    
        finally:
            self.unregister_client_callback(analysis_id, callback)
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an analysis"""
        if analysis_id not in self.active_streams:
            return None
        
        tracker = self.active_streams[analysis_id]
        return tracker.get_progress_data()
    
    def get_event_history(self, analysis_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get event history for an analysis"""
        if analysis_id not in self.event_streams:
            return []
        
        events = self.event_streams[analysis_id][-limit:]
        return [
            {
                'event_type': event.event_type.value,
                'timestamp': event.timestamp.isoformat(),
                'data': event.data,
                'sequence_number': event.sequence_number
            }
            for event in events
        ]
    
    async def _broadcast_event(self, analysis_id: str, event_type: StreamEventType, data: Dict[str, Any]):
        """Broadcast event to all clients"""
        event = StreamEvent(
            event_type=event_type,
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data=data,
            sequence_number=self._get_next_sequence()
        )
        
        self._add_event(analysis_id, event_type, data)
        
        # Call registered callbacks
        callbacks = self.client_callbacks.get(analysis_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in stream callback: {e}")
    
    def _add_event(self, analysis_id: str, event_type: StreamEventType, data: Dict[str, Any]):
        """Add event to stream history"""
        if analysis_id not in self.event_streams:
            self.event_streams[analysis_id] = []
        
        event = StreamEvent(
            event_type=event_type,
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            data=data,
            sequence_number=self._get_next_sequence()
        )
        
        events = self.event_streams[analysis_id]
        events.append(event)
        
        # Limit event history size
        if len(events) > self.max_events_per_stream:
            self.event_streams[analysis_id] = events[-self.max_events_per_stream:]
    
    def _get_next_sequence(self) -> int:
        """Get next sequence number"""
        self._sequence_counter += 1
        return self._sequence_counter
    
    async def _schedule_cleanup(self, analysis_id: str):
        """Schedule cleanup of completed analysis"""
        await asyncio.sleep(self.cleanup_after_hours * 3600)  # Convert to seconds
        await self.cleanup_analysis(analysis_id)
    
    async def cleanup_analysis(self, analysis_id: str):
        """Clean up resources for a completed analysis"""
        try:
            if analysis_id in self.active_streams:
                del self.active_streams[analysis_id]
            
            if analysis_id in self.client_callbacks:
                del self.client_callbacks[analysis_id]
            
            # Keep event history but mark for eventual cleanup
            if analysis_id in self.event_streams:
                # Could implement a separate cleanup strategy for events
                pass
            
            logger.info(f"Cleaned up analysis stream {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up analysis {analysis_id}: {e}")
    
    async def cleanup_old_streams(self):
        """Clean up old streams that should be removed"""
        cutoff_time = datetime.now() - timedelta(hours=self.cleanup_after_hours)
        
        analyses_to_remove = []
        for analysis_id, tracker in self.active_streams.items():
            if tracker.start_time < cutoff_time and tracker.status in ['completed', 'error']:
                analyses_to_remove.append(analysis_id)
        
        for analysis_id in analyses_to_remove:
            await self.cleanup_analysis(analysis_id)
        
        logger.info(f"Cleaned up {len(analyses_to_remove)} old streams")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide streaming statistics"""
        active_count = len(self.active_streams)
        total_events = sum(len(events) for events in self.event_streams.values())
        total_callbacks = sum(len(callbacks) for callbacks in self.client_callbacks.values())
        
        # Status breakdown
        status_counts = {}
        for tracker in self.active_streams.values():
            status = tracker.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'active_streams': active_count,
            'total_events_stored': total_events,
            'total_client_callbacks': total_callbacks,
            'status_breakdown': status_counts,
            'events_per_stream_limit': self.max_events_per_stream,
            'cleanup_after_hours': self.cleanup_after_hours,
            'global_sequence_number': self._sequence_counter
        }

# Server-Sent Events (SSE) formatter
def format_sse_event(event: StreamEvent) -> str:
    """Format event for Server-Sent Events"""
    data = {
        'type': event.event_type.value,
        'analysis_id': event.analysis_id,
        'timestamp': event.timestamp.isoformat(),
        'sequence': event.sequence_number,
        'data': event.data
    }
    
    return f"data: {json.dumps(data)}\n\n"

# WebSocket message formatter
def format_websocket_message(event: StreamEvent) -> str:
    """Format event for WebSocket transmission"""
    return json.dumps({
        'type': event.event_type.value,
        'analysis_id': event.analysis_id,
        'timestamp': event.timestamp.isoformat(),
        'sequence': event.sequence_number,
        'data': event.data
    })

# Global streaming manager instance
streaming_manager = StreamingManager()