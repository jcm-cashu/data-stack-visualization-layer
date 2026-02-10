"""
SQL Queries - Relatório de Conciliação CashU

Queries for reconciliation between CashU Invoice Financing and Fund Administrator systems.
Queries are written for Snowflake SQL syntax.
"""

# =============================================================================
# Table References
# =============================================================================

INVOICE_FINANCING_TABLE = "BRONZE.STG_CASHU_APP__INVOICE_FINANCING_ITEMS"
ORDER_INSTALLMENTS_TABLE = "BRONZE.STG_CASHU_APP__ORDER_INSTALLMENTS"
ORDERS_TABLE = "BRONZE.STG_CASHU_APP__ORDERS"
PARTIES_TABLE = "MASTER_DATA.DIM_PARTIES"
CORPORATES_TABLE = "BRONZE.RAW_CASHU_APP__CORPORATES"
FUND_ACQUISITIONS_TABLE = "FACT_DATA.FACT_FUND_ACQUISITIONS"
CASHU_LIQUIDATIONS_TABLE = "SILVER.INT_CASHU_APP__INVOICE_FINANCING_ITEMS_WRANGLED"
ADMIN_LIQUIDATIONS_TABLE = "FACT_DATA.FACT_FUND_LIQUIDATIONS"

# =============================================================================
# Query Functions
# =============================================================================

def get_cashu_query(date_start: str, date_end: str) -> str:
    """Query for CashU Invoice Financing items."""
    return f"""
        SELECT
            *
        FROM {CASHU_LIQUIDATIONS_TABLE}
        WHERE anticipated_at::DATE BETWEEN '{date_start}' AND '{date_end}'  and cd_name_slug <> 'br_aco'
    """


def get_admin_query(date_start: str, date_end: str) -> str:
    """Query for Fund Administrator acquisitions."""
    return f"""
        SELECT 
            *
        FROM {FUND_ACQUISITIONS_TABLE}
        WHERE REF_DATE::DATE BETWEEN '{date_start}' AND '{date_end}'
    """


def get_cashu_liquidations_query(date_start: str, date_end: str) -> str:
    """Query for CashU liquidations."""
    return f"""
        SELECT
            *
        FROM {CASHU_LIQUIDATIONS_TABLE}
        WHERE PYMT_DATE::DATE BETWEEN '{date_start}' AND '{date_end}' 
    """

def get_admin_liquidations_query(date_start: str, date_end: str) -> str:
    """Query for Fund Administrator liquidations."""
    return f"""
        SELECT
            *
        FROM {ADMIN_LIQUIDATIONS_TABLE}
        WHERE pymt_info_date::DATE BETWEEN '{date_start}' AND '{date_end}'
    """