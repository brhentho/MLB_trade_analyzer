"""
Database Connection Pool Manager
Optimized async connection handling with PostgreSQL
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection

logger = logging.getLogger(__name__)

# Connection pool configuration
DB_POOL_MIN_SIZE = int(os.getenv('DB_POOL_MIN_SIZE', '5'))
DB_POOL_MAX_SIZE = int(os.getenv('DB_POOL_MAX_SIZE', '20'))
DB_POOL_MAX_QUERIES = int(os.getenv('DB_POOL_MAX_QUERIES', '50000'))
DB_POOL_MAX_INACTIVE_TIME = int(os.getenv('DB_POOL_MAX_INACTIVE_TIME', '300'))
DB_COMMAND_TIMEOUT = int(os.getenv('DB_COMMAND_TIMEOUT', '60'))
DB_SERVER_SETTINGS = {
    'application_name': 'baseball_trade_ai',
    'jit': 'off'  # Disable JIT for better performance on short queries
}


class DatabasePool:
    """
    Production-ready database connection pool with monitoring
    """
    
    def __init__(self):
        self.pool: Optional[Pool] = None
        self._connection_count = 0
        self._query_count = 0
        self._error_count = 0
        
    async def initialize(self, database_url: Optional[str] = None) -> bool:
        """Initialize the connection pool"""
        if not database_url:
            database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_URL')
            
        if not database_url:
            logger.error("No database URL provided")
            return False
        
        try:
            # Parse database URL
            parsed = urlparse(database_url)
            
            # For Supabase, we might need to construct the connection URL
            if 'supabase' in parsed.hostname:
                # Supabase uses connection pooling at the service level
                # Use service key for direct database access
                service_key = os.getenv('SUPABASE_SERVICE_KEY')
                if not service_key:
                    logger.error("Supabase service key required for direct database access")
                    return False
                
                # Construct PostgreSQL connection URL
                db_host = parsed.hostname.replace('supabase.co', 'supabase.co').replace('https://', '')
                db_name = 'postgres'  # Default Supabase database
                db_user = 'postgres'
                db_password = service_key
                db_port = 5432
                
                conn_kwargs = {
                    'host': db_host,
                    'port': db_port,
                    'user': db_user,
                    'password': db_password,
                    'database': db_name,
                }
            else:
                # Standard PostgreSQL URL
                conn_kwargs = {
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'user': parsed.username,
                    'password': parsed.password,
                    'database': parsed.path[1:] if parsed.path else None,
                }
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                min_size=DB_POOL_MIN_SIZE,
                max_size=DB_POOL_MAX_SIZE,
                max_queries=DB_POOL_MAX_QUERIES,
                max_inactive_connection_lifetime=DB_POOL_MAX_INACTIVE_TIME,
                command_timeout=DB_COMMAND_TIMEOUT,
                server_settings=DB_SERVER_SETTINGS,
                **conn_kwargs
            )
            
            # Test the connection
            async with self.pool.acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                if result != 1:
                    raise Exception("Connection test failed")
            
            logger.info(f"Database pool initialized: {DB_POOL_MIN_SIZE}-{DB_POOL_MAX_SIZE} connections")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            return False
    
    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        connection = None
        try:
            connection = await self.pool.acquire()
            self._connection_count += 1
            yield connection
        except Exception as e:
            self._error_count += 1
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                await self.pool.release(connection)
    
    async def execute_query(self, query: str, *args) -> list:
        """Execute a SELECT query and return results"""
        async with self.acquire() as conn:
            try:
                self._query_count += 1
                return await conn.fetch(query, *args)
            except Exception as e:
                self._error_count += 1
                logger.error(f"Query execution failed: {e}")
                raise
    
    async def execute_single(self, query: str, *args):
        """Execute a query and return a single result"""
        async with self.acquire() as conn:
            try:
                self._query_count += 1
                return await conn.fetchrow(query, *args)
            except Exception as e:
                self._error_count += 1
                logger.error(f"Single query execution failed: {e}")
                raise
    
    async def execute_scalar(self, query: str, *args):
        """Execute a query and return a single value"""
        async with self.acquire() as conn:
            try:
                self._query_count += 1
                return await conn.fetchval(query, *args)
            except Exception as e:
                self._error_count += 1
                logger.error(f"Scalar query execution failed: {e}")
                raise
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command"""
        async with self.acquire() as conn:
            try:
                self._query_count += 1
                return await conn.execute(command, *args)
            except Exception as e:
                self._error_count += 1
                logger.error(f"Command execution failed: {e}")
                raise
    
    async def execute_transaction(self, queries: list) -> list:
        """Execute multiple queries in a transaction"""
        async with self.acquire() as conn:
            try:
                async with conn.transaction():
                    results = []
                    for query, args in queries:
                        self._query_count += 1
                        if query.strip().upper().startswith('SELECT'):
                            result = await conn.fetch(query, *args)
                        else:
                            result = await conn.execute(query, *args)
                        results.append(result)
                    return results
            except Exception as e:
                self._error_count += 1
                logger.error(f"Transaction execution failed: {e}")
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.pool:
            return {'status': 'not_initialized'}
        
        return {
            'status': 'active',
            'pool_size': self.pool.get_size(),
            'pool_max_size': DB_POOL_MAX_SIZE,
            'pool_min_size': DB_POOL_MIN_SIZE,
            'connections_used': self._connection_count,
            'queries_executed': self._query_count,
            'errors_encountered': self._error_count,
            'idle_connections': self.pool.get_idle_size(),
            'max_queries_per_connection': DB_POOL_MAX_QUERIES
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the database pool"""
        if not self.pool:
            return {'status': 'unhealthy', 'error': 'Pool not initialized'}
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Test basic connectivity
            async with self.acquire() as conn:
                await conn.fetchval('SELECT 1')
            
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'pool_stats': self.get_stats()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'pool_stats': self.get_stats()
            }


# Optimized query templates for common operations
class OptimizedQueries:
    """Pre-compiled query templates for better performance"""
    
    # Team queries
    GET_ALL_TEAMS = """
        SELECT id, team_key, name, abbreviation, city, division, league,
               budget_level, competitive_window, market_size, philosophy,
               payroll_budget, luxury_tax_threshold
        FROM teams 
        WHERE active = true 
        ORDER BY league, division, name
    """
    
    GET_TEAM_BY_KEY = """
        SELECT * FROM teams 
        WHERE team_key = $1 AND active = true
    """
    
    # Player queries with joins
    GET_TEAM_ROSTER = """
        SELECT 
            p.id, p.name, p.position, p.age, p.jersey_number, p.status,
            c.salary, c.years_remaining, c.has_no_trade_clause,
            sc.war, sc.batting_avg, sc.era, sc.ops
        FROM players p
        LEFT JOIN contracts c ON p.id = c.player_id AND c.season = $2
        LEFT JOIN stats_cache sc ON p.id = sc.player_id AND sc.season = $2
        WHERE p.team_id = $1 AND p.active = true
        ORDER BY p.position, p.jersey_number
    """
    
    SEARCH_PLAYERS = """
        SELECT 
            p.id, p.name, p.position, p.age, p.team_id,
            t.team_key, t.name as team_name,
            c.salary, sc.war
        FROM players p
        JOIN teams t ON p.team_id = t.id
        LEFT JOIN contracts c ON p.id = c.player_id AND c.season = $2
        LEFT JOIN stats_cache sc ON p.id = sc.player_id AND sc.season = $2
        WHERE p.name ILIKE $1 AND p.active = true
        ORDER BY sc.war DESC NULLS LAST
        LIMIT $3
    """
    
    # Trade analysis queries
    GET_TRADE_ANALYSIS = """
        SELECT 
            analysis_id, requesting_team_id, request_text, urgency, status,
            progress, results, cost_info, error_message,
            created_at, started_at, completed_at
        FROM trade_analyses 
        WHERE analysis_id = $1
    """
    
    GET_RECENT_ANALYSES = """
        SELECT 
            ta.analysis_id, ta.requesting_team_id, ta.request_text, 
            ta.urgency, ta.status, ta.created_at, ta.completed_at,
            t.team_key, t.name as team_name
        FROM trade_analyses ta
        JOIN teams t ON ta.requesting_team_id = t.id
        WHERE ($1 IS NULL OR ta.requesting_team_id = $1)
        AND ($2 IS NULL OR ta.status = $2)
        ORDER BY ta.created_at DESC
        LIMIT $3
    """
    
    # Materialized view queries
    GET_TEAM_STATS_SUMMARY = """
        SELECT * FROM team_stats_summary
        WHERE team_id = $1
    """
    
    GET_PLAYER_RANKINGS = """
        SELECT * FROM player_rankings
        WHERE position = $1
        ORDER BY position_war_rank
        LIMIT $2
    """


# Global database pool instance
db_pool = DatabasePool()


async def initialize_db_pool(database_url: Optional[str] = None) -> bool:
    """Initialize the global database pool"""
    return await db_pool.initialize(database_url)


async def close_db_pool():
    """Close the global database pool"""
    await db_pool.close()


@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the global pool"""
    async with db_pool.acquire() as conn:
        yield conn