"""
SQL queries for the Cacau Show dashboard.
All queries are kept here to separate data layer from visualization.
Queries are written for Snowflake SQL syntax.
"""

# Main table reference
MAIN_TABLE = "FACT_DATA.FACT_STLIT_CACAU_SHOW_DAILY"
RECEIVABLES_TABLE = "FACT_DATA.FACT_cashu_receivables"


def get_totais_query(month: int, year: int) -> str:
    """Query for general totals metrics."""
    return f"""
        SELECT
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            SUM(IFF(TP_TTL_PYMT = 'BOL', AMT_SELL, 0)) AS financeiro_cashu,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            COUNT(DISTINCT IFF(HAS_CREDIT_LIMIT AND IS_SELL_DAY, ID_CUST, NULL)) AS clientes_com_credito,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
    """


def get_habilitacao_query(month: int, year: int) -> str:
    """Query for metrics grouped by store enablement status."""
    return f"""
        SELECT
            IFF(IS_STORE_OPERABLE, 'Habilitada', 'Não Habilitada') AS status_habilitada,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            SUM(IFF(TP_TTL_PYMT = 'BOL', AMT_SELL, 0)) AS financeiro_cashu,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            COUNT(DISTINCT IFF(HAS_CREDIT_LIMIT AND IS_SELL_DAY, ID_CUST, NULL)) AS clientes_com_credito,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        GROUP BY 1
    """


def get_tier_query(month: int, year: int) -> str:
    """Query for metrics grouped by store tier."""
    return f"""
        SELECT
            COALESCE(CD_STORE_TIER, 'Sem Tier') AS tier_loja,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            SUM(IFF(TP_TTL_PYMT = 'BOL', AMT_SELL, 0)) AS financeiro_cashu,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            COUNT(DISTINCT IFF(HAS_CREDIT_LIMIT AND IS_SELL_DAY, ID_CUST, NULL)) AS clientes_com_credito,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        GROUP BY 1
    """


def get_breakdown_lojas_query(month: int, year: int, habilitacao_filter: str, tier_filter: str) -> str:
    """Query for store breakdown with filters."""
    # Convert DuckDB filter syntax to Snowflake
    sf_hab_filter = habilitacao_filter.replace("loja_habilitada_flag", "IS_STORE_OPERABLE")
    sf_tier_filter = tier_filter.replace("tier_loja", "CD_STORE_TIER")
    
    return f"""
        (
        SELECT
            COALESCE(TP_STORE, 'Sem Classificação') AS tipo_loja,
            TP_TTL_PYMT AS forma_pagamento,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        {sf_hab_filter}
        {sf_tier_filter}
        GROUP BY 1, 2
        )
        UNION ALL
        (
        SELECT
            COALESCE(TP_STORE, 'Sem Classificação') AS tipo_loja,
            'Total' AS forma_pagamento,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        {sf_hab_filter}
        {sf_tier_filter}
        GROUP BY 1
        )
    """


def get_perc_credito_query(month: int, year: int, habilitacao_filter: str, tier_filter: str) -> str:
    """Query for credit percentage distribution per store."""
    # Convert DuckDB filter syntax to Snowflake
    sf_hab_filter = habilitacao_filter.replace("loja_habilitada_flag", "IS_STORE_OPERABLE")
    sf_tier_filter = tier_filter.replace("tier_loja", "CD_STORE_TIER")
    
    return f"""
        SELECT
            CAST(MTH AS VARCHAR) || '/' || CAST(YR AS VARCHAR) AS mes_ano,
            NR_GOV_ID_ISSUER AS emitente_documento,
            COALESCE(TP_STORE, 'Sem Classificação') AS tipo_loja,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            COUNT(DISTINCT IFF(HAS_CREDIT_LIMIT AND IS_SELL_DAY, ID_CUST, NULL)) AS clientes_com_credito,
            clientes_com_credito / NULLIF(numero_clientes, 0) AS perc_com_credito
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        {sf_hab_filter}
        {sf_tier_filter}
        GROUP BY 1, 2, 3
        HAVING numero_clientes > 0
    """


def get_breakdown_revendedores_query(month: int, year: int) -> str:
    """Query for reseller breakdown."""
    return f"""
        (
        SELECT
            IFF(IS_STORE_OPERABLE, 'Habilitada', 'Não Habilitada') AS status_habilitada,
            TP_TTL_PYMT AS forma_pagamento,
            IFF(HAS_CREDIT_LIMIT, 'Possui Crédito CashU', 'Não Possui Crédito CashU') AS tipo_revendedor,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        GROUP BY 1, 2, 3
        )
        UNION ALL
        (
        SELECT
            IFF(IS_STORE_OPERABLE, 'Habilitada', 'Não Habilitada') AS status_habilitada,
            'Total' AS forma_pagamento,
            IFF(HAS_CREDIT_LIMIT, 'Possui Crédito CashU', 'Não Possui Crédito CashU') AS tipo_revendedor,
            SUM(IFF(IS_SELL_DAY, 1, 0)) AS numero_compras,
            SUM(AMT_SELL) AS financeiro,
            COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)) AS numero_clientes,
            AVG(IFF(IS_SELL_DAY, AMT_SELL, NULL)) AS ticket_medio
        FROM {MAIN_TABLE}
        WHERE MTH = {month} AND YR = {year} AND TP_TTL_PYMT IS NOT NULL
        GROUP BY 1, 3
        )
    """


def get_timeseries_receita_query() -> str:
    """Query for revenue time series (parameterized)."""
    return f"""
        SELECT
            DATE_FROM_PARTS(YR, MTH, 1) AS ref_date,
            SUM(AMT_SELL) AS receita
        FROM {MAIN_TABLE}
        WHERE DATE_FROM_PARTS(YR, MTH, 1) BETWEEN %s AND %s
          AND TP_TTL_PYMT IS NOT NULL
          AND HAS_CREDIT_LIMIT = %s
        GROUP BY 1
        ORDER BY 1
    """


def get_faturamento_per_capta_query(ref_date: str, months: int) -> str:
    """Query for per capita revenue evolution."""
    return f"""
        SELECT
            DATE_FROM_PARTS(YR, MTH, 1) AS date,
            TP_TTL_PYMT AS forma_pagamento,
            IFF(HAS_CREDIT_LIMIT, 'Possui Crédito CashU', 'Não Possui Crédito CashU') AS tipo_revendedor,
            SUM(AMT_SELL) / NULLIF(COUNT(DISTINCT IFF(IS_SELL_DAY, ID_CUST, NULL)), 0) AS financeiro_per_capta
        FROM {MAIN_TABLE}
        WHERE TP_TTL_PYMT IS NOT NULL
          AND DATE_FROM_PARTS(YR, MTH, 1) BETWEEN DATEADD('MONTH', -{months}, '{ref_date}'::DATE) AND '{ref_date}'::DATE
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """


def get_distribuicao_credito_query(ref_date: str, filtro_recencia: str) -> str:
    """Query for credit distribution."""
    # Convert filter to use the aggregate expression directly
    # filtro_recencia comes as "and filtro_recencia <= 30" etc.
    # We need to filter on the MIN(QTY_DAYS_LAST_PURCHASE) result
    sf_filtro = filtro_recencia.replace("filtro_recencia", "min_days_last_purchase")
    
    return f"""
       WITH base_credito AS (
           SELECT 
               DATE AS date,
               ID_CUST AS customer_id,
               SUM(IFF(TP_TTL_PYMT = 'BOL' AND IS_PURCHASE_ACTIVE AND HAS_CREDIT_LIMIT, AMT_TTL_GROSS, 0)) AS credito_utilizado,
               MAX(AMT_CREDIT_LIMIT) AS credito_disponivel,
               COALESCE(MIN(QTY_DAYS_LAST_PURCHASE), 0) AS min_days_last_purchase
           FROM {MAIN_TABLE}
           WHERE DATE = '{ref_date}'::DATE
           GROUP BY DATE, ID_CUST
           HAVING MAX(AMT_CREDIT_LIMIT) IS NOT NULL
       )
       SELECT
           date,
           customer_id,
           credito_utilizado,
           credito_disponivel,
           credito_utilizado / NULLIF(credito_disponivel, 0) AS percentual_utilizado,
           min_days_last_purchase AS filtro_recencia
       FROM base_credito
       WHERE 1=1
       {sf_filtro}
    """


def get_inadimplencia_evolucao_query(start_date: str, end_date: str) -> str:
    """Query for delinquency evolution."""
    return f"""
        SELECT 
            DATE,
            SUM(IFF(IS_PURCHASE_ACTIVE AND NOT IS_PYMT_DELAYED AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS exposicao,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_PYMT_DELAYED AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS total_delinquente,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_PYMT_DELAYED AND NOT IS_OVER_30 AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS atraso,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_OVER_30 AND NOT IS_OVER_60 AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS over_30,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_OVER_60 AND NOT IS_OVER_90 AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS over_60,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_OVER_90 AND NOT IS_OVER_180 AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS over_90,
            SUM(IFF(IS_PURCHASE_ACTIVE AND IS_OVER_180 AND TP_TTL_PYMT = 'BOL', AMT_TTL_GROSS, 0)) AS over_180
        FROM {MAIN_TABLE}
        WHERE DATE BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY 1
        ORDER BY DATE
    """


VINTAGE_CLIENTES_QUERY = f"""
WITH base_raw AS (
    SELECT
        DATE,
        DATEADD('DAY', -QTY_DAYS_RELATIONSHIP_CASHU, DATE)::DATE AS data_inicio_relacionamento,
        ID_CUST,
        QTY_DAYS_RELATIONSHIP_CASHU
    FROM {MAIN_TABLE}
    WHERE QTY_DAYS_RELATIONSHIP_CASHU IS NOT NULL AND TP_TTL_PYMT = 'BOL'
), base_tmp AS (
    SELECT
        DATE,
        data_inicio_relacionamento,
        TO_CHAR(data_inicio_relacionamento, 'YYYY-MM') AS vintage,
        DATEDIFF('MONTH', data_inicio_relacionamento, DATE) AS mob,
        ID_CUST,
        QTY_DAYS_RELATIONSHIP_CASHU
    FROM base_raw
), valid_vintage AS (
    SELECT 
        vintage,
        MIN(mob) AS min_mob
    FROM base_tmp
    GROUP BY vintage
    HAVING MIN(mob) = 0
), vintage AS (
    SELECT 
        t1.vintage,
        t1.mob,
        TO_DATE(t1.vintage || '-01', 'YYYY-MM-DD') AS min_date,
        MAX(t1.DATE) AS max_date
    FROM base_tmp t1 
    INNER JOIN valid_vintage t2 ON t1.vintage = t2.vintage
    GROUP BY t1.vintage, t1.mob
), tb AS (
    SELECT 
        t1.vintage,
        t1.mob,
        t1.min_date,
        t1.max_date,
        t2.AMT_INSTALLMENT AS valor_parcela,
        COALESCE(t2.AMT_PAID, 0) AS valor_pago,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 2, TRUE, FALSE) AS atraso_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 15, TRUE, FALSE) AS over_15_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 30, TRUE, FALSE) AS over_30_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 60, TRUE, FALSE) AS over_60_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 90, TRUE, FALSE) AS over_90_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 180, TRUE, FALSE) AS over_180_flag,
        IFF(t2.TTL_PYMT_DATE IS NOT NULL, TRUE, FALSE) AS pago
    FROM vintage t1 
    INNER JOIN {RECEIVABLES_TABLE} t2 
        ON t2.TTL_ISSUE_DATE >= t1.min_date 
        AND t2.TTL_DUE_DATE_CURR <= t1.max_date
    WHERE DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, t1.max_date) > 2 
        AND t2.CD_NAME_SLUG = 'cacau_show'
)
SELECT 
    vintage,
    mob,
    SUM(valor_parcela) AS total_operado,
    SUM(valor_pago) AS total_recebido,
    SUM(IFF(atraso_flag AND NOT pago, valor_parcela, 0)) AS atraso,
    SUM(IFF(over_15_flag AND NOT pago, valor_parcela, 0)) AS over_15p,
    SUM(IFF(over_30_flag AND NOT pago, valor_parcela, 0)) AS over_30p,
    SUM(IFF(over_60_flag AND NOT pago, valor_parcela, 0)) AS over_60p,
    SUM(IFF(over_90_flag AND NOT pago, valor_parcela, 0)) AS over_90p,
    SUM(IFF(over_180_flag AND NOT pago, valor_parcela, 0)) AS over_180,
    1 - SUM(valor_pago) / NULLIF(SUM(valor_parcela), 0) AS delinquencia,
    SUM(IFF(atraso_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_atraso,
    SUM(IFF(over_15_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_over_15,
    SUM(IFF(over_30_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_over_30,
    SUM(IFF(over_60_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_over_60,
    SUM(IFF(over_90_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_over_90,
    SUM(IFF(over_180_flag AND NOT pago, valor_parcela, 0)) / NULLIF(SUM(valor_parcela), 0) AS delinquencia_over_180
FROM tb
GROUP BY vintage, mob
"""


VINTAGE_ORIGINACAO_QUERY = f"""
WITH base_tmp AS (
    SELECT
        DATE,
        TO_CHAR(TTL_ISSUE_DATE, 'YYYY-MM') AS vintage,
        DATEDIFF('MONTH', TTL_ISSUE_DATE, DATE) AS mob,
        ID_CUST,
        TTL_ISSUE_DATE
    FROM {MAIN_TABLE}
    WHERE QTY_DAYS_RELATIONSHIP_CASHU IS NOT NULL AND TP_TTL_PYMT = 'BOL'
), valid_vintage AS (
    SELECT 
        vintage,
        MIN(mob) AS min_mob
    FROM base_tmp
    GROUP BY vintage
    HAVING MIN(mob) = 0
), vintage_base AS (
    SELECT 
        t1.vintage,
        t1.mob,
        TO_DATE(t1.vintage || '-01', 'YYYY-MM-DD') AS min_date
    FROM base_tmp t1
    INNER JOIN valid_vintage t2 ON t1.vintage = t2.vintage
    GROUP BY t1.vintage, t1.mob
), vintage AS (
    SELECT
        vintage,
        mob,
        min_date,
        LEAST(LAST_DAY(DATEADD('MONTH', mob, min_date)), CURRENT_DATE()) AS max_date
    FROM vintage_base
), tb AS (
    SELECT 
        t1.vintage,
        t1.mob,
        t1.min_date,
        t1.max_date,
        t2.AMT_INSTALLMENT AS valor_parcela,
        COALESCE(t2.AMT_PAID, 0) AS valor_pago,
        IFF(t2.TTL_DUE_DATE_CURR <= t1.max_date, TRUE, FALSE) AS classifiable_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 2, TRUE, FALSE) AS atraso_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 15, TRUE, FALSE) AS over_15_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 30, TRUE, FALSE) AS over_30_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 60, TRUE, FALSE) AS over_60_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 90, TRUE, FALSE) AS over_90_flag,
        IFF(DATEDIFF('DAY', t2.TTL_DUE_DATE_CURR, COALESCE(t2.TTL_PYMT_DATE, t1.max_date)) > 180, TRUE, FALSE) AS over_180_flag,
        IFF(t2.TTL_PYMT_DATE IS NOT NULL, TRUE, FALSE) AS pago
    FROM vintage t1 
    INNER JOIN {RECEIVABLES_TABLE} t2 
        ON TO_CHAR(t2.TTL_ISSUE_DATE, 'YYYY-MM') = t1.vintage
    WHERE t2.CD_NAME_SLUG = 'cacau_show'
)
SELECT 
    vintage,
    mob,
    SUM(IFF(classifiable_flag, valor_parcela, 0)) AS total_operado,
    SUM(IFF(classifiable_flag, valor_pago, 0)) AS total_recebido,
    SUM(IFF(over_15_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) AS over_15p,
    SUM(IFF(over_30_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) AS over_30p,
    SUM(IFF(over_60_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) AS over_60p,
    SUM(IFF(over_90_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) AS over_90p,
    SUM(IFF(over_180_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) AS over_180,
    1 - SUM(IFF(classifiable_flag, valor_pago, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia,
    SUM(IFF(over_15_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia_over_15,
    SUM(IFF(over_30_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia_over_30,
    SUM(IFF(over_60_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia_over_60,
    SUM(IFF(over_90_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia_over_90,
    SUM(IFF(over_180_flag AND NOT pago AND classifiable_flag, valor_parcela, 0)) / NULLIF(SUM(IFF(classifiable_flag, valor_parcela, 0)), 0) AS delinquencia_over_180
FROM tb
GROUP BY vintage, mob
"""
