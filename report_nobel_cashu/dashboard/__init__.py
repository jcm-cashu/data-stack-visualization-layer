# Dashboard module - EDIT THESE files for new dashboards
# Contains dashboard-specific configuration, queries, and sections

from .dashboard_config import DASHBOARD_TITLE, PAGES, DEFAULT_PAGE
from . import queries
from .sections import render_carteira

__all__ = [
    'DASHBOARD_TITLE',
    'PAGES',
    'DEFAULT_PAGE',
    'queries',
    'render_carteira',
]
