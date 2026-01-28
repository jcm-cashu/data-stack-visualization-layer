# Components module - DO NOT MODIFY for new dashboards
# Contains reusable UI components

from .table import render_table_with_merged_headers
from .chiclet import chiclet_selector
from .charts import PLOTLY_COLORWAY, adjust_color, build_vintage_line, get_standard_layout

__all__ = [
    'render_table_with_merged_headers',
    'chiclet_selector',
    'PLOTLY_COLORWAY',
    'adjust_color',
    'build_vintage_line',
    'get_standard_layout',
]
