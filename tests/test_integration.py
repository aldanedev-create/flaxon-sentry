"""Integration tests for SentryPlugin with Flaxon app."""

import pytest
from flaxon import Flaxon
from flaxon_sentry import SentryPlugin


@pytest.mark.asyncio
async def test_plugin_loads():
    """Test that plugin loads successfully."""
    app = Flaxon("test-app")
    plugin = SentryPlugin(dsn="https://test@sentry.io/1")
    
    # Simulate loading plugin
    app.state.sentry_plugin = plugin
    await plugin.on_startup(app)
    
    assert hasattr(app.state, "sentry_plugin")
    assert app.state.sentry_plugin is plugin
    
    await plugin.on_shutdown(app)


@pytest.mark.asyncio
async def test_plugin_middleware():
    """Test that plugin adds middleware."""
    app = Flaxon("test-app")
    plugin = SentryPlugin(dsn="https://test@sentry.io/1")
    
    middleware = plugin.add_middleware(app)
    assert middleware is not None
    assert hasattr(middleware, "__call__")


def test_plugin_from_config_integration():
    """Test creating plugin from config and loading."""
    app = Flaxon(
        "test-app",
        config={
            "SENTRY_DSN": "https://test@sentry.io/1",
            "ENV": "testing",
            "VERSION": "1.0.0",
        }
    )
    
    plugin = SentryPlugin.from_config(app.config)
    assert plugin.config.dsn == "https://test@sentry.io/1"
    assert plugin.config.environment == "testing"
    assert plugin.config.release == "1.0.0"


@pytest.mark.asyncio
async def test_plugin_context():
    """Test plugin context functions."""
    from flaxon.http import Request
    from flaxon_sentry.context import build_request_context, build_user_context
    
    # Create a mock request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [(b"host", b"example.com")],
        "client": ("127.0.0.1", 8000),
    }
    request = Request(scope, None, None)
    
    # Test request context
    context = build_request_context(request)
    assert context["method"] == "GET"
    assert context["path"] == "/test"
    assert "headers" in context
    
    # Test user context
    def get_user(req):
        return {"id": 1, "username": "test"}
    
    user_context = build_user_context(request, get_user)
    assert user_context.get("id") == 1
    assert user_context.get("username") == "test"