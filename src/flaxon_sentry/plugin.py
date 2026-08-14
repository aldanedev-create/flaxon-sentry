"""Sentry plugin for Flaxon."""

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from typing import Optional, Dict, Any, Callable, List
from flaxon.plugins import Plugin

from .config import SentryConfig
from .middleware import SentryMiddleware
from .context import (
    build_request_context, 
    build_user_context, 
    build_validation_context,
)


class SentryPlugin(Plugin):
    """
    Sentry error tracking and performance monitoring plugin for Flaxon.
    """
    
    name = "sentry"
    version = "0.1.0"
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: Optional[str] = None,
        release: Optional[str] = None,
        debug: bool = False,
        sample_rate: float = 1.0,
        traces_sample_rate: float = 0.1,
        send_default_pii: bool = False,
        max_request_body_size: str = "medium",
        ignore_exceptions: Optional[List[str]] = None,
        ignore_status_codes: Optional[List[int]] = None,
        default_tags: Optional[Dict[str, Any]] = None,
        attach_request_context: bool = True,
        attach_validation_errors: bool = True,
        attach_route_params: bool = True,
        before_send: Optional[Callable] = None,
        before_send_transaction: Optional[Callable] = None,
        config: Optional[SentryConfig] = None,
    ):
        self.config = config or SentryConfig(
            dsn=dsn or "",
            environment=environment,
            release=release,
            debug=debug,
            sample_rate=sample_rate,
            traces_sample_rate=traces_sample_rate,
            send_default_pii=send_default_pii,
            max_request_body_size=max_request_body_size,
            ignore_exceptions=ignore_exceptions or [],
            ignore_status_codes=ignore_status_codes or [404, 401, 403],
            default_tags=default_tags or {},
            attach_request_context=attach_request_context,
            attach_validation_errors=attach_validation_errors,
            attach_route_params=attach_route_params,
            before_send=before_send,
            before_send_transaction=before_send_transaction,
        )
        
        self._user_getter = None
        self._app = None
        
        # Validate config
        self.config.validate()
    
    @classmethod
    def from_config(cls, config: dict) -> "SentryPlugin":
        """Create SentryPlugin from Flaxon config dict."""
        sentry_dsn = config.get("SENTRY_DSN", config.get("sentry_dsn", ""))
        sentry_env = config.get("ENV", config.get("SENTRY_ENVIRONMENT", ""))
        sentry_release = config.get("VERSION", config.get("SENTRY_RELEASE", ""))
        sentry_debug = config.get("SENTRY_DEBUG", False)
        
        return cls(
            dsn=sentry_dsn,
            environment=sentry_env,
            release=sentry_release,
            debug=sentry_debug,
            default_tags={"framework": "Flaxon"},
        )
    
    def set_user_getter(self, user_getter: Callable) -> None:
        """Set a function that extracts user info from request."""
        self._user_getter = user_getter
    
    def setup(self, app) -> None:
        """Setup: store app reference, initialize Sentry SDK, register middleware."""
        self._app = app

        if self.is_enabled:
            sentry_sdk.init(
                dsn=self.config.dsn,
                environment=self.config.environment,
                release=self.config.release,
                debug=self.config.debug,
                sample_rate=self.config.sample_rate,
                traces_sample_rate=self.config.traces_sample_rate,
                send_default_pii=self.config.send_default_pii,
                max_request_body_size=self.config.max_request_body_size,
                before_send=self.config.before_send,
                before_send_transaction=self.config.before_send_transaction,
                integrations=[
                    LoggingIntegration(
                        level=None,
                        event_level=None,
                    ),
                    ThreadingIntegration(),
                ],
            )

            for key, value in self.config.default_tags.items():
                sentry_sdk.set_tag(key, value)

            sentry_sdk.set_tag("framework", "Flaxon")
            sentry_sdk.set_tag("framework_version", getattr(app, "version", "0.1.0"))

        app.state.sentry_plugin = self
        app.add_middleware(SentryMiddleware, plugin_instance=self)

    def on_shutdown(self) -> None:
        """Shutdown: flush pending events."""
        if self.is_enabled:
            sentry_sdk.flush(timeout=2.0)
    
    def capture_exception(
        self, 
        error: Exception, 
        request=None, 
        validation_errors: Optional[Dict] = None,
        **kwargs
    ) -> None:
        """Manually capture an exception and send to Sentry."""
        if not self.is_enabled or self._should_ignore_exception(error):
            return
        
        with sentry_sdk.isolation_scope():
            if request and self.config.attach_request_context:
                sentry_sdk.set_context("request", build_request_context(request))
                
                if self._user_getter:
                    user_context = build_user_context(request, self._user_getter)
                    if user_context:
                        sentry_sdk.set_user(user_context)
            
            if validation_errors and self.config.attach_validation_errors:
                sentry_sdk.set_context("validation", build_validation_context(validation_errors))
                
            sentry_sdk.capture_exception(error)
    
    def add_breadcrumb(
        self, 
        message: str, 
        category: str = "default", 
        level: str = "info", 
        data: Optional[Dict] = None
    ) -> None:
        """Add a breadcrumb to the current transaction."""
        sentry_sdk.add_breadcrumb(
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
    
    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag on the current scope."""
        sentry_sdk.set_tag(key, value)
    
    def set_context(self, key: str, value: Dict[str, Any]) -> None:
        """Set context on the current scope."""
        sentry_sdk.set_context(key, value)
    
    def _should_ignore_exception(self, error: Exception) -> bool:
        """Check if an exception should be ignored."""
        error_class = error.__class__.__name__
        for pattern in self.config.ignore_exceptions:
            if pattern in error_class or error_class.startswith(pattern):
                return True
        return False
    
    @property
    def is_enabled(self) -> bool:
        """Check if Sentry is enabled."""
        return bool(self.config.dsn) and self.config.sample_rate > 0