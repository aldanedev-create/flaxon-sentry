"""Build Sentry context from Flaxon request objects."""

from typing import Dict, Any, Optional, Callable
from flaxon.http import Request


def build_request_context(request: Request) -> Dict[str, Any]:
    """Build Sentry context from a Flaxon Request object."""
    context = {
        "method": request.method,
        "path": request.path,
        "url": str(request.url),
        "query": dict(request.query_params),
        "client": {
            "ip": request.client[0] if request.client else None,
            "port": request.client[1] if request.client else None,
        },
    }
    
    headers = dict(request.headers)
    sensitive_headers = {
        "authorization", "cookie", "x-api-key", "x-auth-token",
        "proxy-authorization", "www-authenticate", "x-forwarded-for",
    }
    context["headers"] = {
        k: "[REDACTED]" if k.lower() in sensitive_headers else v
        for k, v in headers.items()
    }
    
    if hasattr(request, "state") and hasattr(request.state, "request_id"):
        context["request_id"] = request.state.request_id
    
    return context


def build_user_context(request: Request, user_getter: Optional[Callable] = None) -> Dict[str, Any]:
    """Build Sentry user context from a Flaxon Request object."""
    if not user_getter:
        return {}
    
    try:
        user_data = user_getter(request)
        if isinstance(user_data, dict):
            user_context = {
                "id": user_data.get("id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "ip_address": request.client[0] if request.client else None,
            }
            return {k: v for k, v in user_context.items() if v is not None}
    except Exception:
        pass
    
    return {}


def build_validation_context(validation_errors: Dict[str, Any]) -> Dict[str, Any]:
    """Build Sentry context from validation errors."""
    return {
        "validation_errors": validation_errors,
        "error_count": len(validation_errors),
    }


def build_route_context(route_name: str, route_params: Dict[str, Any]) -> Dict[str, Any]:
    """Build Sentry context from route information."""
    return {
        "route_name": route_name,
        "route_params": route_params,
    }