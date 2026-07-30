"""Tests for SentryPlugin."""

import pytest
from flaxon import Flaxon
from flaxon_sentry import SentryPlugin
from flaxon_sentry.config import SentryConfig


def test_plugin_initialization():
    """Test basic plugin initialization."""
    plugin = SentryPlugin(dsn="https://test@sentry.io/1")
    assert plugin.config.dsn == "https://test@sentry.io/1"
    assert plugin.is_enabled is True


def test_plugin_disabled():
    """Test plugin with empty DSN raises error."""
    with pytest.raises(ValueError):
        SentryPlugin(dsn="")


def test_plugin_from_config():
    """Test creating plugin from Flaxon config."""
    app = Flaxon("test-app", config={"SENTRY_DSN": "https://test@sentry.io/1"})
    plugin = SentryPlugin.from_config(app.config)
    assert plugin.config.dsn == "https://test@sentry.io/1"
    assert plugin.config.default_tags.get("framework") == "Flaxon"


def test_plugin_has_hooks():
    """Test plugin has required lifecycle hooks."""
    plugin = SentryPlugin(dsn="https://test@sentry.io/1")
    
    assert hasattr(plugin, "on_startup")
    assert hasattr(plugin, "on_shutdown")
    assert hasattr(plugin, "add_middleware")


def test_plugin_user_getter():
    """Test setting user getter."""
    plugin = SentryPlugin(dsn="https://test@sentry.io/1")
    
    def get_user(request):
        return {"id": 1, "username": "testuser"}
    
    plugin.set_user_getter(get_user)
    assert plugin._user_getter is get_user


def test_config_validation():
    """Test config validation."""
    # Valid config
    config = SentryConfig(dsn="https://test@sentry.io/1")
    config.validate()  # Should not raise
    
    # Invalid DSN
    with pytest.raises(ValueError):
        config = SentryConfig(dsn="invalid-dsn")
        config.validate()
    
    # Invalid sample rate
    with pytest.raises(ValueError):
        config = SentryConfig(dsn="https://test@sentry.io/1", sample_rate=1.5)
        config.validate()


def test_ignore_exceptions():
    """Test exception filtering."""
    plugin = SentryPlugin(
        dsn="https://test@sentry.io/1",
        ignore_exceptions=["ValidationError", "NotFoundError"],
    )
    
    class ValidationError(Exception):
        pass
    
    class NotFoundError(Exception):
        pass
    
    class DatabaseError(Exception):
        pass
    
    # Should ignore ValidationError and NotFoundError
    assert plugin._should_ignore_exception(ValidationError()) is True
    assert plugin._should_ignore_exception(NotFoundError()) is True
    
    # Should not ignore DatabaseError
    assert plugin._should_ignore_exception(DatabaseError()) is False