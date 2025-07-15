"""
Migration Planning Prompts Package

Provides registration for ClickHouse migration planning prompt handlers in both Chinese and English.
Enables modular support for data migration planning from other systems to ClickHouse.
"""

from .migration_planning import register_migration_planning_prompt
from .migration_planning_en import register_migration_planning_prompt_en

__all__ = [
    "register_migration_planning_prompt",
    "register_migration_planning_prompt_en",
]
