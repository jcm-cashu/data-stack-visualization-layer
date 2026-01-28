"""
Dashboard Configuration - Relatório Metas Sales CashU

This file contains all dashboard-specific metadata.
"""
from datetime import date, timedelta

# =============================================================================
# Dashboard Metadata
# =============================================================================

# Dashboard title (appears in browser tab and header)
DASHBOARD_TITLE = "Relatório Metas Sales CashU"

# Available pages in the dashboard
PAGES = ["Metas Sales"]

# Default page when the dashboard loads
DEFAULT_PAGE = "Metas Sales"

# Minimum selectable date in the date picker
DATE_MIN = date(2024, 1, 1)

# Default date range (end date will be capped to today in app.py)
DEFAULT_DATE_END = date.today() - timedelta(days=2)
DEFAULT_DATE_START = date.today() - timedelta(days=7)

# Month names for the month picker
MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Available years for selection (start from 2024)
MIN_YEAR = 2024
