"""
Audit logging service for security, compliance, and operational monitoring.

Tracks critical user actions and system events:
- Admin operations (cache flush, configuration changes)
- AI prompt requests (for safety monitoring)
- User authentication attempts
- Incident reports
- Volunteer actions
- Emergency responses

Logs are structured JSON for easy parsing by SIEM systems.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger("stadiumos.audit")
settings = get_settings()


class AuditEventType(str, Enum):
    """Types of auditable events."""
    
    # Authentication & Authorization
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    AUTH_FAILURE = "auth_failure"
    
    # AI Operations
    AI_PROMPT = "ai_prompt"
    AI_RESPONSE_CACHED = "ai_response_cached"
    AI_FALLBACK_USED = "ai_fallback_used"
    
    # Admin Operations
    CACHE_FLUSH = "cache_flush"
    CONFIG_CHANGE = "config_change"
    SYSTEM_STATUS_CHECK = "system_status_check"
    
    # User Actions
    NAVIGATION_REQUEST = "navigation_request"
    CHAT_REQUEST = "chat_request"
    INCIDENT_REPORT = "incident_report"
    EMERGENCY_REQUEST = "emergency_request"
    ACCESSIBILITY_REQUEST = "accessibility_request"
    
    # Volunteer/Staff Actions
    VOLUNTEER_ACTION = "volunteer_action"
    CROWD_ANALYSIS = "crowd_analysis"
    TRANSPORT_UPDATE = "transport_update"
    
    # System Events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ERROR = "error"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Centralized audit logging with structured JSON output.
    
    Logs to both application logger and separate audit log file for compliance.
    """
    
    def __init__(self):
        # Create separate audit logger
        self.audit_logger = logging.getLogger("stadiumos.audit.events")
        self.audit_logger.setLevel(logging.INFO)
        
        # Ensure we have a file handler for audit logs
        if not self.audit_logger.handlers:
            # In production, configure file handler via logging config
            # For now, logs go to stdout/stderr
            pass
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        """
        Log an audit event with structured data.
        
        Args:
            event_type: Type of event being logged
            severity: Severity level of the event
            user_id: ID of the user performing the action (if applicable)
            ip_address: IP address of the requester
            details: Additional context about the event
            success: Whether the action succeeded
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "success": success,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address or "unknown",
            "environment": settings.environment,
            "details": details or {},
        }
        
        # Log as structured JSON
        log_message = json.dumps(audit_entry, default=str)
        
        # Route to appropriate log level
        if severity == AuditSeverity.CRITICAL:
            self.audit_logger.critical(log_message)
        elif severity == AuditSeverity.ERROR:
            self.audit_logger.error(log_message)
        elif severity == AuditSeverity.WARNING:
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)
    
    def log_admin_action(
        self,
        action: str,
        admin_key_hash: str,
        ip_address: str,
        details: Optional[dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        """Log an administrative action."""
        self.log_event(
            event_type=AuditEventType.ADMIN_LOGIN if "login" in action.lower() else AuditEventType.CONFIG_CHANGE,
            severity=AuditSeverity.WARNING if not success else AuditSeverity.INFO,
            user_id=f"admin_{admin_key_hash[:8]}",
            ip_address=ip_address,
            details={"action": action, **(details or {})},
            success=success,
        )
    
    def log_ai_prompt(
        self,
        prompt_preview: str,
        user_role: str,
        language: str,
        ip_address: str,
        cached: bool = False,
        success: bool = True,
    ) -> None:
        """Log an AI prompt for safety monitoring and compliance."""
        # Only log first 200 chars of prompt for privacy
        safe_preview = prompt_preview[:200] + "..." if len(prompt_preview) > 200 else prompt_preview
        
        self.log_event(
            event_type=AuditEventType.AI_RESPONSE_CACHED if cached else AuditEventType.AI_PROMPT,
            severity=AuditSeverity.INFO,
            details={
                "prompt_preview": safe_preview,
                "user_role": user_role,
                "language": language,
                "cached": cached,
            },
            ip_address=ip_address,
            success=success,
        )
    
    def log_incident_report(
        self,
        incident_type: str,
        severity: str,
        location: str,
        reporter_ip: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log an incident report for security tracking."""
        self.log_event(
            event_type=AuditEventType.INCIDENT_REPORT,
            severity=AuditSeverity.WARNING if severity in ["high", "critical"] else AuditSeverity.INFO,
            ip_address=reporter_ip,
            details={
                "incident_type": incident_type,
                "severity": severity,
                "location": location,
                **(details or {}),
            },
            success=True,
        )
    
    def log_emergency_request(
        self,
        incident_type: str,
        severity: str,
        affected_zones: list[str],
        ip_address: str,
        escalated: bool = False,
    ) -> None:
        """Log an emergency request for critical incident tracking."""
        self.log_event(
            event_type=AuditEventType.EMERGENCY_REQUEST,
            severity=AuditSeverity.CRITICAL if severity == "high" else AuditSeverity.WARNING,
            ip_address=ip_address,
            details={
                "incident_type": incident_type,
                "severity": severity,
                "affected_zones": affected_zones,
                "escalated": escalated,
            },
            success=True,
        )
    
    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        endpoint: str,
        request_count: int,
    ) -> None:
        """Log rate limit violations for security monitoring."""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            ip_address=ip_address,
            details={
                "endpoint": endpoint,
                "request_count": request_count,
                "limit": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window_seconds,
            },
            success=False,
        )
    
    def log_auth_failure(
        self,
        reason: str,
        ip_address: str,
        attempted_endpoint: str,
    ) -> None:
        """Log authentication failures for security monitoring."""
        self.log_event(
            event_type=AuditEventType.AUTH_FAILURE,
            severity=AuditSeverity.WARNING,
            ip_address=ip_address,
            details={
                "reason": reason,
                "endpoint": attempted_endpoint,
            },
            success=False,
        )
    
    def log_crowd_analysis(
        self,
        zones_analyzed: list[str],
        alerts_generated: int,
        operator_ip: str,
    ) -> None:
        """Log crowd analysis operations for operational tracking."""
        self.log_event(
            event_type=AuditEventType.CROWD_ANALYSIS,
            severity=AuditSeverity.WARNING if alerts_generated > 0 else AuditSeverity.INFO,
            ip_address=operator_ip,
            details={
                "zones_analyzed": zones_analyzed,
                "alerts_generated": alerts_generated,
            },
            success=True,
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        endpoint: str,
        ip_address: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """Log application errors for debugging and monitoring."""
        self.log_event(
            event_type=AuditEventType.ERROR,
            severity=AuditSeverity.ERROR,
            ip_address=ip_address,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "endpoint": endpoint,
                "stack_trace": stack_trace[:500] if stack_trace else None,  # Truncate long traces
            },
            success=False,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Convenience functions for common audit operations
def log_admin_action(action: str, admin_key_hash: str, ip_address: str, **kwargs):
    """Convenience function to log admin actions."""
    get_audit_logger().log_admin_action(action, admin_key_hash, ip_address, **kwargs)


def log_ai_prompt(prompt_preview: str, user_role: str, language: str, ip_address: str, **kwargs):
    """Convenience function to log AI prompts."""
    get_audit_logger().log_ai_prompt(prompt_preview, user_role, language, ip_address, **kwargs)


def log_incident_report(incident_type: str, severity: str, location: str, reporter_ip: str, **kwargs):
    """Convenience function to log incident reports."""
    get_audit_logger().log_incident_report(incident_type, severity, location, reporter_ip, **kwargs)


def log_emergency_request(incident_type: str, severity: str, affected_zones: list[str], ip_address: str, **kwargs):
    """Convenience function to log emergency requests."""
    get_audit_logger().log_emergency_request(incident_type, severity, affected_zones, ip_address, **kwargs)


def log_rate_limit_exceeded(ip_address: str, endpoint: str, request_count: int):
    """Convenience function to log rate limit violations."""
    get_audit_logger().log_rate_limit_exceeded(ip_address, endpoint, request_count)


def log_auth_failure(reason: str, ip_address: str, attempted_endpoint: str):
    """Convenience function to log auth failures."""
    get_audit_logger().log_auth_failure(reason, ip_address, attempted_endpoint)
