"""
Baseball Trade AI - API v1
Production-ready API with proper architecture patterns
"""

from .routers.trades import router as trades_router
from .routers.teams import router as teams_router
from .routers.players import router as players_router
from .routers.health import router as health_router

__version__ = "1.0.0"

__all__ = [
    "trades_router",
    "teams_router", 
    "players_router",
    "health_router"
]