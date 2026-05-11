"""Snowflake SQL queries used by Report Inova."""

MAIN_TABLE = "CASHU.SILVER.INT_CASHU__INVOICE_RECEIVABLES_CURATED"


def get_reference_date_query() -> str:
    """Reference date uses max origination date from valid rows."""
    return f"""
        SELECT MAX(COALESCE(ANTICIPATED_AT, ISSUE_DATE)) AS reference_date
        FROM {MAIN_TABLE}
        WHERE AMT_TOTAL IS NOT NULL
          AND COALESCE(ANTICIPATED_AT, ISSUE_DATE) IS NOT NULL
          AND DUE_DATE IS NOT NULL
    """


def get_base_receivables_query() -> str:
    """Load the curated receivables base used across all sections."""
    return f"""
        WITH base AS (
            SELECT
                ID_INV_FIN_ITEM AS id,
                CD_NAME_SLUG AS seller,
                CD_NFE_KEY AS chave_nfe,
                NR_GOV_ID_BUYER AS sacado_cnpj,
                NM_BUYER AS sacado_nome,
                AMT_TOTAL AS valor_nota,
                AMT_TOTAL AS valor_parcela,
                AMT_NET AS valor_antecipado,
                AMT_PAID AS valor_pago,
                COALESCE(ANTICIPATED_AT, ISSUE_DATE) AS data_antecipacao,
                DUE_DATE AS data_vencimento,
                COALESCE(PYMT_DATE, STTL_DATE_RESALE) AS data_pagamento,
                COALESCE(AMT_INT, 0) + COALESCE(AMT_PNLT, 0) AS juros_multa,
                NM_CHGBK_OCURRENCE AS ocorrencia,
                IS_RESALE,
                IFF(IS_RESALE, AMT_TOTAL, NULL) AS valor_recompra,
                DATEDIFF('day', COALESCE(ANTICIPATED_AT, ISSUE_DATE), DUE_DATE) AS prazo,
                DATE_TRUNC('month', COALESCE(ANTICIPATED_AT, ISSUE_DATE)) AS year_month,
                DATE_TRUNC('month', DUE_DATE) AS year_month_expire
            FROM {MAIN_TABLE}
            WHERE AMT_TOTAL IS NOT NULL
              AND COALESCE(ANTICIPATED_AT, ISSUE_DATE) IS NOT NULL
              AND DUE_DATE IS NOT NULL
              AND DUE_DATE > COALESCE(ANTICIPATED_AT, ISSUE_DATE)
              AND DATEDIFF('day', COALESCE(ANTICIPATED_AT, ISSUE_DATE), DUE_DATE) > 0
              AND (AMT_NET IS NULL OR AMT_NET < AMT_TOTAL)
              AND (
                    NM_CHGBK_OCURRENCE IS NULL
                    OR LOWER(NM_CHGBK_OCURRENCE) IN ('recompra total', 'pago via ted', 'regresso')
                  )
        )
        SELECT * FROM base
    """
