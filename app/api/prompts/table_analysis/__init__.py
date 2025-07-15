"""
Table Analysis Prompts Package

Provides registration for ClickHouse table analysis prompt handlers in both Chinese and English.
Enables modular support for analyzing table structure and providing optimization suggestions.
"""

from .table_analysis import register_table_analysis_prompt
from .table_analysis_en import register_table_analysis_prompt_en

__all__ = [
    "register_table_analysis_prompt",
    "register_table_analysis_prompt_en",
]
