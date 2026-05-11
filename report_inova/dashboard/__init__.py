# Dashboard module - EDIT THESE files for new dashboards
# Contains dashboard-specific configuration, queries, and sections

from .dashboard_config import DASHBOARD_TITLE, PAGES, DEFAULT_PAGE, DATE_MIN
from . import queries
from .sections import (
    render_carteira,
    render_inadimplencia,
    render_performance,
    render_safras,
    render_visao_geral,
)

__all__ = [
    'DASHBOARD_TITLE',
    'PAGES',
    'DEFAULT_PAGE',
    'DATE_MIN',
    'queries',
    'render_visao_geral',
    'render_carteira',
    'render_safras',
    'render_performance',
    'render_inadimplencia',
]
