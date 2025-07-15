"""Configuration module for MCP ClickHouse Server.

This module provides a unified settings interface for the application, supporting
environment variables, .env files, and configuration validation using Pydantic.

Examples:
    Basic usage:

    >>> from app.utils.config import settings
    >>> print(settings.app_name)
    >>> print(settings.clickhouse.host)

    Environment variables take precedence over .env file values:

    >>> # In .env: APP_NAME=local-server
    >>> # Export: export APP_NAME=prod-server
    >>> print(settings.app_name)  # Will print "prod-server"
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    Field,
    SecretStr,
)
from pydantic_settings import BaseSettings

# Load .env file if it exists
load_dotenv()


class LogLevel(str, Enum):
    """Log levels supported by the application."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ClickHouseSettings(BaseSettings):
    """ClickHouse connection settings."""

    host: str = Field(
        default="localhost",
        description="ClickHouse server hostname",
        alias="CH_HOST",
    )
    port: int = Field(
        default=9000,
        description="ClickHouse server port",
        alias="CH_PORT",
    )
    user: str = Field(
        default="default",
        description="ClickHouse username",
        alias="CH_USER",
    )
    password: SecretStr = Field(
        default=SecretStr(""),
        description="ClickHouse password",
        alias="CH_PASSWORD",
    )
    database: str = Field(
        default="default",
        description="ClickHouse default database",
        alias="CH_DATABASE",
    )
    secure: bool = Field(
        default=False,
        description="Use TLS for ClickHouse connection",
        alias="CH_SECURE",
    )
    verify: bool = Field(
        default=True,
        description="Verify TLS certificate",
        alias="CH_VERIFY",
    )
    ca_cert: Optional[Path] = Field(
        default=None,
        description="Path to CA certificate for ClickHouse connection",
        alias="CH_CA_CERT",
    )
    client_cert: Optional[Path] = Field(
        default=None,
        description="Path to client certificate for ClickHouse connection",
        alias="CH_CLIENT_CERT",
    )
    client_key: Optional[Path] = Field(
        default=None,
        description="Path to client key for ClickHouse connection",
        alias="CH_CLIENT_KEY",
    )
    connect_timeout: int = Field(
        default=10,
        description="Connection timeout in seconds",
        alias="CH_CONNECT_TIMEOUT",
    )
    query_timeout: int = Field(
        default=60,
        description="Query execution timeout in seconds",
        alias="CH_QUERY_TIMEOUT",
    )
    compression: bool = Field(
        default=True,
        description="Enable compression for ClickHouse connection",
        alias="CH_COMPRESSION",
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Log level",
        alias="LOG_LEVEL",
    )
    json_format: bool = Field(
        default=True,
        description="Use JSON logging format",
        alias="LOG_JSON",
    )
    log_file: Optional[Path] = Field(
        default=None,
        description="Path to log file",
        alias="LOG_FILE",
    )


class MetricsSettings(BaseSettings):
    """Metrics configuration."""

    enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
        alias="METRICS_ENABLED",
    )
    path: str = Field(
        default="/metrics",
        description="Metrics endpoint path",
        alias="METRICS_PATH",
    )


class TracingSettings(BaseSettings):
    """OpenTelemetry tracing configuration."""

    enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing",
        alias="TRACING_ENABLED",
    )
    otlp_endpoint: Optional[str] = Field(
        default=None,
        description="OTLP collector endpoint",
        alias="OTLP_ENDPOINT",
    )
    service_name: str = Field(
        default="mcp-clickhouse-server",
        description="Service name for tracing",
        alias="TRACING_SERVICE_NAME",
    )


class Settings(BaseSettings):
    """Main application settings."""

    # Application settings
    app_name: str = Field(
        default="mcp-clickhouse-server",
        description="Application name",
        alias="APP_NAME",
    )
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment",
        alias="ENVIRONMENT",
    )

    # Component settings
    clickhouse: ClickHouseSettings = ClickHouseSettings()
    logging: LoggingSettings = LoggingSettings()
    metrics: MetricsSettings = MetricsSettings()
    tracing: TracingSettings = TracingSettings()

    # Additional settings
    temp_dir: Path = Field(
        default=Path("/tmp/mcp-clickhouse"),
        description="Temporary directory",
        alias="TEMP_DIR",
    )
    max_upload_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum upload size in bytes",
        alias="MAX_UPLOAD_SIZE",
    )

    # Pydantic v2 style model configuration
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Allow extra fields from environment variables
    }


# Create global settings instance
settings = Settings()
