"""
Optimized Database Service for Baseball Trade AI
Incorporates connection pooling, async optimization, structured logging, and performance monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
import weakref
from contextlib import asynccontextmanager

from supabase import create_client, Client
from supabase.client import ClientOptions

# Core systems with fallbacks
try:
    from core.async_manager import AsyncServiceMixin, safe_async_call, async_nullcontext
    from core.logging_config import get_logger, log_exceptions, logging_context, get_performance_logger
    from core.performance import profile_performance, cache_result, resource_manager, AdvancedCache
    from core.config import get_database_config, get_performance_config
except ImportError:
    # Fallback implementations for core systems
    class AsyncServiceMixin:
        async def ensure_initialized(self):
            if not hasattr(self, '_initialized'):
                await self.async_init()
                self._initialized = True
        async def async_init(self):
            pass
        async def async_cleanup(self):
            pass
    
    def safe_async_call(func):
        return func
    
    from contextlib import nullcontext as async_nullcontext
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def get_performance_logger(name):
        return logging.getLogger(f"{name}.performance")
    
    def log_exceptions(logger):
        def decorator(func):
            return func
        return decorator
    
    from contextlib import contextmanager
    @contextmanager
    def logging_context(**kwargs):
        yield
    
    def profile_performance(name):
        def decorator(func):
            return func
        return decorator
    
    def cache_result(cache_name=None, ttl=None):
        def decorator(func):
            return func
        return decorator
    
    class MockCache:
        def __init__(self, max_size=1000, default_ttl=300):
            self.cache = {}
            self.max_size = max_size
            self.default_ttl = default_ttl
        
        async def get(self, key):
            return self.cache.get(key)
        
        async def set(self, key, value, ttl=None):
            if len(self.cache) < self.max_size:
                self.cache[key] = value
        
        async def delete(self, key):
            self.cache.pop(key, None)
        
        def get_stats(self):
            return {'size': len(self.cache), 'max_size': self.max_size}
    
    class MockResourceManager:
        def __init__(self):
            self.caches = {}
        
        def add_cache(self, name, cache):
            self.caches[name] = cache
        
        def get_cache(self, name):
            return self.caches.get(name)
    
    resource_manager = MockResourceManager()
    AdvancedCache = MockCache
    
    class MockConfig:
        def __init__(self):
            self.url = os.getenv('SUPABASE_URL', '')
            self.service_key = os.getenv('SUPABASE_SERVICE_KEY', '')
            self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
            self.query_timeout = int(os.getenv('DB_QUERY_TIMEOUT', '30'))
    
    def get_database_config():
        return MockConfig()
    
    def get_performance_config():
        return MockConfig()

logger = get_logger(__name__)
performance_logger = get_performance_logger(__name__)

# Import OS for environment variables
import os


@dataclass
class TradeAnalysisRecord:
    """Enhanced trade analysis record with validation"""
    analysis_id: str
    requesting_team_id: int
    request_text: str
    urgency: str = 'medium'
    status: str = 'queued'
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    cost_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.urgency not in ['low', 'medium', 'high']:
            raise ValueError(f"Invalid urgency level: {self.urgency}")
        
        if self.status not in ['queued', 'analyzing', 'completed', 'error']:
            raise ValueError(f"Invalid status: {self.status}")


class ConnectionManager:
    """
    Advanced connection manager with pooling and health monitoring
    """
    
    def __init__(self, db_config):
        self.db_config = db_config
        self._client: Optional[Client] = None
        self._connection_pool = []
        self._pool_lock = asyncio.Lock()
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        self._connection_count = 0
        self._max_connections = db_config.pool_size
        self._failed_connections = 0
        self._health_status = "unknown"
    
    async def initialize(self):
        """Initialize the connection manager"""
        try:
            # Create primary client
            client_options = ClientOptions(
                postgrest_client_timeout=self.db_config.query_timeout,
                storage_client_timeout=self.db_config.query_timeout
            )
            
            self._client = create_client(
                self.db_config.url,
                self.db_config.service_key,
                options=client_options
            )
            
            # Test connection
            await self._test_connection()
            self._health_status = "healthy"
            
            logger.info("Database connection manager initialized successfully")
            
        except Exception as e:
            self._health_status = "error"
            logger.error(f"Failed to initialize database connection manager: {e}")
            raise
    
    async def _test_connection(self):
        """Test database connectivity"""
        try:
            response = self._client.table('teams').select('id').limit(1).execute()
            if not response.data and len(response.data) >= 0:  # Empty result is OK
                return True
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    @asynccontextmanager
    async def get_client(self):
        """Get a database client with connection management"""
        try:
            # Perform health check if needed
            current_time = asyncio.get_event_loop().time()
            if current_time - self._last_health_check > self._health_check_interval:
                await self._health_check()
                self._last_health_check = current_time
            
            if not self._client:
                await self.initialize()
            
            yield self._client
            
        except Exception as e:
            self._failed_connections += 1
            logger.error(f"Database client error: {e}")
            raise
    
    async def _health_check(self):
        """Perform health check on database connection"""
        try:
            await self._test_connection()
            self._health_status = "healthy"
            if self._failed_connections > 0:
                logger.info("Database connection recovered")
                self._failed_connections = 0
                
        except Exception as e:
            self._health_status = "degraded"
            logger.warning(f"Database health check failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            'health_status': self._health_status,
            'connection_count': self._connection_count,
            'max_connections': self._max_connections,
            'failed_connections': self._failed_connections,
            'last_health_check': self._last_health_check
        }
    
    async def shutdown(self):
        """Shutdown connection manager"""
        logger.info("Shutting down database connection manager")
        # Supabase client doesn't need explicit closing
        self._client = None
        self._connection_pool.clear()


class QueryOptimizer:
    """
    Database query optimization with caching and performance tracking
    """
    
    def __init__(self):
        self.query_cache = {}
        self.slow_queries = []
        self._cache_ttl = 300  # 5 minutes
    
    def get_optimized_team_query(self) -> str:
        """Get optimized team query with proper indexing"""
        return """
        SELECT 
            id, team_key, name, abbreviation, city, division, league,
            budget_level, competitive_window, market_size, philosophy,
            primary_color, secondary_color, created_at, updated_at
        FROM teams 
        WHERE active = true 
        ORDER BY league, division, name
        """
    
    def get_optimized_roster_query(self) -> str:
        """Get optimized roster query with joins"""
        return """
        SELECT 
            p.id, p.name, p.position, p.jersey_number, p.status,
            p.age, p.salary, p.contract_years, p.team_id,
            s.games_played, s.batting_avg, s.era, s.war, s.season
        FROM players p
        LEFT JOIN stats_cache s ON p.id = s.player_id AND s.season = 2024
        WHERE p.team_id = $1 AND p.active = true
        ORDER BY p.position, p.jersey_number
        """
    
    def track_slow_query(self, query_type: str, duration: float, metadata: Dict[str, Any]):
        """Track slow queries for optimization"""
        if duration > 1.0:  # Queries > 1 second
            slow_query = {
                'query_type': query_type,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata
            }
            self.slow_queries.append(slow_query)
            
            # Keep only recent slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]
            
            logger.warning(f"Slow query detected: {query_type} took {duration:.2f}s")


class OptimizedSupabaseService(AsyncServiceMixin):
    """
    Optimized Supabase service with all performance enhancements
    """
    
    def __init__(self):
        super().__init__()
        self.db_config = get_database_config()
        self.perf_config = get_performance_config()
        
        # Components
        self.connection_manager = ConnectionManager(self.db_config)
        self.query_optimizer = QueryOptimizer()
        
        # Caching
        self._setup_caches()
        
        # Metrics
        self._query_count = 0
        self._error_count = 0
        
        logger.info("OptimizedSupabaseService initialized")
    
    def _setup_caches(self):
        """Setup specialized caches for different data types"""
        # Teams cache - long TTL since teams rarely change
        teams_cache = AdvancedCache(max_size=50, default_ttl=1800)  # 30 minutes
        resource_manager.add_cache("teams", teams_cache)
        
        # Players cache - medium TTL
        players_cache = AdvancedCache(max_size=2000, default_ttl=900)  # 15 minutes
        resource_manager.add_cache("players", players_cache)
        
        # Analysis cache - short TTL
        analysis_cache = AdvancedCache(max_size=500, default_ttl=300)  # 5 minutes
        resource_manager.add_cache("analysis", analysis_cache)
    
    async def async_init(self):
        """Async initialization"""
        await self.connection_manager.initialize()
        logger.info("OptimizedSupabaseService async initialization completed")
    
    async def async_cleanup(self):
        """Async cleanup"""
        await self.connection_manager.shutdown()
        logger.info("OptimizedSupabaseService cleanup completed")
    
    # ===================
    # TEAM OPERATIONS
    # ===================
    
    @profile_performance("get_all_teams")
    @cache_result(cache_name="teams", ttl=1800)
    @log_exceptions(logger)
    async def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all MLB teams with advanced caching"""
        await self.ensure_initialized()
        
        with logging_context(operation="get_all_teams"):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_teams_query"):
                    response = client.table('teams').select('*').eq('active', True).execute()
                    self._query_count += 1
                    
                    if not response.data:
                        logger.warning("No teams found in database")
                        return []
                    
                    logger.debug(f"Retrieved {len(response.data)} teams from database")
                    return response.data
    
    @profile_performance("get_team_by_id")
    @log_exceptions(logger)
    async def get_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get team by ID with caching"""
        await self.ensure_initialized()
        
        # Check cache first
        teams_cache = resource_manager.get_cache("teams")
        if teams_cache:
            cached_team = await teams_cache.get(f"team_id_{team_id}")
            if cached_team:
                return cached_team
        
        with logging_context(operation="get_team_by_id", team_id=team_id):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_team_by_id_query"):
                    response = client.table('teams').select('*').eq('id', team_id).execute()
                    self._query_count += 1
                    
                    if not response.data:
                        logger.debug(f"Team with ID {team_id} not found")
                        return None
                    
                    team_data = response.data[0]
                    
                    # Cache the result
                    if teams_cache:
                        await teams_cache.set(f"team_id_{team_id}", team_data, 1800)
                    
                    return team_data
    
    @profile_performance("get_team_by_key")
    @log_exceptions(logger)
    async def get_team_by_key(self, team_key: str) -> Optional[Dict[str, Any]]:
        """Get team by key with caching"""
        await self.ensure_initialized()
        
        team_key = team_key.lower().strip()
        
        # Check cache first
        teams_cache = resource_manager.get_cache("teams")
        if teams_cache:
            cached_team = await teams_cache.get(f"team_key_{team_key}")
            if cached_team:
                return cached_team
        
        with logging_context(operation="get_team_by_key", team_key=team_key):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_team_by_key_query"):
                    # Try team_key first, then abbreviation
                    response = client.table('teams').select('*').or_(
                        f'team_key.eq.{team_key},abbreviation.eq.{team_key.upper()}'
                    ).execute()
                    self._query_count += 1
                    
                    if not response.data:
                        logger.debug(f"Team with key '{team_key}' not found")
                        return None
                    
                    team_data = response.data[0]
                    
                    # Cache the result with multiple keys
                    if teams_cache:
                        await teams_cache.set(f"team_key_{team_key}", team_data, 1800)
                        await teams_cache.set(f"team_key_{team_data['team_key']}", team_data, 1800)
                        await teams_cache.set(f"team_key_{team_data['abbreviation'].lower()}", team_data, 1800)
                    
                    return team_data
    
    # ===================
    # PLAYER OPERATIONS
    # ===================
    
    @profile_performance("get_team_roster")
    @log_exceptions(logger)
    async def get_team_roster(self, team_id: int) -> List[Dict[str, Any]]:
        """Get team roster with optimized queries"""
        await self.ensure_initialized()
        
        # Check cache first
        players_cache = resource_manager.get_cache("players")
        cache_key = f"roster_{team_id}"
        
        if players_cache:
            cached_roster = await players_cache.get(cache_key)
            if cached_roster:
                return cached_roster
        
        with logging_context(operation="get_team_roster", team_id=team_id):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_roster_query"):
                    response = client.table('players').select(
                        'id, name, position, jersey_number, status, age, salary, contract_years, team_id'
                    ).eq('team_id', team_id).eq('active', True).order('position, jersey_number').execute()
                    self._query_count += 1
                    
                    roster = response.data or []
                    
                    # Cache the result
                    if players_cache:
                        await players_cache.set(cache_key, roster, 900)  # 15 minutes
                    
                    logger.debug(f"Retrieved roster of {len(roster)} players for team {team_id}")
                    return roster
    
    @profile_performance("search_players")
    @log_exceptions(logger)
    async def search_players(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search players with optimized text search"""
        await self.ensure_initialized()
        
        search_term = search_term.strip()
        if len(search_term) < 2:
            return []
        
        with logging_context(operation="search_players", search_term=search_term):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_player_search_query"):
                    response = client.table('players').select(
                        'id, name, position, team_id, age, salary'
                    ).ilike('name', f'%{search_term}%').limit(limit).execute()
                    self._query_count += 1
                    
                    players = response.data or []
                    logger.debug(f"Found {len(players)} players matching '{search_term}'")
                    return players
    
    # ===================
    # TRADE ANALYSIS OPERATIONS
    # ===================
    
    @profile_performance("create_trade_analysis")
    @log_exceptions(logger)
    async def create_trade_analysis(self, analysis: TradeAnalysisRecord) -> str:
        """Create trade analysis with validation and error handling"""
        await self.ensure_initialized()
        
        analysis_dict = asdict(analysis)
        analysis_dict['created_at'] = datetime.now().isoformat()
        analysis_dict['updated_at'] = analysis_dict['created_at']
        
        with logging_context(operation="create_trade_analysis", analysis_id=analysis.analysis_id):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_create_analysis_query"):
                    response = client.table('trade_analyses').insert(analysis_dict).execute()
                    self._query_count += 1
                    
                    if not response.data:
                        logger.error(f"Failed to create trade analysis {analysis.analysis_id}")
                        return ""
                    
                    logger.info(f"Created trade analysis {analysis.analysis_id}")
                    return analysis.analysis_id
    
    @profile_performance("get_trade_analysis")
    @log_exceptions(logger)
    async def get_trade_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get trade analysis with caching"""
        await self.ensure_initialized()
        
        # Check cache first
        analysis_cache = resource_manager.get_cache("analysis")
        if analysis_cache:
            cached_analysis = await analysis_cache.get(f"analysis_{analysis_id}")
            if cached_analysis:
                return cached_analysis
        
        with logging_context(operation="get_trade_analysis", analysis_id=analysis_id):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_get_analysis_query"):
                    response = client.table('trade_analyses').select('*').eq(
                        'analysis_id', analysis_id
                    ).execute()
                    self._query_count += 1
                    
                    if not response.data:
                        logger.debug(f"Trade analysis {analysis_id} not found")
                        return None
                    
                    analysis_data = response.data[0]
                    
                    # Cache completed analyses longer
                    ttl = 1800 if analysis_data.get('status') == 'completed' else 300
                    if analysis_cache:
                        await analysis_cache.set(f"analysis_{analysis_id}", analysis_data, ttl)
                    
                    return analysis_data
    
    @profile_performance("update_trade_analysis_status")
    @log_exceptions(logger)
    async def update_trade_analysis_status(self, 
                                         analysis_id: str, 
                                         status: str,
                                         progress: Optional[Dict[str, Any]] = None,
                                         results: Optional[Dict[str, Any]] = None,
                                         cost_info: Optional[Dict[str, Any]] = None,
                                         error_message: Optional[str] = None) -> bool:
        """Update trade analysis status with comprehensive data"""
        await self.ensure_initialized()
        
        updates = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        
        if progress is not None:
            updates['progress'] = progress
        if results is not None:
            updates['results'] = results
        if cost_info is not None:
            updates['cost_info'] = cost_info
        if error_message is not None:
            updates['error_message'] = error_message
        
        if status == 'completed':
            updates['completed_at'] = updates['updated_at']
        
        with logging_context(operation="update_trade_analysis_status", 
                           analysis_id=analysis_id, status=status):
            async with self.connection_manager.get_client() as client:
                with performance_logger.time_operation("supabase_update_analysis_query"):
                    response = client.table('trade_analyses').update(updates).eq(
                        'analysis_id', analysis_id
                    ).execute()
                    self._query_count += 1
                    
                    success = bool(response.data)
                    
                    # Invalidate cache
                    analysis_cache = resource_manager.get_cache("analysis")
                    if analysis_cache:
                        await analysis_cache.delete(f"analysis_{analysis_id}")
                    
                    if success:
                        logger.debug(f"Updated trade analysis {analysis_id} status to {status}")
                    else:
                        logger.error(f"Failed to update trade analysis {analysis_id}")
                    
                    return success
    
    # ===================
    # HEALTH AND MONITORING
    # ===================
    
    @profile_performance("health_check")
    @log_exceptions(logger)
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check with performance metrics"""
        try:
            await self.ensure_initialized()
            
            with performance_logger.time_operation("health_check_full"):
                # Test basic connectivity
                teams_count = len(await self.get_all_teams())
                
                # Get database statistics
                connection_stats = self.connection_manager.get_stats()
                
                return {
                    'status': 'healthy',
                    'teams_count': teams_count,
                    'query_count': self._query_count,
                    'error_count': self._error_count,
                    'connection_stats': connection_stats,
                    'cache_stats': {
                        name: cache.get_stats()
                        for name, cache in resource_manager.caches.items()
                        if name in ['teams', 'players', 'analysis']
                    },
                    'slow_queries_count': len(self.query_optimizer.slow_queries),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._error_count += 1
            return {
                'status': 'unhealthy',
                'error': str(e),
                'query_count': self._query_count,
                'error_count': self._error_count,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        return {
            'query_count': self._query_count,
            'error_count': self._error_count,
            'connection_stats': self.connection_manager.get_stats(),
            'slow_queries': self.query_optimizer.slow_queries[-10:],  # Last 10
            'cache_performance': {
                name: cache.get_stats()
                for name, cache in resource_manager.caches.items()
            }
        }


# Global service instance
optimized_supabase_service = OptimizedSupabaseService()