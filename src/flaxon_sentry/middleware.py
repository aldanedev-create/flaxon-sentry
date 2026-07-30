"""Sentry ASGI middleware for Flaxon."""

import asyncio
from typing import Optional, Dict, Any, Callable
from sentry_sdk import Hub, start_transaction, configure_scope, add_breadcrumb
from sentry_sdk.tracing import Transaction

from flaxon.http import Request


class SentryMiddleware:
    """
    ASGI middleware that captures request context and performance data.
    
    This wraps the ASGI app and adds Sentry instrumentation with Flaxon-specific
    context (request ID, route, validation errors, etc.).
    """
    
    def __init__(
        self,
        app: Callable,
        plugin_instance,  # SentryPlugin instance
    ):
        self.app = app
        self.plugin = plugin_instance
        self.config = plugin_instance.config
    
    async def __call__(self, scope, receive, send):
        """ASGI callable with Sentry instrumentation."""
        
        # Only instrument HTTP requests (WebSocket handled separately)
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        
        # Get path from scope
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        
        # Start transaction for performance tracking
        transaction_name = f"{method} {path}"
        
        with start_transaction(
            name=transaction_name,
            op="http.server",
            sampled=self.config.traces_sample_rate,
        ) as transaction:
            
            # Create Flaxon Request for context building
            # Note: We need a proper Request object - this is simplified
            request = None
            
            # Try to get request from scope state if available
            if "flaxon_request" in scope:
                request = scope["flaxon_request"]
            
            # Set request context
            if self.config.attach_request_context:
                with configure_scope() as sentry_scope:
                    if request:
                        from .context import build_request_context
                        sentry_scope.set_context("request", build_request_context(request))
                    
                    # Set route tags
                    if "flaxon_route" in scope:
                        sentry_scope.set_tag("route", scope["flaxon_route"])
                    
                    # Set method tag
                    sentry_scope.set_tag("http.method", method)
                    
                    # Add default tags
                    for key, value in self.config.default_tags.items():
                        sentry_scope.set_tag(key, value)
            
            # Add breadcrumb
            add_breadcrumb(
                category="http",
                message=f"{method} {path}",
                level="info",
                data={
                    "method": method,
                    "path": path,
                }
            )
            
            # Execute the app
            try:
                await self.app(scope, receive, send)
                
                # Transaction automatically finishes
            except Exception as e:
                # Capture the exception
                self.plugin.capture_exception(e, request)
                raise