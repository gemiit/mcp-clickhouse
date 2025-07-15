"""
Query Optimization Prompts Package

Provides registration for ClickHouse query optimization prompt handlers in both Chinese and English.
Enables modular support for analyzing and optimizing SQL queries.
"""

from .query_optimization import register_query_optimization_prompt
from .query_optimization_en import register_query_optimization_prompt_en

__all__ = [
    "register_query_optimization_prompt",
    "register_query_optimization_prompt_en",
]
