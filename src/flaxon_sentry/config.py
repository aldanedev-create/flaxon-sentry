"""Sentry plugin configuration."""

from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
import os


@dataclass
class SentryConfig:
    """Configuration for Sentry integration."""
    
    # Required
    dsn: str
    
    # Environment
    environment: Optional[str] = None
    release: Optional[str] = None
    debug: bool = False
    
    # Sampling
    sample_rate: float = 1.0
    traces_sample_rate: float = 0.1  # Performance monitoring
    
    # Request/response capture
    send_default_pii: bool = False
    max_request_body_size: str = "medium"  # "never", "small", "medium", "always"
    
    # Filtering
    ignore_exceptions: List[str] = field(default_factory=list)
    ignore_status_codes: List[int] = field(default_factory=lambda: [404, 401, 403])
    
    # Tags
    default_tags: Dict[str, Any] = field(default_factory=dict)
    
    # Integration-specific
    attach_request_context: bool = True
    attach_validation_errors: bool = True
    attach_route_params: bool = True
    
    # Custom callbacks
    before_send: Optional[Callable] = None
    before_send_transaction: Optional[Callable] = None
    
    @classmethod
    def from_env(cls, prefix: str = "SENTRY_") -> "SentryConfig":
        """Load configuration from environment variables."""
        return cls(
            dsn=os.environ.get(f"{prefix}DSN", ""),
            environment=os.environ.get(f"{prefix}ENVIRONMENT"),
            release=os.environ.get(f"{prefix}RELEASE"),
            debug=os.environ.get(f"{prefix}DEBUG", "").lower() == "true",
            sample_rate=float(os.environ.get(f"{prefix}SAMPLE_RATE", "1.0")),
            traces_sample_rate=float(os.environ.get(f"{prefix}TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=os.environ.get(f"{prefix}SEND_DEFAULT_PII", "").lower() == "true",
            max_request_body_size=os.environ.get(f"{prefix}MAX_REQUEST_BODY_SIZE", "medium"),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.dsn:
            raise ValueError(
                "Sentry DSN is required. Set SENTRY_DSN environment variable "
                "or pass dsn to SentryPlugin."
            )
        
        if not self.dsn.startswith(("http://", "https://")):
            raise ValueError("Invalid Sentry DSN format. Must start with http:// or https://")
        
        if not (0.0 <= self.sample_rate <= 1.0):
            raise ValueError("sample_rate must be between 0.0 and 1.0")
        
        if not (0.0 <= self.traces_sample_rate <= 1.0):
            raise ValueError("traces_sample_rate must be between 0.0 and 1.0")