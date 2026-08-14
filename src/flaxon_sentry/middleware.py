"""Sentry ASGI middleware for Flaxon."""

import sentry_sdk
from typing import Callable


class SentryMiddleware:
    """ASGI middleware that captures request context and performance data."""
    
    def __init__(self, app: Callable, plugin_instance):
        self.app = app
        self.plugin = plugin_instance
        self.config = plugin_instance.config
    
    async def __call__(self, scope, receive, send):
        """ASGI callable with Sentry instrumentation."""
        if scope.get("type") != "http" or not self.plugin.is_enabled:
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        transaction_name = f"{method} {path}"
        
        status_code = 500  # Default fallback if request crashes
        
        async def wrapped_send(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)
        
        with sentry_sdk.isolation_scope():
            with sentry_sdk.start_transaction(
                name=transaction_name,
                op="http.server",
                sampled=self.config.traces_sample_rate,
            ):
                request = scope.get("flaxon_request")
                
                if self.config.attach_request_context and request:
                    from .context import build_request_context
                    sentry_sdk.set_context("request", build_request_context(request))
                
                if "flaxon_route" in scope:
                    sentry_sdk.set_tag("route", scope["flaxon_route"])
                
                sentry_sdk.set_tag("http.method", method)
                
                for key, value in self.config.default_tags.items():
                    sentry_sdk.set_tag(key, value)
                
                sentry_sdk.add_breadcrumb(
                    category="http",
                    message=f"{method} {path}",
                    level="info",
                    data={"method": method, "path": path}
                )
                
                try:
                    await self.app(scope, receive, wrapped_send)
                    sentry_sdk.set_tag("http.status_code", status_code)
                except Exception as e:
                    sentry_sdk.set_tag("http.status_code", 500)
                    self.plugin.capture_exception(e, request)
                    raise