"""
SQL Queries - Relatório de Conciliação CashU

Queries for reconciliation between CashU Invoice Financing and Fund Administrator systems.
Queries are written for Snowflake SQL syntax.
"""

# =============================================================================
# Table References
# =============================================================================


GOALS_TABLE_BANKER = "BRONZE.STG_CASHU_SALES__METAS"
INVOICE_FINANCING_TABLE = "SILVER.INT_CASHU_APP__INVOICE_FINANCING_ITEMS_WRANGLED"


# =============================================================================
# Query Functions
# =============================================================================

def get_goals_slug_monthly_query(month: str, year: str) -> str:
    """Query for CashU Invoice Financing items by corporate slug."""
    return f"""
        WITH tmp AS (
            SELECT 
                year(ANTICIPATED_AT) yr,
                month(ANTICIPATED_AT) mth,
                *,
                (due_date - ANTICIPATED_AT::date) due_days,
                amt_total - amt_net amt_discount,
                1-AMT_NET/AMT_TOTAL rate_discount,
                power(power(1+rate_discount,365/due_days),1/12)-1 int_rate_am
            FROM {INVOICE_FINANCING_TABLE} t1
            WHERE IS_ANTCP 
              AND year(ANTICIPATED_AT) = {year} 
              AND month(ANTICIPATED_AT) = {month}
        ), tb AS (
            SELECT
                yr,
                mth,
                CD_NAME_SLUG,
                count(1) amt_inst,
                sum(t1.AMT_TOTAL) amt_total,
                sum(t1.amt_net) AMT_NET,
                sum(t1.amt_total) - sum(t1.amt_net) amt_discount,
                1-sum(t1.amt_net)/sum(t1.amt_total) rate_discount,
                sum(amt_total*due_days)/sum(amt_total) avg_due_days,
                sum(AMT_FEE_CONSULT*AMT_TOTAL) amt_fee_consult,
                sum(AMT_FEE_MDR*AMT_TOTAL) amt_fee_mdr
            FROM tmp t1
            GROUP BY ALL 
        )
        SELECT 
            t1.yr,
            t1.mth,
            cd_name_slug,
            amt_inst,
            amt_total,
            amt_net,
            amt_discount,
            rate_discount,
            avg_due_days,
            amt_fee_consult,
            amt_fee_mdr,
            COALESCE(t2.NM_BANKER,'Sem Banker') nm_banker,
            t2.amt_target AMT_GOAL
        FROM tb t1
        LEFT JOIN {GOALS_TABLE_BANKER} t2 
            ON t1.CD_NAME_SLUG = t2.CD_SLUG_CORP 
            AND t1.yr = t2.YR 
            AND t1.mth = t2.MTH 
    """


def get_goals_banker_monthly_query(month: str, year: str) -> str:
    """Query for goals aggregated by banker."""
    return f"""
        WITH tmp AS (
            SELECT 
                year(ANTICIPATED_AT) yr,
                month(ANTICIPATED_AT) mth,
                *,
                (due_date - ANTICIPATED_AT::date) due_days,
                amt_total - amt_net amt_discount,
                1-AMT_NET/AMT_TOTAL rate_discount,
                power(power(1+rate_discount,365/due_days),1/12)-1 int_rate_am
            FROM {INVOICE_FINANCING_TABLE} t1
            WHERE IS_ANTCP 
              AND year(ANTICIPATED_AT) = {year} 
              AND month(ANTICIPATED_AT) = {month}
        ), tb AS (
            SELECT
                yr,
                mth,
                CD_NAME_SLUG,
                count(1) amt_inst,
                sum(t1.AMT_TOTAL) amt_total,
                sum(t1.amt_net) AMT_NET,
                sum(t1.amt_total) - sum(t1.amt_net) amt_discount,
                1-sum(t1.amt_net)/sum(t1.amt_total) rate_discount,
                sum(amt_total*due_days)/sum(amt_total) avg_due_days,
                sum(AMT_FEE_CONSULT*AMT_TOTAL) amt_fee_consult,
                sum(AMT_FEE_MDR*AMT_TOTAL) amt_fee_mdr
            FROM tmp t1
            GROUP BY ALL 
        )
        SELECT 
            t1.yr,
            t1.mth,
            COALESCE(t2.NM_BANKER,'Sem Banker') nm_banker,
            count(DISTINCT CD_NAME_SLUG) amt_cedent,
            sum(amt_total) amt_total,
            sum(amt_fee_consult) amt_fee_consult_estimated,
            sum(amt_fee_mdr) amt_fee_mdr,
            sum(t2.amt_target) AMT_GOAL,
            sum(amt_total) - sum(t2.amt_target) gap_oport,
            sum(amt_total)/NULLIF(sum(t2.amt_target), 0) perc_goal,
            sum(amt_total)/NULLIF(count(DISTINCT CD_NAME_SLUG), 0) amt_total_per_cedent
        FROM tb t1
        LEFT JOIN {GOALS_TABLE_BANKER} t2 
            ON t1.CD_NAME_SLUG = t2.CD_SLUG_CORP 
            AND t1.yr = t2.YR 
            AND t1.mth = t2.MTH 
        GROUP BY ALL
    """