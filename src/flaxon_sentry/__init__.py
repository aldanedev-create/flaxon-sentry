"""Flaxon Sentry Plugin - Error tracking and performance monitoring."""

from .plugin import SentryPlugin
from .config import SentryConfig

__all__ = [
    "SentryPlugin",
    "SentryConfig",
]

__version__ = "0.1.0"