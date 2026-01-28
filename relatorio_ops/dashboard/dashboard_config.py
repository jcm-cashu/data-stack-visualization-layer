"""
Dashboard Configuration - Relatório de Conciliação CashU

This file contains all dashboard-specific metadata.
"""
from datetime import date, timedelta

# =============================================================================
# Dashboard Metadata
# =============================================================================

# Dashboard title (appears in browser tab and header)
DASHBOARD_TITLE = "Relatório de Conciliação Operações CashU"

# Available pages in the dashboard
PAGES = ["Conciliação Aquisições", "Conciliação Liquidações"]

# Default page when the dashboard loads
DEFAULT_PAGE = "Conciliação Aquisições"

# Minimum selectable date in the date picker
DATE_MIN = date(2026, 1, 9)

# Default date range (end date will be capped to today in app.py)
DEFAULT_DATE_END = date.today() - timedelta(days=2)
DEFAULT_DATE_START = date.today() - timedelta(days=7)
