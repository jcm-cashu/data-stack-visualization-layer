"""
Dashboard Configuration - EDIT THIS FILE for new dashboards

This file contains all dashboard-specific metadata.
Change these values when creating a new dashboard.
"""
from datetime import date

# =============================================================================
# Dashboard Metadata - CHANGE THESE FOR NEW DASHBOARDS
# =============================================================================

# Dashboard title (appears in browser tab and header)
DASHBOARD_TITLE = "CashU | Cacau Show"

# Available pages in the dashboard
PAGES = ["Sumário Geral", "Inadimplência"]

# Default page when the dashboard loads
DEFAULT_PAGE = "Sumário Geral"

# Minimum selectable date in the date picker
DATE_MIN = date(2024, 12, 1)

# =============================================================================
# Filter Options - CHANGE THESE IF NEEDED
# =============================================================================

# Habilitação filter options
HABILITACAO_OPTIONS = ["Todas", "Habilitada", "Não Habilitada"]

# Tier filter options
TIER_OPTIONS = ["Todos", "A", "B", "C", "D", "E", "Sem Tier"]

# Period filter options (for time series charts)
PERIODO_OPTIONS = [
    "Ultimos 2 Meses",
    "Ultimos 3 Meses",
    "Ultimos 6 Meses",
    "Ultimos 9 Meses",
    "Ultimos 12 Meses",
]

# Recency filter options (for credit distribution)
RECENCIA_OPTIONS = [
    "Todos",
    "Compras Últimos 30d",
    "Compras Últimos 60d",
    "Compras Últimos 90d",
]

# =============================================================================
# Metric Labels - CHANGE THESE IF YOUR DATA USES DIFFERENT NAMES
# =============================================================================

METRIC_LABELS = {
    "financeiro": "R$",
    "financeiro_cashu": "R$ CashU",
    "numero_compras": "# Compras",
    "numero_clientes": "# Clientes",
    "clientes_com_credito": "# Clientes com Crédito",
    "ticket_medio": "Ticket Médio",
}

# Bucket labels for delinquency charts
BUCKET_LABELS = {
    "exposicao": "Exposição",
    "total_delinquente": "Total Delinquente",
    "atraso": "Atraso (>2d)",
    "over_15p": "15d+",
    "over_30p": "30d+",
    "over_60p": "60d+",
    "over_90p": "90d+",
    "over_180": "180d+",
}
