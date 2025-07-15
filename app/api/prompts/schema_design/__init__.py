"""
Schema Design Prompts Package

Provides registration for ClickHouse schema design prompt handlers in both Chinese and English.
Enables modular support for designing optimal schemas for specific use cases.
"""

from .schema_design import register_schema_design_prompt
from .schema_design_en import register_schema_design_prompt_en

__all__ = [
    "register_schema_design_prompt",
    "register_schema_design_prompt_en",
]
