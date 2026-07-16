"""
Centralized error handling utilities for StadiumOS GenAI.

This module provides consistent error handling patterns across all services,
ensuring that failures are logged properly and users receive appropriate
fallback responses. The design philosophy is "fail gracefully" - no single
service failure should bring down the entire application.

Design rationale:
- Every GenAI service must have a deterministic fallback path
- Errors are logged for operators but never exposed to end users
- Safety-critical services (emergency, accessibility) never return HTTP 500
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger("stadiumos.error_handler")

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


def safe_service_call(
    fallback_response: Optional[Any] = None,
    service_name: str = "unknown_service"
) -> Callable[[F], F]:
    """
    Decorator that wraps async service functions with error handling.
    
    If the wrapped function raises any exception, it's logged and the
    fallback response is returned instead. This ensures services degrade
    gracefully rather than failing completely.
    
    Args:
        fallback_response: The response to return if the service fails.
                          If None, the exception is re-raised.
        service_name: Human-readable service name for logging
    
    Returns:
        Decorated function that handles exceptions gracefully
    
    Example:
        @safe_service_call(fallback_response=default_value, service_name="navigation")
        async def get_navigation(req: NavigationRequest) -> NavigationResponse:
            # Implementation that might fail
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{service_name} service failed: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        "service": service_name,
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    }
                )
                if fallback_response is None:
                    raise
                return fallback_response
        return wrapper  # type: ignore
    return decorator


class ServiceError(Exception):
    """
    Base exception for service-level errors.
    
    Used to distinguish between expected service errors (which should be
    handled gracefully) and unexpected system errors (which may need
    immediate attention).
    """
    def __init__(self, message: str, service_name: str, recoverable: bool = True):
        """
        Initialize a service error.
        
        Args:
            message: Human-readable error description
            service_name: Name of the service that encountered the error
            recoverable: Whether the service can continue operating with fallback
        """
        self.message = message
        self.service_name = service_name
        self.recoverable = recoverable
        super().__init__(f"[{service_name}] {message}")


class AIServiceUnavailableError(ServiceError):
    """
    Raised when the AI service is unavailable or times out.
    
    This is always recoverable because all AI-powered features have
    rule-based fallbacks. Services should catch this and use their
    deterministic logic instead.
    """
    def __init__(self, message: str = "AI service unavailable", service_name: str = "ai_service"):
        super().__init__(message, service_name, recoverable=True)


class DataValidationError(ServiceError):
    """
    Raised when input data fails validation.
    
    This is typically not recoverable within the service and should be
    propagated to the API layer to return a 400 Bad Request.
    """
    def __init__(self, message: str, service_name: str = "validation"):
        super().__init__(message, service_name, recoverable=False)


def log_and_continue(
    error: Exception,
    context: str,
    level: str = "warning"
) -> None:
    """
    Log an error and continue execution.
    
    Use this for non-critical errors where the application can continue
    operating normally, such as cache misses or optional feature failures.
    
    Args:
        error: The exception that occurred
        context: Description of what was being attempted when the error occurred
        level: Logging level (debug, info, warning, error, critical)
    
    Example:
        try:
            cache.set(key, value)
        except RedisError as e:
            log_and_continue(e, "Failed to cache navigation result", level="warning")
    """
    log_func = getattr(logger, level, logger.warning)
    log_func(
        f"{context}: {type(error).__name__}: {str(error)}",
        extra={"context": context, "error_type": type(error).__name__}
    )


def handle_optional_service(
    func: Callable[..., Any],
    *args: Any,
    default: Any = None,
    service_name: str = "optional_service",
    **kwargs: Any
) -> Any:
    """
    Call an optional service function and return a default value on failure.
    
    Use this for non-critical services where the application should continue
    even if the service fails completely.
    
    Args:
        func: The function to call
        *args: Positional arguments to pass to func
        default: Value to return if func raises an exception
        service_name: Name of the service for logging
        **kwargs: Keyword arguments to pass to func
    
    Returns:
        Result of func() or default if func raises an exception
    
    Example:
        enriched_data = handle_optional_service(
            enrich_with_analytics,
            base_data,
            default=base_data,
            service_name="analytics_enrichment"
        )
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_and_continue(e, f"{service_name} call failed", level="info")
        return default
