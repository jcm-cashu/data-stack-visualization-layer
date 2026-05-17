# Shared module - DO NOT MODIFY for new dashboards
# Contains visual identity, components, and data access layer

from .styles import COLORS, get_custom_css, get_table_styles
from .db import run_query, is_running_in_snowflake

__all__ = [
    'COLORS',
    'get_custom_css',
    'get_table_styles',
    'run_query',
    'is_running_in_snowflake',
]
