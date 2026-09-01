"""Dashboard-specific configuration for Report Inova."""
from datetime import date

DASHBOARD_TITLE = "Report Inova"
PAGES = ["Visão Geral", "Carteira", "Safras", "Performance", "Inadimplência"]
DEFAULT_PAGE = "Visão Geral"
DATE_MIN = date(2024, 1, 1)

PERIODO_OPTIONS = ["Últimos 3 Meses", "Últimos 6 Meses", "Últimos 12 Meses"]
ROLLING_WINDOW_OPTIONS = ["30 dias", "45 dias", "60 dias", "90 dias"]
PD_HORIZON_OPTIONS = ["15 dias", "30 dias", "90 dias"]
COHORT_BASIS_OPTIONS = ["Por vencimento", "Por aquisição"]

AGING_LEVELS = ["0", "1-5", "6-30", "31-60", "61-90", "91-180", "180+"]
DPD_EDGES = [-10_000, 0, 5, 30, 60, 90, 180, 10_000]
PDD_BY_BUCKET = [0, 0, 0, 50, 100, 100, 100]

SELLER_DRILLDOWN_DEFAULT = "inova"
