# Dashboard module - EDIT THESE files for new dashboards
# Contains dashboard-specific configuration, queries, and sections

from .dashboard_config import DASHBOARD_TITLE, PAGES, DEFAULT_PAGE, DATE_MIN
from . import queries
from .sections import render_sumario_geral, render_inadimplencia

__all__ = [
    'DASHBOARD_TITLE',
    'PAGES',
    'DEFAULT_PAGE',
    'DATE_MIN',
    'queries',
    'render_sumario_geral',
    'render_inadimplencia',
]
