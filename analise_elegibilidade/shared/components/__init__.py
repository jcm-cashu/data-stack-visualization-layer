# Components module - DO NOT MODIFY for new dashboards
# Contains reusable UI components

from .table import render_table_with_merged_headers
from .grid import render_data_grid, GridColumnConfig, GridTheme, get_design_system_grid_theme
from .chiclet import chiclet_selector
from .charts import PLOTLY_COLORWAY, adjust_color, build_vintage_line, get_standard_layout, render_plotly_chart
from .html_export import generate_full_export_html, start_collection, stop_collection

# Re-export style constants so sections can import from a single place
from ..styles import PLOTLY_CONFIG

__all__ = [
    'render_table_with_merged_headers',
    'render_data_grid',
    'GridColumnConfig',
    'GridTheme',
    'get_design_system_grid_theme',
    'chiclet_selector',
    'PLOTLY_COLORWAY',
    'PLOTLY_CONFIG',
    'adjust_color',
    'build_vintage_line',
    'get_standard_layout',
    'render_plotly_chart',
    'generate_full_export_html',
    'start_collection',
    'stop_collection',
]
