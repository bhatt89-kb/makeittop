from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.security import require_admin_key
from app.services.ai_service import is_ai_available
from app.services.cache import get_cache_stats, is_cache_available, flush_cache

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])
settings = get_settings()


@router.get("/status")
async def status():
    """Operator-only deployment status check (requires X-Admin-Key header)."""
    cache_stats = await get_cache_stats()
    
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "genai_available": is_ai_available(),
        "cache_available": is_cache_available(),
        "cache_stats": cache_stats,
        "rate_limit": f"{settings.rate_limit_requests} req / {settings.rate_limit_window_seconds}s",
    }


@router.get("/cache/stats")
async def cache_stats():
    """Get detailed cache statistics (requires X-Admin-Key header)."""
    stats = await get_cache_stats()
    return {
        "cache": stats,
        "recommendation": "Consider increasing cache TTL if hit rate < 70%" if stats.get("hit_rate", 100) < 70 else "Cache performance is healthy"
    }


@router.post("/cache/flush")
async def flush_cache_endpoint(pattern: str = "*"):
    """
    Flush cache entries matching pattern (requires X-Admin-Key header).
    
    WARNING: Use with caution in production.
    Examples:
    - pattern="*" flushes all cache
    - pattern="ai_response:*" flushes only AI responses
    - pattern="navigation:*" flushes only navigation routes
    """
    deleted_count = await flush_cache(pattern)
    return {
        "flushed": deleted_count,
        "pattern": pattern,
        "message": f"Successfully flushed {deleted_count} cache entries"
    }
