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

def get_admin_liquidations_without_cashu_query(date_start: str, date_end: str) -> str:
    """Query for Fund Administrator liquidations without CashU."""
    return f"""
    SELECT
        coalesce(t2.nr_cnab_doc,t2.id_external) as nr_cnab_doc,
        t2.* exclude(nr_cnab_doc)
    FROM {CASHU_LIQUIDATIONS_TABLE} t1
    right JOIN {ADMIN_LIQUIDATIONS_TABLE} t2 ON t1.id_inv_fin_item = t2.id_inv_fin_item 
    WHERE t2.pymt_info_date::date BETWEEN '{date_start}' AND '{date_end}' AND t1.pymt_date IS NULL
    """

def get_cashu_liquidations_without_admin_query(date_start: str, date_end: str) -> str:
    """Query for CashU liquidations without Admin."""
    return f"""
        SELECT
        	t1.*
        FROM {CASHU_LIQUIDATIONS_TABLE} t1
        left JOIN {ADMIN_LIQUIDATIONS_TABLE} t2 ON t1.id_inv_fin_item  = t2.id_inv_fin_item 
        WHERE t1.pymt_date::date BETWEEN '{date_start}' AND '{date_end}' AND t1.pymt_date IS NOT NULL AND t2.id_inv_fin_item IS NULL AND t1.cd_name_slug  <> 'br_aco'
   """

def get_matching_liquidations_query(date_start: str, date_end: str) -> str:
    """Query for matching liquidations."""
    return f"""
        SELECT
        	t1.id_inv_fin_item,
        	t1.NR_GOV_ID_SELLER,
        	t1.NR_CNAB_CTRL NR_CNAB_CTRL_cashu,
        	t1.NR_CNAB_DOC NR_CNAB_DOC_cashu,
        	t1.PYMT_DATE,
        	t1.AMT_TOTAL,
        	t1.AMT_PAID,
        	t1.st_billet,
        	t2.NR_CNAB_CTRL NR_CNAB_CTRL_admin,
        	t2.NR_CNAB_DOC NR_CNAB_DOC_admin,
        	t2.PYMT_INFO_DATE,
        	t2.AMT_FUTURE,
        	t2.AMT_PYMT,
        	t2.TP_LIQUIDATION
        FROM {CASHU_LIQUIDATIONS_TABLE} t1
        INNER JOIN {ADMIN_LIQUIDATIONS_TABLE} t2 ON t1.id_inv_fin_item  = t2.id_inv_fin_item 
        WHERE t2.pymt_info_date::date BETWEEN '{date_start}' AND '{date_end}' AND t1.pymt_date::date IS NOT NULL AND (t1.cd_name_slug  <> 'br_aco' OR t1.cd_name_slug  IS NULL) 
    """