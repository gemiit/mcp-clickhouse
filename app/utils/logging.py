"""Logging module for MCP ClickHouse Server.

This module provides structured logging using structlog and Python's standard logging,
with optional integration with OpenTelemetry for distributed tracing.

The logging configuration is automatically loaded from the Settings system and supports:
- Console and file logging
- JSON or human-readable formatting
- OpenTelemetry integration when enabled
- Structured logging with context variables

Examples:
    Basic usage:

    >>> from app.utils.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Hello world", extra_field="value")

    With request context:

    >>> from app.utils.logging import bind_logger
    >>> logger = get_logger(__name__)
    >>> ctx_logger = bind_logger(logger, request_id="1234")
    >>> ctx_logger.info("Processing request")  # Will include request_id

    Timing operations:

    >>> from app.utils.logging import time_request
    >>> logger = get_logger(__name__)
    >>> with time_request(logger, "database query"):
    ...     # perform database operation
    ...     pass
"""

import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional, Union

import structlog
from structlog.stdlib import BoundLogger

from app.utils.config import settings

# Constants
DEFAULT_FORMAT = "%(levelname)s [%(asctime)s] %(name)s - %(message)s"
JSON_FORMAT = "%(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 10485760  # 10MB
BACKUP_COUNT = 5


def configure_logging() -> None:
    """Configure logging for the application.

    This function sets up structlog with the appropriate processors based on the
    application settings. It configures console and file handlers, and integrates
    with OpenTelemetry for distributed tracing if enabled.
    """
    log_level = settings.logging.level.value

    # Configure standard logging
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.logging.json_format:
        console_handler.setFormatter(logging.Formatter(JSON_FORMAT))
    else:
        console_handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
        )
    handlers.append(console_handler)

    # File handler if configured
    if settings.logging.log_file:
        file_path = Path(settings.logging.log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            file_path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
        )
        if settings.logging.json_format:
            file_handler.setFormatter(logging.Formatter(JSON_FORMAT))
        else:
            file_handler.setFormatter(
                logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
            )
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Configure structlog processors first
    structlog_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add output formatters based on environment and settings
    if settings.environment.value == "development" and not settings.logging.json_format:
        # Human-readable output for development
        structlog_processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        structlog_processors.append(structlog.processors.dict_tracebacks)
        structlog_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=structlog_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up OpenTelemetry integration if enabled
    if settings.tracing.enabled and settings.tracing.otlp_endpoint:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # Set up the tracer provider
            resource = Resource.create({"service.name": settings.tracing.service_name})
            tracer_provider = TracerProvider(resource=resource)

            # Set up the exporter
            otlp_exporter = OTLPSpanExporter(endpoint=settings.tracing.otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            # Set the global tracer provider
            trace.set_tracer_provider(tracer_provider)

            # Add trace context processor to structlog
            structlog_processors.append(structlog.processors.CallsiteParameterAdder())
        except ImportError:
            logging.warning(
                "OpenTelemetry packages not installed. Tracing will be disabled."
            )


def get_logger(name: str) -> BoundLogger:
    """Get a logger instance for the given name.

    Args:
        name: The name of the logger, typically __name__.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)


def bind_logger(logger: BoundLogger, **bindings: Any) -> BoundLogger:
    """Bind additional context to a logger.

    Args:
        logger: The logger to bind context to.
        **bindings: Key-value pairs to bind to the logger.

    Returns:
        A new logger with the bound context.
    """
    return logger.bind(**bindings)


def add_trace_id_to_log_context(trace_id: str) -> None:
    """Add a trace ID to the current logging context.

    This function adds a trace ID to the structlog context variables,
    which will be included in all subsequent log entries in the current context.

    Args:
        trace_id: The trace ID to add to the context.
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def add_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Add request context to the current logging context.

    Args:
        request_id: The request ID.
        user_id: The user ID.
        session_id: The session ID.
        **kwargs: Additional context variables.
    """
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    if session_id:
        context["session_id"] = session_id
    context.update(kwargs)

    structlog.contextvars.bind_contextvars(**context)


class LoggerAdapter:
    """Adapter for structlog loggers to provide a consistent interface."""

    def __init__(self, logger: BoundLogger):
        """Initialize the adapter.

        Args:
            logger: The structlog logger to adapt.
        """
        self.logger = logger

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log an info message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log a critical message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.critical(msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log an exception message.

        Args:
            msg: The message to log.
            **kwargs: Additional context variables.
        """
        self.logger.exception(msg, **kwargs)


class RequestTimer:
    """Timer for measuring request execution time."""

    def __init__(self, logger: Union[BoundLogger, LoggerAdapter], operation: str):
        """Initialize the timer.

        Args:
            logger: The logger to use.
            operation: The operation being timed.
        """
        self.logger = logger
        self.operation = operation
        self.start_time = None
        self.end_time = None

    def __enter__(self) -> "RequestTimer":
        """Start the timer.

        Returns:
            The timer instance.
        """
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop the timer and log the execution time.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000

        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                duration_ms=duration_ms,
                error=str(exc_val),
            )
        else:
            self.logger.info(
                f"{self.operation} completed",
                duration_ms=duration_ms,
            )


def time_request(
    logger: Union[BoundLogger, LoggerAdapter], operation: str
) -> RequestTimer:
    """Create a timer for measuring request execution time.

    Args:
        logger: The logger to use.
        operation: The operation being timed.

    Returns:
        A RequestTimer instance.
    """
    return RequestTimer(logger, operation)
