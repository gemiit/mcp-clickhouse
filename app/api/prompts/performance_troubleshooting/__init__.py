"""
Performance Troubleshooting Prompts Package

Provides registration for ClickHouse performance troubleshooting prompt handlers in both Chinese and English.
Enables modular support for diagnosing and resolving performance issues.
"""

from .performance_troubleshooting import register_performance_troubleshooting_prompt
from .performance_troubleshooting_en import (
    register_performance_troubleshooting_prompt_en,
)

__all__ = [
    "register_performance_troubleshooting_prompt",
    "register_performance_troubleshooting_prompt_en",
]
